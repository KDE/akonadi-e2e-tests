# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny Lorin <kenny.lorin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from logging import getLogger

import pytest
from imap_tools import BaseMailBox

from akonadi.client import AkonadiClient
from imap.email_utils import create_message
from src.akonadi.imap_resource import ImapResource
from src.imap.test_utils import assert_collection_equal_mailbox, old_prepare

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
    old_prepare(imap_client, imap_resource)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

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
    reason="The tests are flaky/not stable, we xfail conflict tests while stabilizing others"
)
def test_offline_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Flag change on an item from an offline resource and flag mail from a server
    When going back online, both items/mails are correctly flagged
    """
    old_prepare(imap_client, imap_resource)
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

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
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_add_item_in_akonadi_on_collection_removed_on_server(
        imap_resource: ImapResource,
        imap_client: BaseMailBox,
        akonadi_client: AkonadiClient,
) -> None:
    collection_name = "Test7"
    imap_client.folder.create(collection_name)
    imap_client.folder.set(collection_name)
    server_items_on_collection_creation = list(imap_client.fetch(mark_seen=False))
    imap_resource.synchronize()
    assert collection_name in (c.name() for c in imap_resource.list_collections())
    assert len(imap_resource.list_items(collection_name)) == len(server_items_on_collection_creation) == 0

    collection = imap_resource.resolve_collection(collection_name)
    imap_resource.set_online(False)

    akonadi_client.add_item(
        collection.id(),
        create_message(subject="test_add_item_in_akonadi_on_collection_removed_on_server").as_bytes(),
        "message/rfc822",
    )

    assert len(list(imap_client.fetch(mark_seen=False))) == len(server_items_on_collection_creation) # no message added to folder

    imap_client.folder.delete(collection_name)

    imap_resource.set_online(True)

    imap_resource.synchronize()
    assert collection_name not in (c.name() for c in imap_resource.list_collections())
    # Cannot fetch items on a deleted collection, assume it is gone as well


def test_remove_item_in_akonadi_on_collection_removed_on_server(
        imap_resource: ImapResource,
        imap_client: BaseMailBox,
        akonadi_client: AkonadiClient,
) -> None:
    collection_name = "Test7"
    imap_client.folder.create(collection_name)
    imap_client.folder.set(collection_name)
    imap_client.append(create_message().as_bytes(), collection_name)
    imap_resource.synchronize()
    assert collection_name in (c.name() for c in imap_resource.list_collections())
    pre_delete_items = list(imap_client.fetch(mark_seen=False))

    pre_delete_items_on_resource = imap_resource.list_items(collection_name)
    imap_resource.set_online(False)

    akonadi_client.delete_item(pre_delete_items_on_resource[-1].id()) # the last item is the one we added earlier, so it is the one we remove

    assert len(list(imap_client.fetch(mark_seen=False))) == len(pre_delete_items)

    imap_client.folder.delete(collection_name)

    imap_resource.set_online(True)

    imap_resource.synchronize()
    assert collection_name not in (c.name() for c in imap_resource.list_collections())
    # Cannot fetch items on a deleted collection, assume it is gone as well


def test_update_item_in_akonadi_on_collection_removed_on_server(
        imap_resource: ImapResource,
        imap_client: BaseMailBox,
        akonadi_client: AkonadiClient,
) -> None:
    collection_name = "Test7"
    flag_to_add = "\\Draft"
    imap_client.folder.create(collection_name)
    imap_client.folder.set(collection_name)
    imap_client.append(create_message().as_bytes(), collection_name)
    imap_resource.synchronize()
    assert collection_name in (c.name() for c in imap_resource.list_collections())
    pre_update_items_on_resource = imap_resource.list_items(collection_name)
    pre_update_items_on_server = list(imap_client.fetch(mark_seen=False))
    assert len(pre_update_items_on_server) == len(pre_update_items_on_resource) == 1
    assert flag_to_add not in pre_update_items_on_server[0].flags

    imap_resource.set_online(False)

    imap_resource.add_flag(pre_update_items_on_resource[-1].id(), flag_to_add)

    imap_client.folder.delete(collection_name)

    imap_resource.set_online(True)

    imap_resource.synchronize()
    assert collection_name not in (c.name() for c in imap_resource.list_collections())
    # Cannot fetch items on a deleted collection, assume it is gone as well
