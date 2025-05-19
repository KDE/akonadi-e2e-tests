# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

import asyncio
import pytest
from src.akonadi.imap_resource import ImapResource
from src.akonadi.client import AkonadiClient
from src.imap.client import ImapClient
from src.imap.email_utils import create_message
from src.imap.test_utils import check_collection_in_sync

from src.test import wait_until

log = getLogger(__name__)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_initial_sync(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param(
            {"suppress_capabilities": ["CONDSTORE"]},
            id="without CONDSTORE",
            marks=pytest.mark.xfail(
                reason="IMAP resource doesn't do flag sync when CONDSTORE is not available and no messages were added/removed."
            ),
        ),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_sync_flag_only_change(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 1, "$TestFlag")
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_sync_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.remove_message("Test", 1)
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_sync_added_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_new_message("Test")
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 2, "$TestFlag")
    await imap_client.remove_message("Test", 1)
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_flag("Test", 2, "$TestFlag")
    await imap_client.add_new_message("Test")
    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
@pytest.mark.asyncio
async def test_sync_added_and_removed_message(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.add_new_message("Test")
    await imap_client.remove_message("Test", 1)

    await imap_resource.sync_collection("Test")

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.parametrize(
    "cyrus_server",
    [
        pytest.param({}, id="with CONDSTORE"),
        pytest.param({"suppress_capabilities": ["CONDSTORE"]}, id="without CONDSTORE"),
    ],
    indirect=["cyrus_server"],
)
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
    await imap_client.create_mailbox("Test2")
    await imap_resource.synchronize()

    collections = await imap_resource.list_collections()
    assert any(lambda c: c.name == "Test2" for c in collections)


@pytest.mark.asyncio
async def test_mailbox_deleted_on_server_is_synced(
    imap_resource: ImapResource, imap_client: ImapClient
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    await imap_client.delete_mailbox("Test")
    await imap_resource.synchronize()

    collections = await imap_resource.list_collections()
    assert "Test" not in list(map(lambda c: c.name, collections))


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
    collection = await imap_resource.resolve_collection("Test")

    # Append the item to Akonadi
    await akonadi_client.add_item(
        collection.id,
        create_message(subject="test_append_message").as_bytes(),
        "message/rfc822",
    )

    # List items from Akonadi, there should be 3 now.
    items = await akonadi_client.list_items(collection.id)
    assert len(items) == 3

    # Wait for it to be uploaded to the IMAP as well
    # It may take a little bit for the change to propagate to the IMAP server, so try a few times
    async def message_added() -> bool:
        return await imap_client.fetch_message("Test", seq=3) is not None

    await wait_until(message_added)

    await check_collection_in_sync("Test", imap_resource, imap_client)


@pytest.mark.asyncio
async def test_delete_message(
    imap_resource: ImapResource,
    imap_client: ImapClient,
    akonadi_client: AkonadiClient,
) -> None:
    await check_collection_in_sync("Test", imap_resource, imap_client)

    collection = await imap_resource.resolve_collection("Test")
    items = await akonadi_client.list_items(collection.id)
    assert len(items) == 2
    item = items[0]

    await akonadi_client.delete_item(item.id)

    async def message_deleted() -> bool:
        assert item.remote_id is not None
        await imap_client.expunge("Test")
        return await imap_client.fetch_message("Test", uid=int(item.remote_id)) is None

    await wait_until(message_deleted)

    await check_collection_in_sync("Test", imap_resource, imap_client)


# Ideas/plan
# * HIGHESTMODSEQ support disabled
# * Changing flags of a message when offline and online
# * Moving a message to another mailbox when offline and online
# * Copying a message to another mailbox when offline and online
# * Changing mailbox name when offline and online
# * Deleting a mailbox when offline and online
# * Creating a mailbox when offline and online
# * Interruping sync in the middle
# * IDLE support (email should appear in Akonadi without sync - will need akonadiclient
#                 support to list items without triggering sync)
# * Namespace support
# * ACL handling
# * Benchmark/slow tests
#   * sync 10'000 messages
#   * mark 10'000 messages as read/unread
#   * move 10'000 messages to another mailbox
