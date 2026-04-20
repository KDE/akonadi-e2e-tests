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
from src.akonadi.utils import AkonadiUtils
from src.factories.email_factory import ImapEmailFactory, ImapFolderFactory, fake
from src.imap.test_utils import (
    assert_all_collections_are_equals,
    assert_collection_equal_mailbox,
    message_added,
)
from src.test import wait_until

log = getLogger(__name__)


@pytest.mark.xfail(
    reason="The tests are flaky/not stable, we xfail conflict tests while stabilizing others"
)
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


@pytest.mark.xfail(
    reason="The tests are flaky/not stable, we xfail conflict tests while stabilizing others"
)
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
    imap_resource.add_flag(item.id(), "$TestFlag2")

    imap_resource.set_online(True)
    imap_resource.sync_collection(folder)
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

    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
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

    imap_client.folder.set(server_new_name)
    assert len(imap_resource.list_items(server_new_name)) == len(
        list(imap_client.fetch(mark_seen=False))
    )

    assert_collection_equal_mailbox(server_new_name, imap_resource, imap_client)
    assert_all_collections_are_equals(imap_client, imap_resource)
