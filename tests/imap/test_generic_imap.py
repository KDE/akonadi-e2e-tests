# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from logging import getLogger

import pytest

from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.imap.client import ImapClient
from src.imap.email_utils import create_message
from src.imap.test_utils import check_collection_in_sync, message_added, message_deleted
from src.test import wait_until

log = getLogger(__name__)


@pytest.mark.asyncio
async def test_initial_sync(imap_resource: ImapResource, imap_client: ImapClient) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_only_change(imap_resource: ImapResource, imap_client: ImapClient) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 1, "$TestFlag")
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_offline_flag_only_change(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_resource.set_online(False)

    collection = imap_resource.resolve_collection("Test")
    items = imap_resource.list_items(collection.id())
    item = items[0]
    imap_uid = int(item.remoteId())

    await imap_client.add_flag("Test", imap_uid, "$TestFlag")
    imap_resource.add_flag(item.id(), "$TestFlag2")

    await imap_resource.set_online(True)
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_removed_message(imap_resource: ImapResource, imap_client: ImapClient) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.remove_message("Test", 1)
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_added_message(imap_resource: ImapResource, imap_client: ImapClient) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_new_message("Test")
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 2, "$TestFlag")
    await imap_client.remove_message("Test", 1)
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 2, "$TestFlag")
    await imap_client.add_new_message("Test")
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_added_and_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_new_message("Test")
    await imap_client.remove_message("Test", 1)

    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_sync_flag_change_and_added_and_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 2, "$TestFlag")
    await imap_client.add_new_message("Test")
    await imap_client.remove_message("Test", 1)

    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_new_mailbox_on_server_is_synced(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await imap_client.create_mailbox("Test3")
    await imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert any(lambda c: c.name() == "Test3" for c in collections)


@pytest.mark.asyncio
async def test_mailbox_deleted_on_server_is_synced(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.delete_mailbox("Test")
    await imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert "Test" not in list(map(lambda c: c.name(), collections))


@pytest.mark.asyncio
async def test_mailbox_deleted_on_server_is_unsynced(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_resource.set_online(False)

    await imap_client.delete_mailbox("Test")
    imap_resource.delete_collection("Test2")

    # check mailboxes in disconnected state
    collections_akonadi = imap_resource.list_collections()
    assert "Test" in list(map(lambda c: c.name(), collections_akonadi))
    assert await imap_client.mailbox_exists("Test2")

    # reconnect
    await imap_resource.set_online(True)
    await imap_resource.synchronize()

    # check that both imap and akonadi server are properly synchronised
    collections_akonadi = imap_resource.list_collections()
    assert "Test" not in list(map(lambda c: c.name(), collections_akonadi))
    assert not (await imap_client.mailbox_exists("Test2"))


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="IMAP/Akonadi bug? The old and new items get merged based on RID despite the UIDVALIDITY change."
)
async def test_uidvalidity_change_detected(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.delete_mailbox("Test")
    await asyncio.sleep(1)
    await imap_client.create_mailbox("Test")
    await imap_client.add_new_message("Test")

    await imap_resource.synchronize()

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_append_message(
    imap_resource: ImapResource,
    imap_client: ImapClient,
    akonadi_client: AkonadiClient,
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)
    collection = imap_resource.resolve_collection("Test")

    # Append the item to Akonadi
    akonadi_client.add_item(
        collection.id(),
        create_message(subject="test_append_message").as_bytes(),
        "message/rfc822",
    )

    # List items from Akonadi, there should be 3 now.
    items = akonadi_client.list_items(collection.id())
    assert len(items) == 3

    # Wait for it to be uploaded to the IMAP as well
    # It may take a little bit for the change to propagate to the IMAP server, so try a few times
    await wait_until(lambda: message_added(imap_client, "Test", 3))

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_delete_message(
    imap_resource: ImapResource,
    imap_client: ImapClient,
    akonadi_client: AkonadiClient,
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    collection = imap_resource.resolve_collection("Test")
    items = akonadi_client.list_items(collection.id())
    assert len(items) == 2
    item = items[0]

    akonadi_client.delete_item(item.id())

    await wait_until(lambda: message_deleted(imap_client, item, "Test"), timeout=10.0)

    await check_collection_in_sync("Test", imap_resource, imap_client)


### Tests I added


@pytest.mark.asyncio
async def test_move_message_on_server_is_synced(
    imap_resource: ImapResource,
    imap_client: ImapClient,
    akonadi_client: AkonadiClient,
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)
    await check_collection_in_sync("Test2", imap_resource, imap_client)

    source = imap_resource.resolve_collection("Test")
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == 2

    destination = imap_resource.resolve_collection("Test2")
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == 2

    item = items_source[0]
    akonadi_client.move_item(item.id(), destination.id())

    await wait_until(lambda: message_deleted(imap_client, item, "Test"))
    await wait_until(lambda: message_added(imap_client, "Test2", 3))

    await check_collection_in_sync("Test", imap_resource, imap_client)
    await check_collection_in_sync("Test2", imap_resource, imap_client)


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Akonadi bug ? An append command is sent to the server, and cyrus rejects it because of wrong flags",
)
async def test_copy_message_on_server_is_synced(
    imap_resource: ImapResource,
    imap_client: ImapClient,
    akonadi_client: AkonadiClient,
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)
    await check_collection_in_sync("Test2", imap_resource, imap_client)

    source = imap_resource.resolve_collection("Test")
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == 2

    destination = imap_resource.resolve_collection("Test2")
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == 2

    item = items_source[0]
    akonadi_client.copy_item(item.id(), destination.id())

    await wait_until(lambda: message_added(imap_client, "Test", 2))
    await wait_until(lambda: message_added(imap_client, "Test2", 3))

    await check_collection_in_sync("Test", imap_resource, imap_client)
    await check_collection_in_sync("Test2", imap_resource, imap_client)


""""
@pytest.mark.asyncio
async def test_sync_10000_messages(imap_resource: ImapResource, imap_client: ImapClient) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    start = time.time()

    for _ in range(10000):
        await imap_client.add_new_message("Test")

    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)

    total = time.time() - start

    log.debug(f"Benchmark test : synced 10 000 messages in {total} seconds")
"""

# Ideas/plan
# * HIGHESTMODSEQ support disabled
# * Changing flags of a message when offline
# * Moving a message to another mailbox when offline
# * Copying a message to another mailbox when offline
# * Changing mailbox name when offline and online
# * Creating a mailbox when offline
# * Interruping sync in the middle
# * IDLE support (email should appear in Akonadi without sync - will need akonadiclient
#                 support to list items without triggering sync)
# * Namespace support
# * ACL handling
# * Benchmark/slow tests
#   * sync 10'000 messages
#   * mark 10'000 messages as read/unread
#   * move 10'000 messages to another mailbox
