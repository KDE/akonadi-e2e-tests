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
from src.factories.email_factory import ImapEmailFactory, ImapFolderFactory, fake
from src.imap.email_utils import create_message
from src.imap.test_utils import (
    assert_all_collections_are_equals,
    assert_collection_equal_mailbox,
    assert_item_sync,
    assert_item_unsync,
    compare_flags,
)

log = getLogger(__name__)


def test_initial_sync(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Starting a first full sync leads to all the items and collections being replicated in the akonadi server
    """
    folder = ImapFolderFactory.create(nb_items=5)
    ImapEmailFactory.create_batch(10, folder="INBOX")

    imap_resource.synchronize()

    assert len(imap_resource.list_collections()) == 3  # INBOX, Test and IMAP Account
    assert len(imap_resource.list_items("INBOX")) == 10
    assert len(imap_resource.list_items(folder.name)) == 5

    assert len(imap_client.folder.list()) == 2

    imap_client.folder.set("INBOX")
    assert len(list(imap_client.fetch(mark_seen=False))) == 10
    imap_client.folder.set(folder.name)
    assert len(list(imap_client.fetch(mark_seen=False))) == 5

    assert_collection_equal_mailbox("INBOX", imap_resource, imap_client)
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_new_mailbox_on_server_is_synced(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,  # noqa: ARG001
) -> None:
    """
    Adding a collection in the server implicitly triggers a partial sync
    The added collection is replicated in the akonadi server
    No other change occurred (other than timestamps book keeping)
    """
    folder = ImapFolderFactory.create(nb_items=0)
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert any(lambda c: c.name() == folder.name for c in collections)


def test_mailbox_deleted_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Removing a collection from the server implicitly triggers a partial sync
    The removed collection is also removed from the akonadi server
    No other change occurred (other than timestamps book keeping)
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete(folder.name)

    assert not imap_client.folder.exists(folder.name)
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert folder.name not in list(map(lambda c: c.name(), collections))


@pytest.mark.xfail(
    reason="IMAP/Akonadi bug? The old and new items get merged based on RID despite the UIDVALIDITY change."
)
def test_uidvalidity_change_detected(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Recreating a mailbox on the server, the change is replayed on the resource
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete(folder.name)
    imap_client.folder.create(folder.name)
    imap_client.append(create_message().as_bytes(), folder.name)

    imap_resource.synchronize()

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_removed_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Deleting a message on the server, the change is replayed on the resource
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    imap_client.delete(["1"])
    imap_resource.sync_collection(folder.name)
    assert len(imap_resource.list_items(folder.name)) == len(folder.messages) - 1

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_added_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Adding a message on the server, the change is replayed on the resource
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    ImapEmailFactory.create(folder=folder.name)
    imap_resource.sync_collection(
        folder.name
    )  # Doing a double sync as check collection in sync, do a sync too
    assert len(imap_resource.list_items(folder.name)) == len(folder.messages) + 1

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Adding and removing a message on the server, the message is not present in the resource
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    ImapEmailFactory.create(folder=folder.name)
    imap_client.delete(["1"])
    imap_resource.sync_collection(folder.name)

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Changing the flag of a message on the server, the change is replayed on the resource
    """
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create_batch(2, folder=folder.name, flags=[])
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    imap_client.flag(["1"], ["$TestFlag"], True)
    imap_resource.sync_collection(folder.name)

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing the flag and deleting a different message on the server, the changes are replayed on the resource
    """
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create_batch(2, folder=folder.name, flags=[])
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.delete(["1"])
    imap_resource.sync_collection(folder.name)

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing the flag and adding a different message on the server, the changes are replayed on the resource
    """
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create_batch(2, folder=folder.name, flags=[])
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    imap_client.flag(["2"], "$TestFlag", True)
    ImapEmailFactory.create(folder=folder.name)
    imap_resource.sync_collection(folder.name)

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_sync_flag_change_and_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing the flag, adding and removing a different message on the server, the changes are replayed on the resource
    """
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create_batch(2, folder=folder.name, flags=[])
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    imap_client.flag(["2"], "$TestFlag", True)
    ImapEmailFactory.create(folder=folder.name)
    imap_client.delete(["1"])

    imap_resource.sync_collection(folder.name)

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_offline_change_email_flags_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Changing flags of an item on the server while the resource is offline, nothing happens
    When the resource is online, the flags are replicated and no other change occurred
    """
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create(folder=folder.name, flags=("\\Draft"))
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    # Set offline and change server flags
    [item] = imap_resource.list_items(folder.name)
    imap_resource.set_online(False)
    imap_client.folder.set(folder.name)
    imap_client.flag([item.remoteId()], "\\Flagged", True)
    imap_client.flag([item.remoteId()], "\\Draft", False)

    # Check nothing happened
    [item] = [i for i in imap_resource.list_items(folder.name) if i.id() == item.id()]
    flags = [bytes(f).decode() for f in item.flags()]
    assert compare_flags(flags, ["\\Draft"])

    # Set collection online and ensure flags have not yet changed
    imap_resource.set_online(True)
    [item] = [i for i in imap_resource.list_items(folder.name) if i.id() == item.id()]
    flags = [bytes(f).decode() for f in item.flags()]
    assert compare_flags(flags, ["\\Draft"])

    # Sync and check flags have changes
    imap_resource.sync_collection(folder.name)
    [item] = [i for i in imap_resource.list_items(folder.name) if i.id() == item.id()]
    flags = [bytes(f).decode() for f in item.flags()]
    assert compare_flags(flags, ["\\Flagged"])

    assert_all_collections_are_equals(imap_client, imap_resource)


def test_offline_removed_message_server_side(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Removing a message on the server while offline, the message is removed in the resource when online
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    # Issuing set_online(False) while the IMAP resource is not idle might lead to crashes
    imap_resource.wait_resource_is_idle()
    imap_resource.set_online(False)

    imap_resource.list_items(folder.name)
    imap_client.delete(["1"])

    # Make sure this resource isn't updated when offline
    assert len(imap_resource.list_items(folder.name)) == len(folder.messages)

    imap_resource.set_online(True)
    imap_resource.sync_collection(folder.name)
    assert len(imap_resource.list_items(folder.name)) == len(folder.messages) - 1

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_offline_append_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Add a message on the server side when offline
    Check sync after online
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    # Issuing set_online(False) while the IMAP resource is not idle might lead to crashes
    imap_resource.wait_resource_is_idle()
    imap_resource.set_online(False)

    ImapEmailFactory.create(folder=folder.name)
    # Make sure this resource isn't updated when offline
    assert len(imap_resource.list_items(folder.name)) == len(folder.messages)

    imap_resource.set_online(True)
    imap_resource.sync_collection(folder.name)
    assert len(imap_resource.list_items(folder.name)) == len(folder.messages) + 1

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


@pytest.mark.xfail(reason="Akonadi bug? ModificationTime is not updated")
def test_partial_sync_on_flag_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Changing flags of an item on the server implicitly triggers a partial sync
    The flags are also changed on the corresponding item in the akonadi server
    No other change occurred (other than timestamps book keeping)
    """
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create_batch(2, folder=folder.name, flags=[])
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    initial_items = imap_resource.list_items(folder.name)
    item_to_update = initial_items[0]

    imap_client.folder.set(folder.name)
    imap_client.flag([item_to_update.remoteId()], ["$TestFlag"], True)
    imap_resource.sync_collection(folder.name)
    current_items = imap_resource.list_items(folder.name)

    initial_items.sort(key=lambda i: i.id())
    current_items.sort(key=lambda i: i.id())

    for initial_item, current_item in zip(initial_items, current_items, strict=True):
        # updated item should have been sync
        if initial_item.id() == item_to_update.id():
            assert_item_sync(initial_item, current_item)
        # other items should not have been sync
        else:
            assert_item_unsync(initial_item, current_item)

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_partial_sync_on_append_msg(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Adding an item to a collection on the server implicitly triggers a partial sync
    The added item is replicated in the akonadi server
    No other change occurred (other than timestamps book keeping)
    """
    folder = ImapFolderFactory.create(nb_items=5)
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    initial_items = imap_resource.list_items(folder.name)
    assert len(initial_items) == 5

    for _ in range(5):
        ImapEmailFactory.create(folder=folder.name)
        imap_resource.sync_collection(folder.name)

    updated_items = imap_resource.list_items(folder.name)
    items_added = [item for item in updated_items if item not in initial_items]
    items_added_id = [item.id() for item in items_added]

    assert len(updated_items) == 10
    assert len(items_added) == 5
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    for item in updated_items:
        # Added item should have no revision, aka revision to 0, and modificationTime not none
        if item.id() in items_added_id:
            assert item.revision() == 0
            assert item.modificationTime().toMSecsSinceEpoch() is not None
        else:
            [initial_item] = [
                initial_item for initial_item in initial_items if initial_item == item
            ]
            assert_item_unsync(initial_item, item)


@pytest.mark.xfail(
    reason="Fail on CYRUS only, unchanged items are actually sync, revision is updated"
)
def test_partial_sync_on_delete_msg(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Removing an item from a collection on the server implicitly triggers a partial sync, the removed item is also removed in the akonadi server, no other change occurred.
    To do this check, we actually look that all other items are unsynced
    """
    custom_folder = ImapFolderFactory.create(nb_items=5)
    inbox_folder = "INBOX"
    ImapEmailFactory.create_batch(10, folder=inbox_folder)
    imap_resource.synchronize()

    # Check custom_folder before deleting
    assert_collection_equal_mailbox(custom_folder.name, imap_resource, imap_client)
    custom_folder_initial_items = imap_resource.list_items(custom_folder.name)
    assert len(custom_folder_initial_items) == 5

    # Check inbox folder before deleting
    assert_collection_equal_mailbox(inbox_folder, imap_resource, imap_client)
    inbox_folder_initial_items = imap_resource.list_items(inbox_folder)
    assert len(inbox_folder_initial_items) == 10

    custom_folder_msgs_to_delete = custom_folder_initial_items[:3]
    inbox_folder_msgs_to_delete = inbox_folder_initial_items[:6]

    # delete msgs in custom_folder
    imap_client.folder.set(custom_folder.name)
    for msg in custom_folder_msgs_to_delete:
        imap_client.delete(msg.remoteId())

    # delete msgs in inbox folder
    imap_client.folder.set(inbox_folder)
    for msg in inbox_folder_msgs_to_delete:
        imap_client.delete(msg.remoteId())

    imap_resource.synchronize()
    custom_folder_current_items = imap_resource.list_items(custom_folder.name)
    inbox_folder_current_items = imap_resource.list_items(inbox_folder)

    # check msg in custom folder
    assert len(custom_folder_current_items) == 2
    assert_collection_equal_mailbox(custom_folder.name, imap_resource, imap_client)

    for item in custom_folder_current_items:
        # Check that unchanged item is unsync
        [initial_item] = [
            initial_item for initial_item in custom_folder_initial_items if initial_item == item
        ]
        assert_item_unsync(initial_item, item)

    # Check that deleted item is not in the current collection
    for msg in custom_folder_msgs_to_delete:
        assert msg not in custom_folder_current_items

    # check msg in inbox folder
    assert len(inbox_folder_current_items) == 4
    assert_collection_equal_mailbox(inbox_folder, imap_resource, imap_client)

    for item in inbox_folder_current_items:
        # Check that unchanged item is unsync
        [initial_item] = [
            initial_item for initial_item in inbox_folder_initial_items if initial_item == item
        ]
        assert_item_unsync(initial_item, item)

    # Check that deleted item is not in the current collection
    for msg in inbox_folder_msgs_to_delete:
        assert msg not in custom_folder_current_items

    assert_all_collections_are_equals(imap_client, imap_resource)


def test_server_offline_rename_collection(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Renaming a collection in the server, nothing happens, when the resource is set online, the collection is also
    renamed in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    old_name = ImapFolderFactory.create().name
    imap_resource.synchronize()

    new_name = fake.word()
    initial_collections = imap_resource.list_collections()

    assert old_name in (collection.name() for collection in initial_collections)
    assert new_name not in (collection.name() for collection in initial_collections)
    assert imap_client.folder.exists(old_name)
    assert not imap_client.folder.exists(new_name)

    imap_resource.set_online(False)
    imap_client.folder.rename(old_name, new_name)

    assert not imap_client.folder.exists(old_name)
    assert imap_client.folder.exists(new_name)

    # Here we need to test that nothing happens in the akonadi server
    offline_collections = imap_resource.list_collections()

    assert old_name in (collection.name() for collection in offline_collections)
    assert new_name not in (collection.name() for collection in offline_collections)

    imap_resource.set_online(True)

    updated_offline_collections = imap_resource.list_collections()

    assert old_name not in (collection.name() for collection in updated_offline_collections)
    assert new_name in (collection.name() for collection in updated_offline_collections)

    imap_resource.sync_collection(new_name)

    assert_collection_equal_mailbox(new_name, imap_resource, imap_client)
