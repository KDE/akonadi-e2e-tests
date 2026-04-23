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
from AkonadiCore import Akonadi
from imap_tools import BaseMailBox

from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.akonadi.utils import AkonadiUtils
from src.factories.email_factory import (
    AkonadiEmailFactory,
    AkonadiFolderFactory,
    ImapFolderFactory,
    fake,
)
from src.imap.test_utils import (
    assert_akonadi_items_are_equal,
    assert_collection_equal_mailbox,
    has_flag,
    message_added,
    message_deleted,
)
from src.test import wait_until

log = getLogger(__name__)


def test_akonadi_sync_add_collection(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Adding a collection in the akonadi server, the change is replayed on the server
    """
    # Create toplevel collection
    toplevel_folder = AkonadiFolderFactory.create()
    wait_until(lambda: imap_client.folder.exists(toplevel_folder.name))

    child_folder = AkonadiFolderFactory.create(parent=toplevel_folder)
    wait_until(lambda: imap_client.folder.exists(child_folder.imap_path))

    assert_collection_equal_mailbox(toplevel_folder.name, imap_resource, imap_client)
    assert_collection_equal_mailbox(child_folder.imap_path, imap_resource, imap_client)


def test_akonadi_sync_delete_collection(
    imap_resource: ImapResource,  # noqa: ARG001
    imap_client: BaseMailBox,
) -> None:
    """
    Deleting a collection in the akonadi server, the change is replayed on the server
    """
    toplevel_folder = AkonadiFolderFactory.create()
    child_folder = AkonadiFolderFactory.create(parent=toplevel_folder)
    wait_until(
        lambda: (
            imap_client.folder.exists(toplevel_folder.name)
            and imap_client.folder.exists(child_folder.imap_path)
        )
    )

    # Delete parent collection
    job = Akonadi.CollectionDeleteJob(toplevel_folder.get_collection())
    AkonadiUtils.wait_for_job(job)

    wait_until(
        lambda: (
            not imap_client.folder.exists(toplevel_folder.name)
            and not imap_client.folder.exists(child_folder.imap_path)
        )
    )


def test_rename_collection(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
) -> None:
    """
    Test renaming a collection in akonadi side when online and verifying the change in both Akonadi and IMAP server.
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    initial_collections = imap_resource.list_collections()
    initial_items = imap_resource.list_items(folder.name)

    old_name, new_name = folder.name, fake.word()
    assert old_name in [c.name() for c in initial_collections]
    assert new_name not in [c.name() for c in initial_collections]

    # If the rename request arrives to quickly after the sync and list
    # somehow the rename never reaches the resource... there is a bug
    # somewhere in the chain
    time.sleep(0.1)
    imap_resource.rename_collection(old_name, new_name)

    updated_collections = imap_resource.list_collections()
    updated_items = imap_resource.list_items(new_name)

    assert new_name in [c.name() for c in updated_collections]
    assert old_name not in [c.name() for c in updated_collections]

    # Check in imap server that the new collection exists and the old one is deleted
    wait_until(lambda: not imap_client.folder.exists(old_name))
    assert_collection_equal_mailbox(new_name, imap_resource, imap_client)

    # Check that the renamed collection has the same items as the original one
    assert len(initial_items) == len(updated_items)
    initial_items.sort(key=lambda item: item.id())
    updated_items.sort(key=lambda item: item.id())
    for initial_item, updated_item in zip(initial_items, updated_items, strict=False):
        assert_akonadi_items_are_equal(initial_item, updated_item)


def test_akonadi_offline_delete_collection(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Removing a collection from the akonadi server, nothing happens, when the resource is set online, the change is replayed on the server
    """
    toplevel_folder = AkonadiFolderFactory.create()
    child_folder = AkonadiFolderFactory.create(parent=toplevel_folder)
    wait_until(
        lambda: (
            imap_client.folder.exists(toplevel_folder.name)
            and imap_client.folder.exists(child_folder.imap_path)
        )
    )

    imap_resource.set_online(False)

    # Delete parent collection
    job = Akonadi.CollectionDeleteJob(toplevel_folder.get_collection())
    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        AkonadiUtils.wait_for_job(job)

    resource_collections = imap_resource.list_collections()
    assert toplevel_folder.name not in [c.name() for c in resource_collections]
    assert child_folder.name not in [c.name() for c in resource_collections]
    assert imap_client.folder.exists(toplevel_folder.name)
    assert imap_client.folder.exists(child_folder.imap_path)

    imap_resource.set_online(True)

    resource_collections = imap_resource.list_collections()
    assert toplevel_folder.name not in [c.name() for c in resource_collections]
    assert child_folder.name not in [c.name() for c in resource_collections]
    wait_until(lambda: not imap_client.folder.exists(toplevel_folder.name))
    wait_until(lambda: not imap_client.folder.exists(child_folder.imap_path))


def test_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Adding an item to a collection in the akonadi server, the change is replayed on the server
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    # Append the item to Akonadi
    AkonadiEmailFactory.create(folder=folder.name)

    # List items from Akonadi, there should be 3 now.
    collection = imap_resource.resolve_collection(folder.name)
    items = akonadi_client.list_items(collection.id())
    new_count = len(folder.messages) + 1
    assert len(items) == len(folder.messages) + 1

    wait_until(lambda: message_added(imap_client, folder.name, f"{new_count}"))

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_delete_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the akonadi server, the change is replayed on the server
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    collection = imap_resource.resolve_collection(folder.name)
    items = akonadi_client.list_items(collection.id())
    assert len(items) == len(folder.messages)
    item = items[0]

    akonadi_client.delete_item(item.id())

    wait_until(lambda: message_deleted(imap_client, item, folder.name))

    items = akonadi_client.list_items(collection.id())
    assert len(items) == len(folder.messages) - 1
    assert item.id() not in [i.id() for i in items]

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_offline_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Adding an item to a collection in the offline akonadi server, nothing happens
    When the resource is set online, the change is replayed on the server
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_resource.set_online(False)

    # Append the item to Akonadi
    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        AkonadiEmailFactory.create(folder=folder.name)

    new_count = len(folder.messages) + 1
    collection = imap_resource.resolve_collection(folder.name)
    items = akonadi_client.list_items(collection.id())
    assert len(items) == new_count

    # No messages should have been added to imap server at this point
    imap_client.folder.set(folder.name)
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == len(folder.messages)

    imap_resource.set_online(True)

    wait_until(lambda: message_added(imap_client, folder.name, f"{new_count}"))

    imap_client.folder.set(folder.name)
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == new_count

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_offline_delete_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the offline akonadi server, nothing happens
    When the resource is set online, the change is replayed on the server
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    collection = imap_resource.resolve_collection(folder.name)
    items = akonadi_client.list_items(collection.id())
    assert len(items) == len(folder.messages)
    item = items[0]

    # Issuing set_online(False) while the IMAP resource is not idle might lead to crashes
    imap_resource.wait_resource_is_idle()
    imap_resource.set_online(False)

    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        akonadi_client.delete_item(item.id())

    new_count = len(folder.messages) - 1
    items = akonadi_client.list_items(collection.id())
    assert len(items) == new_count
    assert item.id() not in [i.id() for i in items]

    # No messages should have been deleted on imap server at this point
    imap_client.folder.set(folder.name)
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == len(folder.messages)

    imap_resource.set_online(True)

    wait_until(lambda: message_deleted(imap_client, item, folder.name))

    imap_client.folder.set(folder.name)
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == new_count

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_move_message_on_resource_is_synced(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Moving an item from one collection to another in the akonadi server, the change is replayed on the server
    """
    folder1 = ImapFolderFactory.create()
    folder2 = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder1.name, imap_resource, imap_client)
    assert_collection_equal_mailbox(folder2.name, imap_resource, imap_client)

    source = imap_resource.resolve_collection(folder1.name)
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == len(folder1.messages)

    destination = imap_resource.resolve_collection(folder2.name)
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == len(folder2.messages)

    item = items_source[0]
    akonadi_client.move_item(item.id(), destination.id())

    uid2 = len(folder2.messages) + 1
    wait_until(lambda: message_deleted(imap_client, item, folder1.name))
    wait_until(lambda: message_added(imap_client, folder2.name, f"{uid2}"))

    assert_collection_equal_mailbox(folder1.name, imap_resource, imap_client)
    assert_collection_equal_mailbox(folder2.name, imap_resource, imap_client)


@pytest.mark.xfail(
    reason="Akonadi bug ? An append command is sent to the server, and cyrus rejects it because of wrong flags",
)
def test_copy_message_on_server_is_synced(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Copying an item from one collection to another in the akonadi server, the change is replayed on the server
    """
    folder1 = ImapFolderFactory.create()
    folder2 = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder1.name, imap_resource, imap_client)
    assert_collection_equal_mailbox(folder2.name, imap_resource, imap_client)

    source = imap_resource.resolve_collection(folder1.name)
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == len(folder1.messages)

    destination = imap_resource.resolve_collection(folder2.name)
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == len(folder2.messages)

    item = items_source[0]
    akonadi_client.copy_item(item.id(), destination.id())

    uid_1, uid_2 = len(folder1.messages), len(folder2.messages) + 1
    wait_until(lambda: message_added(imap_client, folder1.name, f"{uid_1}"))
    wait_until(lambda: message_added(imap_client, folder2.name, f"{uid_2}"))

    assert_collection_equal_mailbox(folder1.name, imap_resource, imap_client)
    assert_collection_equal_mailbox(folder2.name, imap_resource, imap_client)


@pytest.mark.xfail(
    reason="Akonadi bug ? Flag disappear from akonadi server, maybe sync issues with imap server ?",
)
def test_akonadi_sync_add_flag(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    When changing flags of an item in the akonadi server, the change is replayed on the server
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()
    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    imap_client.folder.set(folder.name)
    items = imap_resource.list_items(folder.name)
    item = items[0]

    flags = ["\\Answered", "\\Flagged", "\\Draft", "\\Seen"]
    for flag in flags:
        imap_resource.add_flag(item.id(), flag)

        imap_resource.sync_collection(folder.name)
        wait_until(lambda: has_flag(imap_client, item, folder.name, flag))  # noqa: B023
        assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)

    for flag in flags:
        imap_resource.clear_flag(item.id(), flag)

        imap_resource.sync_collection(folder.name)
        wait_until(lambda: not has_flag(imap_client, item, folder.name, flag))  # noqa: B023

        assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)


def test_offline_rename_collection(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
) -> None:
    """
    Renaming a collection in the akonadi server, nothing happens, when the resource is set online, the change is replayed on the server.
    """
    folder = ImapFolderFactory.create()
    imap_resource.synchronize()

    assert_collection_equal_mailbox(folder.name, imap_resource, imap_client)
    initial_collections = imap_resource.list_collections()
    initial_items = imap_resource.list_items(folder.name)

    old_name, new_name = folder.name, fake.word()
    assert old_name in [c.name() for c in initial_collections]
    assert new_name not in [c.name() for c in initial_collections]

    imap_resource.set_online(False)

    # If the rename request arrives to quickly after the sync and list
    # somehow the rename never reaches the resource... there is a bug
    # somewhere in the chain
    time.sleep(0.1)
    imap_resource.rename_collection(old_name, new_name)

    updated_collections = imap_resource.list_collections()
    updated_items = imap_resource.list_items(new_name)

    assert new_name in [c.name() for c in updated_collections]
    assert old_name not in [c.name() for c in updated_collections]

    # Check that nothing changed on the imap server side
    wait_until(
        lambda: imap_client.folder.exists(old_name) and (not imap_client.folder.exists(new_name))
    )

    imap_resource.set_online(True)

    assert new_name in [c.name() for c in updated_collections]
    assert old_name not in [c.name() for c in updated_collections]

    # Check in imap server that the new collection exists and the old one is deleted
    wait_until(lambda: not imap_client.folder.exists(old_name))
    assert_collection_equal_mailbox(new_name, imap_resource, imap_client)

    # Check that the renamed collection has the same items as the original one
    assert len(initial_items) == len(updated_items)
    initial_items.sort(key=lambda item: item.id())
    updated_items.sort(key=lambda item: item.id())
    for initial_item, updated_item in zip(initial_items, updated_items, strict=False):
        assert_akonadi_items_are_equal(initial_item, updated_item)
