# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import pytest
from caldav.collection import Principal
from caldav.elements import ical

from src.akonadi.dav_resource import DAVResource
from src.akonadi.test_utils import assert_akonadi_item_are_equal, assert_item_unsync
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.event_factory import DavCalendarFactory, DavEventFactory, GenericCalendar, fake


def test_multiple_sync_without_change(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    When already synced, another sync doesn't lead to any change (other than timestamps book keeping)
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    collection = groupware_resource.collection_from_display_name(calendar.name)
    initial_items = groupware_resource.list_items(collection.id())

    groupware_resource.synchronize()
    current_items = groupware_resource.list_items(collection.id())

    initial_items.sort(key=lambda i: i.id())
    current_items.sort(key=lambda i: i.id())
    for initial_item, current_item in zip(initial_items, current_items, strict=True):
        assert_item_unsync(initial_item, current_item)
        assert_akonadi_item_are_equal(initial_item, current_item)


def test_offline_change_color(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    """
    Changing the color of a collection in the server, nothing happens, when the resource is set online, when the resource is set online, the change is replayed on the resource
    """
    calendar: GenericCalendar = DavCalendarFactory.create()
    new_color = fake.qcolor()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)
    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert dav_principal.calendar(calendar.name).get_property(ical.CalendarColor()) != new_color
    assert groupware_resource.get_collection_color(collection.name()) != new_color

    groupware_resource.set_online(False)
    dav_principal.calendar(calendar.name).set_properties(ical.CalendarColor(new_color.name()))

    # assert server is updated but not resource
    assert dav_principal.calendar(calendar.name).get_property(ical.CalendarColor()) == new_color
    assert groupware_resource.get_collection_color(collection.name()) != new_color

    groupware_resource.set_online(True)

    # assert color is synchronized
    assert dav_principal.calendar(calendar.name).get_property(ical.CalendarColor()) == new_color
    assert groupware_resource.get_collection_color(collection.name()) == new_color
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_offline_add_items(dav_principal: Principal, groupware_resource: DAVResource):
    """
    Adding an item to a collection on the server, nothing happens, when the resource is set online, the added item is replicated in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    initial_events_from_custom_calendar = dav_principal.calendar(calendar.name).get_events()
    initial_events_from_default_calendar = dav_principal.calendar("Default Calendar").get_events()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    groupware_resource.set_online(False)

    event_created_default_calendar = DavEventFactory.create_batch(10, calendar="Default Calendar")
    event_created_custom_calendar = DavEventFactory.create_batch(5, calendar=calendar.name)

    # assert nothing happened on akonadi side
    unsynced_custom_collection = groupware_resource.collection_from_display_name(calendar.name)
    unsynced_custom_items = groupware_resource.list_items(unsynced_custom_collection.id())
    assert len(unsynced_custom_items) == len(initial_events_from_custom_calendar)

    unsynced_default_collection = groupware_resource.collection_from_display_name(
        "Default Calendar"
    )
    unsynced_default_items = groupware_resource.list_items(unsynced_default_collection.id())
    assert len(unsynced_default_items) == len(initial_events_from_default_calendar)

    groupware_resource.set_online(True)

    # assert synchronization is done
    synced_custom_collection = groupware_resource.collection_from_display_name(calendar.name)
    synced_custom_items = groupware_resource.list_items(synced_custom_collection.id())
    assert len(synced_custom_items) == len(initial_events_from_custom_calendar) + len(
        event_created_custom_calendar
    )

    synced_default_collection = groupware_resource.collection_from_display_name("Default Calendar")
    synced_default_items = groupware_resource.list_items(synced_default_collection.id())
    assert len(synced_default_items) == len(initial_events_from_default_calendar) + len(
        event_created_default_calendar
    )
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_offline_remove_items(dav_principal: Principal, groupware_resource: DAVResource):
    """
    Removing an item from a collection on the server, nothing happens, when the resource is set online, the removed item is also removed in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    calendar = DavCalendarFactory.create(nb_items=5)
    DavEventFactory.create_batch(10, calendar="Default Calendar")
    groupware_resource.synchronize()
    initial_events_from_custom_calendar = dav_principal.calendar(calendar.name).get_events()
    initial_events_from_default_calendar = dav_principal.calendar("Default Calendar").get_events()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    events_to_remove_default_calendar = initial_events_from_default_calendar[:3]
    events_to_remove_custom_calendar = initial_events_from_custom_calendar[:2]

    groupware_resource.set_online(False)

    for event in events_to_remove_default_calendar:
        event.delete()
    for event in events_to_remove_custom_calendar:
        event.delete()

    # assert nothing happened on akonadi side
    unsynced_custom_collection = groupware_resource.collection_from_display_name(calendar.name)
    unsynced_custom_items = groupware_resource.list_items(unsynced_custom_collection.id())
    assert len(unsynced_custom_items) == len(initial_events_from_custom_calendar)

    unsynced_default_collection = groupware_resource.collection_from_display_name(
        "Default Calendar"
    )
    unsynced_default_items = groupware_resource.list_items(unsynced_default_collection.id())
    assert len(unsynced_default_items) == len(initial_events_from_default_calendar)

    groupware_resource.set_online(True)

    # assert synchronization is done
    synced_custom_collection = groupware_resource.collection_from_display_name(calendar.name)
    synced_custom_items = groupware_resource.list_items(synced_custom_collection.id())
    assert len(synced_custom_items) == len(initial_events_from_custom_calendar) - len(
        events_to_remove_custom_calendar
    )

    synced_default_collection = groupware_resource.collection_from_display_name("Default Calendar")
    synced_default_items = groupware_resource.list_items(synced_default_collection.id())
    assert len(synced_default_items) == len(initial_events_from_default_calendar) - len(
        events_to_remove_default_calendar
    )
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.xfail(
    reason="Akonadi bug? The partial sync does not seem to replicate the new item in the akonadi server\n"
    "Issue: https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/103",
    strict=True,
)
def test_partial_sync_on_item_add(dav_principal: Principal, groupware_resource: DAVResource):
    """
    Adding an item to a collection on the server, after requesting a partial sync, the added item is replicated in the
    akonadi server, no other change occurred (other than timestamps book keeping)
    """
    created_calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    edited_collection_name = created_calendar.name
    edited_collection = groupware_resource.collection_from_display_name(edited_collection_name)
    init_nb_items = len(groupware_resource.list_items(edited_collection.id()))
    DavEventFactory.create(calendar=edited_collection_name)

    groupware_resource.sync_collection(edited_collection.remoteId())

    assert len(groupware_resource.list_items(edited_collection.id())) == init_nb_items + 1
    assert_all_collections_are_equals(dav_principal, groupware_resource)
