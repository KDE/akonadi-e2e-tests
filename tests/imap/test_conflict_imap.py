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
from src.factories.email_factory import ImapFolderFactory
from src.imap.test_utils import assert_collection_equal_mailbox

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
    folder = ImapFolderFactory.create(nb_items=2).name
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