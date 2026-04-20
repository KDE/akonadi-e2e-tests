# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from logging import getLogger

import pytest
from AkonadiCore import Akonadi
from imap_tools import BaseMailBox

from akonadi.utils import AkonadiUtils
from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.imap.email_utils import create_message
from src.imap.test_utils import (
    assert_collection_equal_mailbox,
    has_flag,
    message_added,
    message_deleted,
)
from test import wait_until

log = getLogger(__name__)


def test_akonadi_sync_add_collection(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    Adding a collection in the akonadi server, the change is replayed on the server
    """
    root_collection = imap_resource.get_root_collection()
    mime_types = ["inode/directory", "message/rfc822"]

    assert not imap_client.folder.exists("TestTopLevel")
    assert not imap_client.folder.list("", "TestTopLevel*TestChild")

    # Create toplevel collection
    toplevel_collection = Akonadi.Collection()
    toplevel_collection.setName("TestTopLevel")
    toplevel_collection.setContentMimeTypes(mime_types)
    toplevel_collection.setParentCollection(root_collection)
    job = Akonadi.CollectionCreateJob(toplevel_collection)

    AkonadiUtils.wait_for_job(job)
    wait_until(lambda: imap_client.folder.exists("TestTopLevel"))

    # Creat child collection
    toplevel_collection = imap_resource.resolve_collection("TestTopLevel")
    child_collection = Akonadi.Collection()
    child_collection.setName("TestChild")
    child_collection.setContentMimeTypes(mime_types)
    child_collection.setParentCollection(toplevel_collection)
    job = Akonadi.CollectionCreateJob(child_collection)

    AkonadiUtils.wait_for_job(job)
    wait_until(lambda: len(imap_client.folder.list("", "TestTopLevel*TestChild")) > 0)


def test_akonadi_sync_delete_collection(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Deleting a collection in the akonadi server, the change is replayed on the server
    """
    mime_types = ["inode/directory", "message/rfc822"]
    toplevel_collection = imap_resource.resolve_collection("Test")

    # Creat child collection
    child_collection = Akonadi.Collection()
    child_collection.setName("TestChild")
    child_collection.setContentMimeTypes(mime_types)
    child_collection.setParentCollection(toplevel_collection)
    job = Akonadi.CollectionCreateJob(child_collection)

    AkonadiUtils.wait_for_job(job)
    wait_until(lambda: len(imap_client.folder.list("", "Test*TestChild")) > 0)

    # Delete parent collection
    job = Akonadi.CollectionDeleteJob(toplevel_collection)
    AkonadiUtils.wait_for_job(job)

    wait_until(lambda: not imap_client.folder.exists("Test"))
    wait_until(lambda: len(imap_client.folder.list("", "Test*TestChild")) == 0)


def test_rename_collection(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
) -> None:
    """
    Test renaming a collection in akonadi side when online and verifying the change in both Akonadi and IMAP server.
    """
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    initial_collections = imap_resource.list_collections()

    assert "Test" in [c.name() for c in initial_collections]
    assert "Test3" not in [c.name() for c in initial_collections]

    imap_resource.rename_collection("Test", "Test3")

    updated_collections = imap_resource.list_collections()

    assert "Test3" in [c.name() for c in updated_collections]
    assert "Test" not in [c.name() for c in updated_collections]

    # Check in imap server that the new collection exists and the old one is deleted
    wait_until(lambda: not imap_client.folder.exists("Test"))
    assert_collection_equal_mailbox("Test3", imap_resource, imap_client)

    # Check that the renamed collection has the same items as the original one
    initial_collection = [
        collection for collection in initial_collections if collection.name() == "Test"
    ]
    updated_collection = [
        collection for collection in updated_collections if collection.name() == "Test3"
    ]
    assert sorted(initial_collection) == sorted(updated_collection)


def test_akonadi_offline_delete_collection(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Removing a collection from the akonadi server, nothing happens, when the resource is set online, the change is replayed on the server
    """
    mime_types = ["inode/directory", "message/rfc822"]
    toplevel_collection = imap_resource.resolve_collection("Test")

    # Create child collection
    child_collection = Akonadi.Collection()
    child_collection.setName("TestChild")
    child_collection.setContentMimeTypes(mime_types)
    child_collection.setParentCollection(toplevel_collection)
    job = Akonadi.CollectionCreateJob(child_collection)

    AkonadiUtils.wait_for_job(job)
    assert "TestChild" in list(map(lambda c: c.name(), imap_resource.list_collections()))
    wait_until(lambda: len(imap_client.folder.list("", "*TestChild")) > 0)

    imap_resource.set_online(False)

    # Delete parent collection
    job = Akonadi.CollectionDeleteJob(toplevel_collection)
    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        AkonadiUtils.wait_for_job(job)

    resource_collections = imap_resource.list_collections()

    assert "Test" not in list(map(lambda c: c.name(), resource_collections))
    assert "TestChild" not in list(map(lambda c: c.name(), resource_collections))
    assert imap_client.folder.exists("Test")
    assert len(imap_client.folder.list("", "*TestChild")) > 0

    imap_resource.set_online(True)

    resource_collections = imap_resource.list_collections()

    assert "Test" not in list(map(lambda c: c.name(), resource_collections))
    assert "TestChild" not in list(map(lambda c: c.name(), resource_collections))
    wait_until(lambda: not imap_client.folder.exists("Test"))
    wait_until(lambda: len(imap_client.folder.list("", "*TestChild")) == 0)


def test_akonadi_offline_rename_collection(
    imap_resource: ImapResource, imap_client: BaseMailBox
) -> None:
    """
    Renaming a collection in the server, nothing happens, when the resource is set online, the collection is also
    renamed in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    old_name = "Test"
    new_name = "Test0"
    initial_collections = imap_resource.list_collections()

    assert old_name in (collection.name() for collection in initial_collections)
    assert new_name not in (collection.name() for collection in initial_collections)
    assert imap_client.folder.exists(old_name)
    assert not imap_client.folder.exists(new_name)

    imap_resource.set_online(False)
    imap_resource.rename_collection(old_name, new_name)

    updated_offline_collections = imap_resource.list_collections()

    assert old_name not in (collection.name() for collection in updated_offline_collections)
    assert new_name in (collection.name() for collection in updated_offline_collections)

    # Here we need to test that nothing happens in the server
    assert imap_client.folder.exists(old_name)
    assert not imap_client.folder.exists(new_name)

    imap_resource.set_online(True)

    assert imap_client.folder.exists(new_name)
    assert not imap_client.folder.exists(old_name)
    assert_collection_equal_mailbox(new_name, imap_resource, imap_client)


def test_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Adding an item to a collection in the akonadi server, the change is replayed on the server
    """
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    collection = imap_resource.resolve_collection("Test")

    # Append the item to Akonadi
    akonadi_client.add_item(
        collection.id(),
        create_message(subject="test_append_message").as_bytes(),
        "message/rfc822",
    )

    # List items from Akonadi, there should be 3 now.
    items = akonadi_client.list_items(collection.id())
    assert len(items) == 3

    wait_until(lambda: message_added(imap_client, "Test", "3"))

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_delete_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the akonadi server, the change is replayed on the server
    """
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    collection = imap_resource.resolve_collection("Test")
    items = akonadi_client.list_items(collection.id())
    assert len(items) == 2
    item = items[0]

    akonadi_client.delete_item(item.id())

    wait_until(lambda: message_deleted(imap_client, item, "Test"), timeout=10.0)

    items = akonadi_client.list_items(collection.id())
    assert len(items) == 1
    assert item.id() not in [i.id() for i in items]

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_offline_append_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Adding an item to a collection in the offline akonadi server, nothing happens
    When the resource is set online, the change is replayed on the server
    """
    assert_collection_equal_mailbox("TestEmpty", imap_resource, imap_client)
    collection = imap_resource.resolve_collection("TestEmpty")

    imap_resource.set_online(False)

    # Append the item to Akonadi
    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        akonadi_client.add_item(
            collection.id(),
            create_message(subject="test_append_message").as_bytes(),
            "message/rfc822",
        )

    items = akonadi_client.list_items(collection.id())
    assert len(items) == 1

    # No messages should have been added to imap server at this point
    imap_client.folder.set("TestEmpty")
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == 0

    imap_resource.set_online(True)

    wait_until(lambda: message_added(imap_client, "TestEmpty", "1"))

    imap_client.folder.set("TestEmpty")
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == 1

    assert_collection_equal_mailbox("TestEmpty", imap_resource, imap_client)


def test_offline_delete_message(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the offline akonadi server, nothing happens
    When the resource is set online, the change is replayed on the server
    """
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    collection = imap_resource.resolve_collection("Test")

    items = akonadi_client.list_items(collection.id())
    assert len(items) == 2
    item = items[0]

    imap_resource.set_online(False)

    # This context manager is needed as we need to wait for the ChangeReplay
    # to be queued before set_online(True) is called, otherwise the ChangeReplay
    # might be lost, this is sign of a bug in Akonadi
    with AkonadiUtils.wait_for_queued_change_replay(imap_resource.instance):
        akonadi_client.delete_item(item.id())

    items = akonadi_client.list_items(collection.id())
    assert len(items) == 1
    assert item.id() not in [i.id() for i in items]

    # No messages should have been deleted on imap server at this point
    imap_client.folder.set("Test")
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == 2

    imap_resource.set_online(True)

    wait_until(lambda: message_deleted(imap_client, item, "Test"), timeout=10.0)

    imap_client.folder.set("Test")
    messages = list(imap_client.fetch(mark_seen=False))
    assert len(messages) == 1

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)


def test_move_message_on_resource_is_synced(
    imap_resource: ImapResource,
    imap_client: BaseMailBox,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Moving an item from one collection to another in the akonadi server, the change is replayed on the server
    """
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert_collection_equal_mailbox("Test2", imap_resource, imap_client)

    source = imap_resource.resolve_collection("Test")
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == 2

    destination = imap_resource.resolve_collection("Test2")
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == 2

    item = items_source[0]
    akonadi_client.move_item(item.id(), destination.id())

    wait_until(lambda: message_deleted(imap_client, item, "Test"))
    wait_until(lambda: message_added(imap_client, "Test2", "3"))

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert_collection_equal_mailbox("Test2", imap_resource, imap_client)


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
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert_collection_equal_mailbox("Test2", imap_resource, imap_client)

    source = imap_resource.resolve_collection("Test")
    items_source = akonadi_client.list_items(source.id())
    assert len(items_source) == 2

    destination = imap_resource.resolve_collection("Test2")
    items_destination = akonadi_client.list_items(destination.id())
    assert len(items_destination) == 2

    item = items_source[0]
    akonadi_client.copy_item(item.id(), destination.id())

    wait_until(lambda: message_added(imap_client, "Test", "2"))
    wait_until(lambda: message_added(imap_client, "Test2", "3"))

    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
    assert_collection_equal_mailbox("Test2", imap_resource, imap_client)


@pytest.mark.xfail(
    reason="Akonadi bug ? Flag disappear from akonadi server, maybe sync issues with imap server ?",
)
def test_akonadi_sync_add_flag(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    """
    When changing flags of an item in the akonadi server, the change is replayed on the server
    """
    imap_client.folder.set("Test")
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    items = imap_resource.list_items("Test")
    item = items[0]

    flags = ["\\Answered", "\\Flagged", "\\Draft", "\\Seen"]
    for flag in flags:
        imap_resource.add_flag(item.id(), flag)

        imap_resource.sync_collection("Test")
        wait_until(lambda: has_flag(imap_client, item, "Test", flag))  # noqa: B023
        assert_collection_equal_mailbox("Test", imap_resource, imap_client)

    for flag in flags:
        imap_resource.clear_flag(item.id(), flag)

        imap_resource.sync_collection("Test")
        wait_until(lambda: not has_flag(imap_client, item, "Test", flag))  # noqa: B023

        assert_collection_equal_mailbox("Test", imap_resource, imap_client)
