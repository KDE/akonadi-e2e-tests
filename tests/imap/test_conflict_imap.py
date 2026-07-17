# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Alan Thouvenin <alan.thouvenin@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny Lorin <kenny.lorin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from logging import getLogger

import pytest
from imap_tools import BaseMailBox

from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.akonadi.utils import AkonadiUtils, WaitJobError
from src.factories.email_factory import (
    AkonadiEmailFactory,
    ImapEmailFactory,
    ImapFolderFactory,
    fake,
)
from src.imap.test_utils import (
    assert_all_collections_are_equals,
    assert_collection_equal_mailbox,
    has_flag,
    message_added,
)
from src.test import wait_until

log = getLogger(__name__)


def test_mailbox_deleted_on_server_is_unsynced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Deleting a collection from an offline resource and deleting a mailbox from a server
    When going back online, both collection/mailbox are deleted
    """
    mailbox_to_delete = ImapFolderFactory.create().name
    collection_to_delete = ImapFolderFactory.create().name
    imap_resource.synchronize()

    assert_collection_equal_mailbox(mailbox_to_delete, imap_resource, imap_client)
    assert_collection_equal_mailbox(collection_to_delete, imap_resource, imap_client)

    imap_resource.set_online(False)

    imap_client.folder.set(
        "INBOX"
    )  # Needed to avoid CREATE => Selected mailbox was deleted, have to disconnect
    imap_client.folder.delete(mailbox_to_delete)
    imap_resource.delete_collection(collection_to_delete)

    # check mailboxes in disconnected state
    collections_akonadi = imap_resource.list_collections()
    assert mailbox_to_delete in list(map(lambda c: c.name(), collections_akonadi))
    assert imap_client.folder.exists(collection_to_delete)

    # reconnect
    imap_resource.set_online(True)
    imap_resource.synchronize()

    # check that both imap and akonadi server are properly synchronised
    collections_akonadi = imap_resource.list_collections()
    assert mailbox_to_delete not in list(map(lambda c: c.name(), collections_akonadi))
    assert not imap_client.folder.exists(collection_to_delete)


def test_remove_collection_on_server(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Removing a collection from the akonadi server, adding an item to the collection on the server, nothing happens, when
    the resource is set online, the change is replayed on the server and the collection is removed (including the newly
    added item)
    """

    # Create an initial collection with 5 items
    folder_to_delete = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder_to_delete.name, imap_resource, imap_client)
    assert len(list(imap_client.fetch(mark_seen=False))) == len(folder_to_delete.messages)

    imap_resource.set_online(False)

    # Remove collection from resource, add an item on the server
    imap_resource.delete_collection(folder_to_delete.name)
    ImapEmailFactory.create(folder=folder_to_delete.name)

    # Change is not propagated when offline
    assert folder_to_delete.name not in [c.name() for c in imap_resource.list_collections()]
    assert imap_client.folder.exists(folder_to_delete.name)
    assert len(list(imap_client.fetch(mark_seen=False))) == len(folder_to_delete.messages) + 1

    imap_resource.set_online(True)
    # Then the collection and its new item are removed from the server
    assert folder_to_delete.name not in [c.name() for c in imap_resource.list_collections()]
    assert not imap_client.folder.exists(folder_to_delete.name)

    imap_resource.synchronize()
    # Check that the collection does still not exist after a synchronize()
    assert folder_to_delete.name not in [c.name() for c in imap_resource.list_collections()]
    assert not imap_client.folder.exists(folder_to_delete.name)


def test_offline_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Flag change on an item from an offline resource and flag mail from a server
    When going back online, both items/mails are correctly flagged
    """
    folder = ImapFolderFactory.create(nb_items=0).name
    ImapEmailFactory.create_batch(2, folder=folder, flags=[])
    imap_resource.synchronize()

    assert_collection_equal_mailbox(folder, imap_resource, imap_client)

    imap_resource.set_online(False)

    collection = imap_resource.resolve_collection(folder)
    items = imap_resource.list_items(collection.id())
    item = items[0]
    imap_uid = item.remoteId()

    imap_client.folder.set(folder)
    imap_client.flag([imap_uid], "$TestFlag", True)

    imap_resource.add_flags(item.id(), {"$TestFlag2"})

    imap_resource.set_online(True)
    imap_resource.sync_collection(folder)
    wait_until(
        lambda: (
            has_flag(imap_client, item, folder, "$TestFlag")
            and has_flag(imap_client, item, folder, "$TestFlag2")
        )
    )
    assert_collection_equal_mailbox(folder, imap_resource, imap_client)


def test_conflict_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
) -> None:
    """
    Adding an item to a collection on the server, removing the collection in akonadi server, nothing happens.
    When the resource is set online, the collection is removed on the server
    """
    folder_name = ImapFolderFactory.create(nb_items=0).name
    imap_resource.synchronize()

    assert_collection_equal_mailbox(folder_name, imap_resource, imap_client)

    imap_resource.set_online(False)

    # Append the item to the server
    ImapEmailFactory.create(folder=folder_name)
    imap_client.folder.set(folder_name)
    wait_until(lambda: message_added(imap_client, folder_name, "1"))

    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        # Remove the collection from the akonadi server
        imap_resource.delete_collection(folder_name)
        assert folder_name not in [col.name() for col in imap_resource.list_collections()]

    imap_resource.set_online(True)

    wait_until(lambda: not imap_client.folder.exists(folder_name))
    assert folder_name not in [col.name() for col in imap_resource.list_collections()]


def test_akonadi_conflict_rename_collection(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Renaming a collection in the akonadi server, renaming the same collection under another name on the server, nothing happens.
    When the resource is set online, the collection in the akonadi server is renamed with the name given on the server
    """
    old_name = ImapFolderFactory.create().name
    imap_resource.synchronize()

    akonadi_new_name = f"{fake.word()}_{fake.word()}"
    server_new_name = f"{fake.word()}_{fake.word()}"
    initial_collections = imap_resource.list_collections()

    assert old_name in (collection.name() for collection in initial_collections)
    assert akonadi_new_name not in (collection.name() for collection in initial_collections)
    assert server_new_name not in (collection.name() for collection in initial_collections)

    assert imap_client.folder.exists(old_name)
    assert not imap_client.folder.exists(akonadi_new_name)
    assert not imap_client.folder.exists(server_new_name)

    imap_resource.set_online(False)
    imap_resource.rename_collection(old_name, akonadi_new_name)
    imap_client.folder.rename(old_name, server_new_name)

    updated_akonadi_collections = imap_resource.list_collections()

    assert old_name not in (collection.name() for collection in updated_akonadi_collections)
    assert akonadi_new_name in (collection.name() for collection in updated_akonadi_collections)
    assert server_new_name not in (collection.name() for collection in updated_akonadi_collections)

    assert not imap_client.folder.exists(old_name)
    assert not imap_client.folder.exists(akonadi_new_name)
    assert imap_client.folder.exists(server_new_name)

    imap_resource.set_online(True)

    # At this point we're sure old_name is not a collection's name on akonadi or server's side, so no need to test it again

    updated_akonadi_collections = imap_resource.list_collections()

    assert akonadi_new_name not in (collection.name() for collection in updated_akonadi_collections)
    assert server_new_name in (collection.name() for collection in updated_akonadi_collections)

    assert not imap_client.folder.exists(akonadi_new_name)
    assert imap_client.folder.exists(server_new_name)

    assert len(imap_resource.list_items(server_new_name)) == 0

    imap_resource.sync_collection(server_new_name)
    wait_until(lambda: imap_client.folder.exists(server_new_name))
    imap_client.folder.set(server_new_name)
    wait_until(
        lambda: (
            len(imap_resource.list_items(server_new_name))
            == len(list(imap_client.fetch(mark_seen=False)))
        )
    )

    assert_collection_equal_mailbox(server_new_name, imap_resource, imap_client)
    assert_all_collections_are_equals(imap_client, imap_resource)


def test_add_item_in_akonadi_on_collection_removed_on_server(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    While the resource is offline, adding an item to a collection in the akonadi server while deleting the same
    collection on the IMAP server
    Then both the item and the collection should be removed from akonadi once the resource comes back online
    """
    folder = ImapFolderFactory.create(nb_items=0)
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_resource.set_online(False)

    AkonadiEmailFactory.create(folder=folder.name)
    collection = imap_resource.resolve_collection(folder.name)
    created_item = akonadi_client.list_items(collection.id())[0]

    assert len(list(imap_client.fetch(mark_seen=False))) == 0  # no message added to folder

    imap_client.folder.delete(folder.name)

    imap_resource.set_online(True)

    assert folder.name not in (c.name() for c in imap_resource.list_collections())
    with pytest.raises(WaitJobError):
        akonadi_client.item_by_id(created_item.id())


def test_remove_item_in_akonadi_on_collection_removed_on_server(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    While the resource is offline, removing an item to a collection in the akonadi server while deleting the same
    collection on the IMAP server
    Then both the item and the collection should be removed from akonadi once the resource comes back online
    """
    folder = ImapFolderFactory.create(nb_items=1)
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)

    pre_delete_items_on_resource = imap_resource.list_items(folder.name)
    imap_resource.set_online(False)

    akonadi_client.delete_item(pre_delete_items_on_resource[0].id())

    assert (
        len(list(imap_client.fetch(mark_seen=False))) == 1
    )  # item was not deleted on the remote server

    imap_client.folder.delete(folder.name)

    imap_resource.set_online(True)

    assert folder.name not in (c.name() for c in imap_resource.list_collections())
    # item deleted by the resource, querying it should throw
    with pytest.raises(WaitJobError):
        akonadi_client.item_by_id(pre_delete_items_on_resource[0].id())


def test_update_item_in_akonadi_on_collection_removed_on_server(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    While the resource is offline, changing the flags of an item to a collection in the akonadi server while deleting
    the same collection on the IMAP server
    Then both the item and the collection should be removed from akonadi once the resource comes back online
    """
    flag_to_add = set("\\Draft")
    folder = ImapFolderFactory.create(nb_items=0)
    ImapEmailFactory.create(folder=folder.name, flags=[])
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    pre_update_items_on_resource = imap_resource.list_items(folder.name)
    imap_client.folder.set(folder.name)
    pre_update_items_on_server = list(imap_client.fetch(mark_seen=False))
    assert len(pre_update_items_on_server) == len(pre_update_items_on_resource) == 1
    assert len(pre_update_items_on_server[0].flags) == 0

    imap_resource.set_online(False)

    imap_resource.add_flags(pre_update_items_on_resource[0].id(), flag_to_add)

    imap_client.folder.delete(folder.name)

    imap_resource.set_online(True)

    assert folder.name not in (c.name() for c in imap_resource.list_collections())
    with pytest.raises(WaitJobError):
        akonadi_client.item_by_id(pre_update_items_on_resource[0].id())


def test_offline_delete_item_server_side_delete_collection_akonadi_side(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Removing an item from a collection on the server, removing the collection in akonadi server, nothing happens, when the resource is set online, the collection is removed on the server
    """
    folder = ImapFolderFactory.create(nb_items=5)
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    collection_to_delete = imap_resource.resolve_collection(folder.name)

    items = imap_resource.list_items(collection_to_delete.id())
    items_to_delete = items[:3]

    imap_resource.set_online(False)
    imap_client.folder.set(folder.name)
    imap_client.delete([item.remoteId() for item in items_to_delete])
    imap_resource.delete_collection(folder.name)

    # check state before reconnect
    collections_akonadi = imap_resource.list_collections()
    assert collection_to_delete.name() not in [coll.name() for coll in collections_akonadi]
    assert imap_client.folder.exists(collection_to_delete.name())
    assert len(list(imap_client.fetch(mark_seen=False))) == len(folder.messages) - len(
        items_to_delete
    )

    imap_resource.set_online(True)
    imap_resource.synchronize()

    # check state after reconnection, collection should be deleted on the server side
    assert collection_to_delete.name() not in [coll.name() for coll in collections_akonadi]
    assert not imap_client.folder.exists(collection_to_delete.name())
