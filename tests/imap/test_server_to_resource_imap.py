# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import time
from logging import getLogger

import pytest
from imap_tools import BaseMailBox, MailboxFolderDeleteError

from src.akonadi.imap_resource import ImapResource
from src.imap.email_utils import create_message
from src.imap.test_utils import assert_collection_equal_mailbox

log = getLogger(__name__)


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
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

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


@pytest.mark.xfail(
    reason="IMAP/Akonadi bug? The old and new items get merged based on RID despite the UIDVALIDITY change."
)
def test_uidvalidity_change_detected(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
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
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_added_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
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
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    imap_client.append(create_message().as_bytes(), "Test")

    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_only_change(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.folder.set("Test")
    imap_client.flag(["1"], ["$TestFlag"], True)
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_change_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_change_and_added_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_flag_change_and_added_and_removed_message(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
