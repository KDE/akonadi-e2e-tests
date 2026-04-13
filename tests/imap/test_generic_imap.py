# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import time
from logging import getLogger

import pytest
from imap_tools import BaseMailBox, MailboxFolderDeleteError

from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.imap.email_utils import create_message
from src.imap.test_utils import check_collection_in_sync, message_added, message_deleted
from test import wait_until

log = getLogger(__name__)


def test_initial_sync(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.folder.set("Test")
    imap_client.flag(["1"], ["$TestFlag"], True)
    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_offline_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_resource.set_online(False)

    collection = imap_resource.resolve_collection("Test")
    items = imap_resource.list_items(collection.id())
    item = items[0]
    imap_uid = item.remoteId()

    imap_client.folder.set("Test")
    imap_client.flag([imap_uid], "$TestFlag", True)
    imap_resource.add_flag(item.id(), "$TestFlag2")

    imap_resource.set_online(True)
    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_removed_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    imap_client.folder.set("Test")
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_added_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    imap_client.folder.set("Test")
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.append(create_message().as_bytes(), "Test")
    imap_resource.sync_collection(
        "Test"
    )  # Doing a double sync as check collection in sync, do a sync too

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    check_collection_in_sync("Test", imap_resource, imap_client)
    imap_client.append(create_message().as_bytes(), "Test")

    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_sync_flag_change_and_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_new_mailbox_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.create("Test3")
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert any(lambda c: c.name() == "Test3" for c in collections)


def test_mailbox_deleted_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    for _ in range(5):
        try:
            imap_client.folder.delete("Test")
        except MailboxFolderDeleteError:
            time.sleep(0.2)
    assert not imap_client.folder.exists("Test")
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert "Test" not in list(map(lambda c: c.name(), collections))


def test_mailbox_deleted_on_server_is_unsynced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_resource.set_online(False)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete("Test")
    imap_resource.delete_collection("Test2")

    # check mailboxes in disconnected state
    collections_akonadi = imap_resource.list_collections()
    assert "Test" in list(map(lambda c: c.name(), collections_akonadi))
    assert imap_client.folder.exists("Test2")

    # reconnect
    imap_resource.set_online(True)
    imap_resource.synchronize()

    # check that both imap and akonadi server are properly synchronised
    collections_akonadi = imap_resource.list_collections()
    assert "Test" not in list(map(lambda c: c.name(), collections_akonadi))
    assert not imap_client.folder.exists("Test2")


@pytest.mark.xfail(
    reason="IMAP/Akonadi bug? The old and new items get merged based on RID despite the UIDVALIDITY change."
)
def test_uidvalidity_change_detected(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete("Test")
    imap_client.folder.create("Test")
    imap_client.append(create_message().as_bytes(), "Test")

    imap_resource.synchronize()

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)
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
    wait_until(lambda: message_added(imap_client, "Test", "3"))

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_delete_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    collection = imap_resource.resolve_collection("Test")
    items = akonadi_client.list_items(collection.id())
    assert len(items) == 2
    item = items[0]

    akonadi_client.delete_item(item.id())

    wait_until(lambda: message_deleted(imap_client, item, "Test"), timeout=10.0)

    check_collection_in_sync("Test", imap_resource, imap_client)


def test_move_message_on_server_is_synced(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)
    check_collection_in_sync("Test2", imap_resource, imap_client)

    source = imap_resource.resolve_collection("Test")
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == 2

    destination = imap_resource.resolve_collection("Test2")
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == 2

    item = items_source[0]
    akonadi_client.move_item(item.id(), destination.id())

    wait_until(lambda: message_deleted(imap_client, item, "Test"))
    wait_until(lambda: message_added(imap_client, "Test2", "3"))

    check_collection_in_sync("Test", imap_resource, imap_client)
    check_collection_in_sync("Test2", imap_resource, imap_client)


@pytest.mark.xfail(
    reason="Akonadi bug ? An append command is sent to the server, and cyrus rejects it because of wrong flags",
)
def test_copy_message_on_server_is_synced(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)
    check_collection_in_sync("Test2", imap_resource, imap_client)

    source = imap_resource.resolve_collection("Test")
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == 2

    destination = imap_resource.resolve_collection("Test2")
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == 2

    item = items_source[0]
    akonadi_client.copy_item(item.id(), destination.id())

    wait_until(lambda: message_added(imap_client, "Test", "2"))
    wait_until(lambda: message_added(imap_client, "Test2", "3"))

    check_collection_in_sync("Test", imap_resource, imap_client)
    check_collection_in_sync("Test2", imap_resource, imap_client)

def test_offline_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    check_collection_in_sync("TestEmpty", imap_resource, imap_client)
    collection = imap_resource.resolve_collection("TestEmpty")

    imap_resource.set_online(False)

    # Append the item to Akonadi
    akonadi_client.add_item(
        collection.id(),
        create_message(subject="test_append_message").as_bytes(),
        "message/rfc822",
    )

    items = akonadi_client.list_items(collection.id())
    assert len(items) == 1

    # No messages should have been added to imap server at this point
    imap_client.folder.set("TestEmpty")
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == 0

    imap_resource.set_online(True)

    wait_until(lambda: message_added(imap_client, "TestEmpty", "1"))

    imap_client.folder.set("TestEmpty")
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == 1

    check_collection_in_sync("TestEmpty", imap_resource, imap_client)


""""
@pytest.mark.asyncio
async def test_sync_10000_messages(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    check_collection_in_sync("Test", imap_resource, imap_client)

    start = time.time()

    for _ in range(10000):
        imap_client.append(create_message(), "Test")

    imap_resource.sync_collection("Test")

    check_collection_in_sync("Test", imap_resource, imap_client)

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
