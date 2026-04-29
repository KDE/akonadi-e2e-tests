# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import pytest
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Principal
from caldav.elements import ical

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.test_utils import assert_akonadi_items_are_equal
from src.akonadi.utils import AkonadiUtils
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import (
    AkonadiCalendarFactory,
    AkonadiEventFactory,
    DavCalendarFactory,
    GenericCalendar,
    fake,
)
from src.test import wait_until


@pytest.mark.xfail(
    reason="The test is failing because collectionAdded is not implemented in dav resource"
)
def test_akonadi_sync_add_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Adding a collection in the akonadi server, the change is replayed on the server
    """
    calendar = AkonadiCalendarFactory.create()
    groupware_resource.synchronize()

    wait_until(
        lambda: calendar.name in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_sync_remove_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Removing a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    wait_until(
        lambda: calendar.name in [c.displayName() for c in groupware_resource.list_collections()]
    )

    collection = groupware_resource.collection_from_display_name(calendar.name)
    job = Akonadi.CollectionDeleteJob(collection)
    AkonadiUtils.wait_for_job(job)
    wait_until(
        lambda: calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.xfail(
    reason="Akonadi bug? Akonadi doesnt seem to sync calendar attributes https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/91"
)
def test_adkonadi_sync_change_color_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Changing the color of a collection in the akonadi server, the change is replayed on the server
    """
    calendar: GenericCalendar = DavCalendarFactory.create()
    new_color = fake.hex_rgba()
    groupware_resource.synchronize()
    assert calendar.name in [c.displayName() for c in groupware_resource.list_collections()]

    collection = groupware_resource.collection_from_display_name(calendar.name)
    groupware_resource.set_collection_color(collection.name(), new_color)

    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert groupware_resource.get_collection_color(collection.name()) == new_color

    groupware_resource.synchronize()
    wait_until(
        lambda: (
            dav_principal.calendar(calendar.name).get_property(ical.CalendarColor()) == new_color
        )
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_sync_add_item(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    """
    Adding an item to a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    AkonadiEventFactory.create(calendar=calendar.name)
    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) + 1
    groupware_resource.synchronize()

    wait_until(
        lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) + 1
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_sync_remove_item(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.id())
    item = items[0]

    akonadi_client.delete_item(item.id())

    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) - 1

    groupware_resource.synchronize()
    wait_until(
        lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) - 1
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.xfail(
    reason="The test fails on RADICALE, the collection is deleted when calling the delete job then recreated by the resource when going back online (as an empty collection)."
    "Note that if the test calls synchronize just after going back online, the resource will call a second delete collection job"
)
def test_offline_akonadi_remove_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Removing a collection from the akonadi server, nothing happens, when the resource is set online, the change is replayed on the server
    """
    calendar_to_delete = DavCalendarFactory.create()
    unchanged_calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)
    initial_calendars = dav_principal.get_calendars()
    assert len(initial_calendars) == len(
        groupware_resource.list_collections(sync_collections_only=True)
    )
    collection_to_delete = groupware_resource.collection_from_display_name(calendar_to_delete.name)

    groupware_resource.set_online(False)
    job = Akonadi.CollectionDeleteJob(collection_to_delete)
    AkonadiUtils.wait_for_job(job)

    # assert nothing happens

    # the calendar is still on server side but not anymore on akonadi side
    unsynced_calendars = dav_principal.get_calendars()
    assert len(unsynced_calendars) - 1 == len(
        groupware_resource.list_collections(sync_collections_only=True)
    )

    initial_calendars_display_name = [c.get_display_name() for c in unsynced_calendars]
    assert calendar_to_delete.name in initial_calendars_display_name
    assert unchanged_calendar.name in initial_calendars_display_name

    groupware_resource.set_online(True)

    # assert synchronization is done
    current_calendars = dav_principal.get_calendars()
    current_calendars_display_name = [c.get_display_name() for c in current_calendars]
    # check that the calendar has been removed on server side
    assert len(current_calendars) == len(initial_calendars) - 1
    # now collections and calendars should be the same
    assert len(current_calendars) == len(
        groupware_resource.list_collections(sync_collections_only=True)
    )
    assert calendar_to_delete.name not in current_calendars_display_name
    assert unchanged_calendar.name in current_calendars_display_name

    # assert all events are still there
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.xfail(
    reason="Akonadi bug? Changing the displayname attribute isn't synced https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/91"
)
def test_akonadi_sync_rename_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Renaming a collection in the akonadi server, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    old_name, new_name = calendar.name, f"{calendar.name}{fake.word()}"

    initial_collection = groupware_resource.collection_from_display_name(old_name)
    initial_items = groupware_resource.list_items(initial_collection.id())

    groupware_resource.update_displayname_collection(initial_collection.name(), new_name)

    # Check the rename occurred locally and on remote
    updated_collection_names = [c.displayName() for c in groupware_resource.list_collections()]
    assert old_name not in updated_collection_names
    assert new_name in updated_collection_names
    wait_until(lambda: new_name in [c.get_display_name() for c in dav_principal.get_calendars()])

    # Check the items locally are the same
    updated_collection = groupware_resource.collection_from_display_name(new_name)
    updated_items = groupware_resource.list_items(updated_collection.id())
    assert len(initial_items) == len(updated_items)
    assert_akonadi_items_are_equal(initial_items, updated_items)

    # Check the items are matching between resource and server
    assert_all_collections_are_equals(dav_principal, groupware_resource)
