# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from caldav.collection import Principal
from imap_tools import BaseMailBox

from src.akonadi.dav_resource import DAVResource
from src.akonadi.imap_resource import ImapResource
from src.factories.email_factory import (
    AkonadiEmailFactory,
    AkonadiFolderFactory,
    ImapEmailFactory,
    ImapFolderFactory,
)
from src.factories.event_factory import AkonadiEventFactory, DavCalendarFactory, DavEventFactory


def test_imap_factory(imap_resource: ImapResource, imap_client: BaseMailBox):  # noqa: ARG001
    ImapFolderFactory.create(name="Test", nb_items=5)
    ImapEmailFactory.create_batch(10, folder="INBOX")

    assert len(imap_client.folder.list()) == 2
    imap_client.folder.set("INBOX")
    assert len(list(imap_client.fetch(mark_seen=False))) == 10
    imap_client.folder.set("Test")
    assert len(list(imap_client.fetch(mark_seen=False))) == 5


def test_imap_factory_sub_folder(imap_resource: ImapResource, imap_client: BaseMailBox):  # noqa: ARG001
    parent = ImapFolderFactory.create(name="Parent", nb_items=3)
    child1 = ImapFolderFactory.create(name="Child1", parent=parent, nb_items=4)
    child2 = ImapFolderFactory.create(name="Child2", parent=parent, nb_items=5)
    child11 = ImapFolderFactory.create(name="Child11", parent=parent, nb_items=0)
    ImapEmailFactory.create_batch(2, folder=child11)

    assert parent.parent is None
    assert child1.parent.name == child2.parent.name == parent.name

    assert len(imap_client.folder.list()) == 1 + 4
    imap_client.folder.set(parent.imap_path)
    assert len(list(imap_client.fetch(mark_seen=False))) == 3
    imap_client.folder.set(child1.imap_path)
    assert len(list(imap_client.fetch(mark_seen=False))) == 4
    imap_client.folder.set(child2.imap_path)
    assert len(list(imap_client.fetch(mark_seen=False))) == 5
    imap_client.folder.set(child11.imap_path)
    assert len(list(imap_client.fetch(mark_seen=False))) == 2


def test_imap_resource_factory(imap_resource: ImapResource, imap_client: BaseMailBox):  # noqa: ARG001
    AkonadiFolderFactory.create(name="Test", nb_items=5)
    AkonadiEmailFactory.create_batch(10, folder="INBOX")

    imap_resource.wait_resource_is_idle()
    assert len(imap_resource.list_collections()) == 3  # INBOX, Test and IMAP Account
    assert len(imap_resource.list_items("INBOX")) == 10
    assert len(imap_resource.list_items("Test")) == 5


def test_imap_resource_factory_sub_folder(imap_resource: ImapResource, imap_client: BaseMailBox):  # noqa: ARG001
    parent = AkonadiFolderFactory.create(name="Parent", nb_items=3)
    child1 = AkonadiFolderFactory.create(name="Child1", parent=parent, nb_items=4)
    child2 = AkonadiFolderFactory.create(name="Child2", parent=parent, nb_items=5)
    child11 = AkonadiFolderFactory.create(name="Child1", parent=child1, nb_items=0)
    AkonadiEmailFactory.create_batch(2, folder=child11)

    assert parent.parent is None
    assert child1.parent.name == child2.parent.name == parent.name

    imap_resource.wait_resource_is_idle()

    collection_parent = parent.get_collection()
    collection_child1 = child1.get_collection()
    collection_child2 = child2.get_collection()
    collection_child11 = child11.get_collection()

    assert len(imap_resource.list_collections()) == 2 + 4
    assert len(imap_resource.list_items(collection_parent.id())) == 3
    assert len(imap_resource.list_items(collection_child1.id())) == 4
    assert len(imap_resource.list_items(collection_child2.id())) == 5
    assert len(imap_resource.list_items(collection_child11.id())) == 2
    assert collection_child1.parentCollection().id() == collection_parent.id()
    assert collection_child2.parentCollection().id() == collection_parent.id()
    assert collection_child11.parentCollection().id() == collection_child1.id()


def test_dav_factory(groupware_resource: DAVResource, dav_principal: Principal):  # noqa: ARG001
    DavCalendarFactory.create(name="Test", nb_items=5)
    DavEventFactory.create_batch(10, calendar="Default Calendar")

    assert len(dav_principal.calendars()) == 2
    assert len(dav_principal.calendar("Test").get_events()) == 5
    assert len(dav_principal.calendar("Default Calendar").get_events()) == 10


def test_dav_resource_factory(groupware_resource: DAVResource, dav_principal: Principal):  # noqa: ARG001
    AkonadiEventFactory.create_batch(10, calendar="Default Calendar")
    groupware_resource.wait_resource_is_idle()
    assert (
        len(groupware_resource.list_collections()) == 2
    )  # Default Calendar and resource collection
    collection = groupware_resource.collection_from_display_name("Default Calendar")
    assert len(groupware_resource.list_items(collection.id())) == 10
