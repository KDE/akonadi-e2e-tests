# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
from caldav.collection import Principal
from caldav.elements import dav
from caldav.lib.error import NotFoundError

from src.akonadi.dav_resource import DAVResource
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import DavCalendarFactory, DavEventFactory, fake


@pytest.mark.xfail(
    reason="RADICALE: Collection is recreated with an item. https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/102"
)
def test_offline_remove_collection_and_add_event(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Removing a collection from the akonadi server, adding an item to the collection on the server, nothing happens
    When the resource is set online, the change is replayed on the server and the collection is removed (including the newly added item)
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)
    initial_collections = groupware_resource.list_collections()
    collection = groupware_resource.collection_from_display_name(calendar.name)

    groupware_resource.set_online(False)

    groupware_resource.delete_collection(collection.name())
    DavEventFactory.create(calendar=calendar.name)

    # Nothing happens
    assert dav_principal.calendar(calendar.name)
    assert len(groupware_resource.list_collections()) == len(initial_collections) - 1
    assert calendar.name not in [c.displayName() for c in groupware_resource.list_collections()]

    groupware_resource.set_online(True)

    with pytest.raises(NotFoundError):
        dav_principal.calendar(calendar.name)
    assert len(groupware_resource.list_collections()) == len(initial_collections) - 1
    assert calendar.name not in [c.displayName() for c in groupware_resource.list_collections()]
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.xfail(
    reason="Akonadi BUG? The akonadi collection is not renamed. https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/105"
)
def test_offline_rename_collection_server_and_resource(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Renaming a collection in the akonadi server, renaming the same collection under another name on the server, nothing happens
    When the resource is set online, the collection in the akonadi server is renamed with the name given on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    initial_collections = groupware_resource.list_collections()
    collection = groupware_resource.collection_from_display_name(calendar.name)
    resource_new_name = f"{calendar.name}{fake.word()}1"
    server_new_name = f"{calendar.name}{fake.word()}2"

    groupware_resource.set_online(False)

    groupware_resource.update_collection_displayname(collection.name(), resource_new_name)
    dav_principal.calendar(calendar.name).set_properties([dav.DisplayName(server_new_name)])

    # Nothing changed
    assert groupware_resource.collection_from_display_name(resource_new_name)
    assert dav_principal.calendar(server_new_name)

    groupware_resource.set_online(True)

    assert len(groupware_resource.list_collections()) == len(initial_collections)
    assert groupware_resource.collection_from_display_name(server_new_name)
    assert dav_principal.calendar(server_new_name)
    assert_all_collections_are_equals(dav_principal, groupware_resource)
