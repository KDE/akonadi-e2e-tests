# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from imap_tools import BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.factories.email_factory import (
    AkonadiEmailFactory,
    AkonadiFolderFactory,
    ImapEmailFactory,
    ImapFolderFactory,
)


def test_imap_factory(imap_resource: ImapResource, imap_client: BaseMailBox):  # noqa: ARG001
    ImapFolderFactory.create(name="Test", nb_items=5)
    ImapEmailFactory.create_batch(10, folder="INBOX")

    assert len(imap_client.folder.list()) == 2
    imap_client.folder.set("INBOX")
    assert len(list(imap_client.fetch(mark_seen=False))) == 10
    imap_client.folder.set("Test")
    assert len(list(imap_client.fetch(mark_seen=False))) == 5


def test_imap_resource_factory(imap_resource: ImapResource, imap_client: BaseMailBox):  # noqa: ARG001
    AkonadiFolderFactory.create(name="Test", nb_items=5)
    AkonadiEmailFactory.create_batch(10, folder="INBOX")

    imap_resource.wait_resource_is_idle()
    assert len(imap_resource.list_collections()) == 3  # INBOX, Test and IMAP Account
    assert len(imap_resource.list_items("INBOX")) == 10
    assert len(imap_resource.list_items("Test")) == 5

