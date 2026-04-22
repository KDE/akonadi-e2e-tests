# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from logging import getLogger

import pytest
from imap_tools import BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.factories.email_factory import (
    ImapEmailFactory,
    ImapFolderFactory,
)
from src.imap.email_utils import create_message
from src.imap.test_utils import assert_collection_equal_mailbox, assert_partial_sync, old_prepare
from src.test.wait import wait_until

log = getLogger(__name__)


def test_initial_sync(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Starting a first full sync leads to all the items and collections being replicated in the akonadi server
    """
    ImapFolderFactory.create(name="Test", nb_items=5)
    ImapEmailFactory.create_batch(10, folder="INBOX")

    imap_resource.synchronize()

    assert len(imap_resource.list_collections()) == 3  # INBOX, Test and IMAP Account
    assert len(imap_resource.list_items("INBOX")) == 10
    assert len(imap_resource.list_items("Test")) == 5

    assert len(imap_client.folder.list()) == 2

    imap_client.folder.set("INBOX")
    assert len(list(imap_client.fetch(mark_seen=False))) == 10
    imap_client.folder.set("Test")
    assert len(list(imap_client.fetch(mark_seen=False))) == 5

    assert_collection_equal_mailbox("INBOX", imap_resource, imap_client)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_new_mailbox_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Creating a new mailbox on the server, the change is replayed on the resource
    """
    ImapFolderFactory.create(name="test_new_mailbox_on_server_is_synced", nb_items=0)
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert any(lambda c: c.name() == "test_new_mailbox_on_server_is_synced" for c in collections)


def test_mailbox_deleted_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Deleting a mailbox on the server, the change is replayed on the resource
    """
    ImapFolderFactory.create(name="to_be_deleted")
    imap_resource.synchronize()
    assert_collection_equal_mailbox("to_be_deleted", imap_resource, imap_client)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete("to_be_deleted")

    assert not imap_client.folder.exists("to_be_deleted")
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert "to_be_deleted" not in list(map(lambda c: c.name(), collections))


@pytest.mark.xfail(
    reason="IMAP/Akonadi bug? The old and new items get merged based on RID despite the UIDVALIDITY change."
)
def test_uidvalidity_change_detected(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Recreating a mailbox on the server, the change is replayed on the resource
    """
    ImapFolderFactory.create(name="Test")
    imap_resource.synchronize()
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete("Test")
    imap_client.folder.create("Test")
    imap_client.append(create_message().as_bytes(), "Test")

    imap_resource.synchronize()

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_removed_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Deleting a message on the server, the change is replayed on the resource
    """
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    imap_resource.synchronize()

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_added_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Adding a message on the server, the change is replayed on the resource
    """
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.append(create_message().as_bytes(), "Test")
    imap_resource.sync_collection(
        "Test"
    )  # Doing a double sync as check collection in sync, do a sync too

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Adding and removing a message on the server, the message is not present in the resource
    """
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    imap_client.append(create_message().as_bytes(), "Test")

    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Changing the flag of a message on the server, the change is replayed on the resource
    """
    old_prepare(imap_client, imap_resource)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.folder.set("Test")
    imap_client.flag(["1"], ["$TestFlag"], True)
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing the flag and deleting a different message on the server, the changes are replayed on the resource
    """
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing the flag and adding a different message on the server, the changes are replayed on the resource
    """
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_change_and_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing the flag, adding and removing a different message on the server, the changes are replayed on the resource
    """
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_offline_removed_message_server_side(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    old_prepare(imap_client, imap_resource)
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    # Issuing set_online(False) while the IMAP resource is not idle
    # might lead to crashes
    imap_resource.wait_resource_is_idle()
    imap_resource.set_online(False)

    items = imap_resource.list_items("Test")
    item_to_delete = items[0]
    imap_client.delete(item_to_delete.remoteId())

    # Make sure this resource isn't updated when offline
    assert len(imap_resource.list_items("Test")) == 2

    imap_resource.set_online(True)
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert len(imap_resource.list_items("Test")) == 1


def test_offline_append_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Add a message on the server side when offline
    Check sync after online
    """
    old_prepare(imap_client, imap_resource)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    # Issuing set_online(False) while the IMAP resource is not idle
    # might lead to crashes
    imap_resource.wait_resource_is_idle()
    imap_resource.set_online(False)

    imap_client.append(create_message("appendTest").as_bytes(), "Test")
    # Make sure this resource isn't updated when offline
    assert len(imap_resource.list_items("Test")) == 2

    imap_resource.set_online(True)
    imap_resource.sync_collection("Test")

    assert len(imap_resource.list_items("Test")) == 3
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


@pytest.mark.xfail(reason="Akonadi bug? ModificationTime is not updated")
def test_partial_sync_on_flag_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Check that only the updated item has been sync
    """
    old_prepare(imap_client, imap_resource)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    initial_items = imap_resource.list_items("Test")
    item_to_update = initial_items[0]

    imap_client.folder.set("Test")
    imap_client.flag([item_to_update.remoteId()], ["$TestFlag"], True)
    imap_resource.sync_collection("Test")
    updated_items = imap_resource.list_items("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert_partial_sync(initial_items, updated_items, [item_to_update])


def test_partial_sync_on_append_msg(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Check that only the added items has been sync
    """
    old_prepare(imap_client, imap_resource)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    initial_items = imap_resource.list_items("Test")
    assert len(initial_items) == 2

    for _ in range(5):
        msg_to_append = create_message("appendTest")
        imap_client.append(msg_to_append.as_bytes(), "Test")
        imap_resource.sync_collection("Test")

    updated_items = imap_resource.list_items("Test")
    items_added = [item for item in updated_items if item not in initial_items]

    assert len(updated_items) == 7
    assert len(items_added) == 5
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert_partial_sync(initial_items, updated_items, items_added)

def test_total_sync_on_append_msg(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    When an item has been added to INBOX mailbox server-side, the change is replayed on the akonadi server without the need to sync
    """
    # Create some items that should not have been synced at the end of the test
    ImapEmailFactory.create_batch(10, folder="INBOX")
    imap_resource.synchronize()

    assert_collection_equal_mailbox("INBOX", imap_resource, imap_client)
    initial_items = imap_resource.list_items("INBOX")
    assert len(initial_items) == 10

    ImapEmailFactory.create(folder="INBOX")

    wait_until(lambda: len(imap_resource.list_items("INBOX")) == 11)

    updated_items = imap_resource.list_items("INBOX")
    items_added = [item for item in updated_items if item not in initial_items]

    assert_collection_equal_mailbox("INBOX", imap_resource, imap_client)
    assert_partial_sync(initial_items, updated_items, items_added)
