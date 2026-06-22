# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny LORIN <kenny.lorin@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Alan THOUVENIN <alan.thouvenin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from datetime import timedelta
from urllib.parse import unquote

import pytest
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Principal
from caldav.elements import dav, ical
from caldav.elements.ical import CalendarColor
from icalendar import Calendar, vRecur
from PySide6 import QtGui  # type: ignore

from src.akonadi.dav_resource import DAVResource
from src.akonadi.test_utils import (
    assert_akonadi_item_are_equal,
    assert_akonadi_items_are_equal,
    assert_item_unsync,
)
from src.dav.test_utils import (
    assert_all_collections_are_equals,
    assert_collection_equal_calendar,
    field_is_equal,
    normalize_vrecur,
    rrule_are_equal,
)
from src.factories.event_factory import DavCalendarFactory, DavEventFactory, GenericCalendar, fake
from src.test import wait_until


def test_add_collection_to_server_is_sync(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Adding a calendar to the DAV server gets replicated to the akonadi server
    """
    created_calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    matching_collection = groupware_resource.collection_from_display_name(created_calendar.name)

    assert_collection_equal_calendar(
        matching_collection.name(), dav_resource=groupware_resource, dav_principal=dav_principal
    )


def test_delete_collection_to_server_is_sync(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Removing a calendar from the DAV server gets deleted from the akonadi server
    """
    created_calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    matching_collection = groupware_resource.collection_from_display_name(created_calendar.name)

    assert_collection_equal_calendar(
        matching_collection.name(), dav_resource=groupware_resource, dav_principal=dav_principal
    )

    dav_principal.calendar(created_calendar.name).delete()
    groupware_resource.synchronize()

    with pytest.raises(pytest.fail.Exception):
        groupware_resource.collection_from_display_name(created_calendar.name)


def test_update_collection_name_on_server_is_sync(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Changing the display name of a calendar on the DAV server gets updated on the akonadi server
    """
    created_calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    new_display_name = created_calendar.name + fake.word()
    assert new_display_name not in (c.displayName() for c in groupware_resource.list_collections())

    calendar_to_update = dav_principal.calendar(created_calendar.name)
    calendar_to_update.set_properties([dav.DisplayName(new_display_name)])
    assert created_calendar.name not in (c.get_display_name() for c in dav_principal.calendars())
    assert new_display_name in (c.get_display_name() for c in dav_principal.calendars())
    groupware_resource.synchronize()

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_update_collection_color_on_server_is_sync(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Changing the color of a calendar on the DAV server gets updated on the akonadi server
    """
    new_color = fake.qcolor()
    new_color_on_server = new_color.name(QtGui.QColor.NameFormat.HexRgb)

    created_calendar = DavCalendarFactory.create()
    remote_calendar = dav_principal.calendar(created_calendar.name)
    assert remote_calendar.get_property(CalendarColor()) == created_calendar.color.name(
        QtGui.QColor.NameFormat.HexRgb
    )
    groupware_resource.synchronize()

    remote_calendar.set_properties([CalendarColor(new_color_on_server)])
    assert remote_calendar.get_property(CalendarColor()) == new_color_on_server
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(created_calendar.name)
    assert (
        groupware_resource.get_collection_attribute(
            collection, Akonadi.CollectionColorAttribute
        ).color()
        == new_color
    )


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


def test_offline_remove_collection_server_side(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Removing a collection from the server, nothing happens, when the resource is set online, the removed collection is
    also removed from the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    initial_count = len(groupware_resource.list_collections())
    calendar_name = DavCalendarFactory.create().name
    created_calendar = dav_principal.calendar(calendar_name)
    groupware_resource.synchronize()

    groupware_resource.set_online(False)
    created_calendar.delete()
    # The resource is offline so the removed calendar should still be there Akonadi side
    assert len(groupware_resource.list_collections()) == initial_count + 1

    groupware_resource.set_online(True)

    assert len(groupware_resource.list_collections()) == initial_count
    assert unquote(str(created_calendar.url)) not in (
        unquote(c.remoteId()) for c in groupware_resource.list_collections()
    )
    assert calendar_name not in (c.displayName() for c in groupware_resource.list_collections())


def test_offline_add_collection_server_side(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Adding a collection in the server, nothing happens, when the resource is set online, the added collection is
    replicated in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    initial_count = len(groupware_resource.list_collections())
    groupware_resource.set_online(False)
    calendar_name = DavCalendarFactory.create().name
    created_calendar = dav_principal.calendar(calendar_name)

    # The resource is offline so the new calendar should not appear Akonadi side
    assert len(groupware_resource.list_collections()) == initial_count

    groupware_resource.set_online(True)
    assert len(groupware_resource.list_collections()) == initial_count + 1
    assert unquote(str(created_calendar.url)) in (
        unquote(c.remoteId()) for c in groupware_resource.list_collections()
    )
    assert calendar_name in (c.displayName() for c in groupware_resource.list_collections())
    assert_all_collections_are_equals(dav_resource=groupware_resource, dav_principal=dav_principal)


def test_offline_rename_collection_server_side(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Renaming a collection in the server, nothing happens, when the resource is set online, the collection is also
    renamed in the akonadi server, no other change occurred (other than timestamps book keeping)
    """
    calendar_name = DavCalendarFactory.create().name
    created_calendar = dav_principal.calendar(calendar_name)
    groupware_resource.synchronize()

    groupware_resource.set_online(False)

    new_collection_name = calendar_name + fake.word()
    created_calendar.set_properties([dav.DisplayName(new_collection_name)])
    assert all(
        c.displayName() != new_collection_name for c in groupware_resource.list_collections()
    )

    groupware_resource.set_online(True)

    assert any(
        c.displayName() == new_collection_name for c in groupware_resource.list_collections()
    )
    assert_all_collections_are_equals(dav_resource=groupware_resource, dav_principal=dav_principal)


@pytest.mark.xfail(
    reason="The partial sync does not seem to replicate the delete item in the akonadi server "
    "Issue: https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/103",
    strict=True,
)
def test_partial_sync_on_item_deleted(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Removing an item from a collection on the server, after requesting a partial sync,
    the removed item is also removed in the akonadi server;
    no other change occurred (other than timestamps book keeping)
    """
    calendar_to_sync = DavCalendarFactory.create(nb_items=5)
    DavEventFactory.create_batch(10, calendar="Default Calendar")
    groupware_resource.synchronize()
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    collection_to_sync = groupware_resource.collection_from_display_name(calendar_to_sync.name)
    unsynced_collection = groupware_resource.collection_from_display_name("Default Calendar")
    initial_events_from_calendar_to_sync = dav_principal.calendar(
        calendar_to_sync.name
    ).get_events()
    initial_events_from_unsynced_calendar = dav_principal.calendar("Default Calendar").get_events()

    initial_items_from_collection_to_sync = groupware_resource.list_items(collection_to_sync.id())
    initial_items_from_unsynced_collection = groupware_resource.list_items(unsynced_collection.id())

    events_to_remove_from_unsynced_calendar = initial_events_from_unsynced_calendar[:3]
    events_to_remove_from_calendar_to_sync = initial_events_from_calendar_to_sync[:2]

    for event in events_to_remove_from_unsynced_calendar:
        event.delete()
    for event in events_to_remove_from_calendar_to_sync:
        event.delete()

    # requesting partial sync
    groupware_resource.sync_collection(collection_to_sync.remoteId())

    # wait items to be sync, synchronize is not enough
    wait_until(
        lambda: (
            len(groupware_resource.list_items(collection_to_sync.id()))
            == len(initial_events_from_calendar_to_sync)
            - len(events_to_remove_from_calendar_to_sync)
        )
    )

    updated_items_from_synced_collection = groupware_resource.list_items(collection_to_sync.id())
    updated_items_from_unsynced_collection = groupware_resource.list_items(unsynced_collection.id())

    # assert not deleted items are still there for sync collection
    for item in updated_items_from_synced_collection:
        [initial_item] = [
            initial_item
            for initial_item in initial_items_from_collection_to_sync
            if initial_item == item
        ]
        assert_item_unsync(initial_item, item)
        assert_akonadi_item_are_equal(initial_item, item)

    # unsynced collection has the same items as initial
    assert_akonadi_items_are_equal(
        initial_items_from_unsynced_collection, updated_items_from_unsynced_collection
    )


random_dtsart = fake.future_datetime()

changed_field_data = [
    pytest.param("DESCRIPTION", fake.paragraph(), fake.boolean(), id="description"),
    pytest.param("SUMMARY", fake.sentence(), fake.boolean(), id="summary"),
    pytest.param(
        "DTSTART", fake.future_datetime().strftime("%Y%m%dT%H%M%S"), fake.boolean(), id="dtstart"
    ),
    pytest.param(
        "DTEND",
        fake.date_time_between(
            start_date=random_dtsart, end_date=random_dtsart + timedelta(hours=8)
        ).strftime("%Y%m%dT%H%M%S"),
        True,
        id="dtend",
    ),
    pytest.param("DURATION", f"PT{fake.random_int(min=9, max=16)}H", False, id="duration"),
]


@pytest.mark.parametrize("field, new_value, use_dtend", changed_field_data)
def test_akonadi_partial_offline_change_item_contents(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    field: str,
    new_value: str,
    use_dtend: bool,
) -> None:
    """
    Changing the content of an item on the server (description, alarms, attachments… should all be tested), nothing happens
    When the resource is set online, the content is also changed on the corresponding item in the akonadi server
    No other change occurred (other than timestamps book keeping)
    """
    calendar = DavCalendarFactory.create(nb_items=0)
    event = DavEventFactory.create(calendar=calendar.name, use_dtend=use_dtend)
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) == 1
    item = items[0]

    wait_until(lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(items))
    event = dav_principal.calendar(calendar.name).event_by_url(item.remoteId())

    payload = bytes(item.payloadData()).decode()
    item_calendar = Calendar.from_ical(payload)
    [item_event] = item_calendar.walk("VEVENT")

    assert item_event[field] == event.icalendar_component[field]

    groupware_resource.set_online(False)

    event.icalendar_component[field] = new_value
    event.save()

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() != new_value
    assert field_is_equal(
        field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.set_online(True)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert field_is_equal(
        field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )
    assert updated_event[field].to_ical().decode() == new_value
    assert_all_collections_are_equals(dav_principal, groupware_resource)


rrules = [
    (False, dict(), fake.rrule()),
    (True, {"FREQ": "MONTHLY"}, {"FREQ": "WEEKLY"}),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
    ),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL", "UNTIL"]),
        fake.rrule(["FREQ", "INTERVAL"]),
    ),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT", "BYDAY"]),
    ),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT", "BYDAY", "BYSETPOS"]),
    ),
]
ids = [
    "no_base_rrule",
    "only_freq",
    "add_optional_field",
    "remove_optional_field",
    "add_byday_filter",
    "by_and_setpos",
]


@pytest.mark.parametrize("existing_rrule, base_rrule, new_rrule", rrules, ids=ids)
def test_akonadi_partial_offline_change_item_rrule(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    existing_rrule: bool,
    base_rrule: dict,
    new_rrule: dict,
) -> None:
    """
    Changing the content of an item on the server (description, alarms, attachments… should all be tested), nothing happens
    When the resource is set online, the content is also changed on the corresponding item in the akonadi server
    No other change occurred (other than timestamps book keeping)
    This test is separated from other change_item_contents tests because it needs special formatting / equality operators
    """
    calendar = DavCalendarFactory.create(nb_items=0)
    event = DavEventFactory.create(
        calendar=calendar.name, use_rrule=existing_rrule, rrule=base_rrule
    )
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) == 1
    item = items[0]

    wait_until(lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(items))
    event = dav_principal.calendar(calendar.name).event_by_url(item.remoteId())

    payload = bytes(item.payloadData()).decode()
    item_calendar = Calendar.from_ical(payload)
    [item_event] = item_calendar.walk("VEVENT")

    if not existing_rrule:
        assert "RRULE" not in item_event
        assert "RRULE" not in event.icalendar_component

    else:
        assert normalize_vrecur(item_event["RRULE"]) == normalize_vrecur(
            event.icalendar_component["RRULE"]
        )

    groupware_resource.set_online(False)

    new_value = vRecur(new_rrule)
    event.icalendar_component["RRULE"] = new_value
    event.save()

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    if not existing_rrule:
        assert "RRULE" not in updated_event
    else:
        assert normalize_vrecur(updated_event["RRULE"]) != normalize_vrecur(new_value)
    assert rrule_are_equal(
        new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.set_online(True)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value)
    assert rrule_are_equal(
        new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )
    assert_all_collections_are_equals(dav_principal, groupware_resource)
