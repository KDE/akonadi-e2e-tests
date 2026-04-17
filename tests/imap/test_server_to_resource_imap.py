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
from imap_tools import BaseMailBox, MailboxFolderDeleteError, MailboxFolderRenameError

from src.akonadi.imap_resource import ImapResource
from src.imap.email_utils import create_message
from src.imap.test_utils import assert_collection_equal_mailbox

log = getLogger(__name__)


def test_mailbox_created_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Creating a new mailbox on the server, the change is replayed on the resource
    """
    imap_client.folder.create("Test3")
    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert "Test3" in (c.name() for c in collections)


def test_mailbox_deleted_on_server_is_synced(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Deleting a mailbox on the server, the change is replayed on the resource
    """
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

    assert "Test" not in (c.name() for c in imap_resource.list_collections())


def test_mailbox_renamed_on_server_is_synced(
        imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Renaming a mailbox on the server, the change is replayed on the resource
    """
    collection_to_rename = "Test"
    collection_new_name = "Test6"

    for _ in range(5):
        try:
            imap_client.folder.rename(collection_to_rename, collection_new_name)
        except MailboxFolderRenameError:
            time.sleep(0.2)

    imap_resource.synchronize()

    collections = imap_resource.list_collections()
    assert collection_to_rename not in (c.name() for c in collections)
    assert collection_new_name in (c.name() for c in collections)


@pytest.mark.xfail(
    reason="IMAP/Akonadi bug? The old and new items get merged based on RID despite the UIDVALIDITY change."
)
def test_uidvalidity_change_detected(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Recreating a mailbox on the server, the change is replayed on the resource
    """
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
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.delete(["1"])
    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_sync_added_message(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Adding a message on the server, the change is replayed on the resource
    """
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
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    imap_client.flag(["2"], "$TestFlag", True)
    imap_client.append(create_message().as_bytes(), "Test")
    imap_client.delete(["1"])

    imap_resource.sync_collection("Test")

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
