# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Arnaud Chirat <arnaud.chirat@enioka.com>
# SPDX-FileCopyrightText: 2026 Alan Thouvenin <alan.thouvenin@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from datetime import timedelta

import pytest
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Principal
from caldav.elements import ical
from icalendar import Calendar, vRecur

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.test_utils import assert_akonadi_items_are_equal
from src.akonadi.utils import AkonadiUtils
from src.dav.test_utils import (
    assert_all_collections_are_equals,
    assert_collection_equal_calendar,
    field_is_equal,
    normalize_vrecur,
    rrule_are_equal,
)
from src.factories.event_factory import (
    AkonadiCalendarFactory,
    AkonadiEventFactory,
    DavCalendarFactory,
    DavEventFactory,
    GenericCalendar,
    fake,
)
from src.test import wait_until


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
    reason="Akonadi bug? Akonadi doesnt seem to sync calendar attributes https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/101",
    strict=True,
)
def test_akonadi_sync_change_color_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Changing the color of a collection in the akonadi server, the change is replayed on the server
    """
    calendar: GenericCalendar = DavCalendarFactory.create()
    new_color = fake.qcolor()
    groupware_resource.synchronize()
    assert calendar.name in [c.displayName() for c in groupware_resource.list_collections()]

    collection = groupware_resource.collection_from_display_name(calendar.name)
    groupware_resource.set_collection_color(collection.name(), new_color)
    assert groupware_resource.get_collection_color(collection.name()) == new_color

    groupware_resource.synchronize()
    assert groupware_resource.get_collection_color(collection.name()) == new_color
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
        groupware_resource.list_collections(exclude_resource_root_collection=True)
    )
    collection_to_delete = groupware_resource.collection_from_display_name(calendar_to_delete.name)

    groupware_resource.set_online(False)

    job = Akonadi.CollectionDeleteJob(collection_to_delete)
    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
        AkonadiUtils.wait_for_job(job)

    # assert nothing happens

    # the calendar is still on server side but not anymore on akonadi side
    unsynced_calendars = dav_principal.get_calendars()
    assert len(unsynced_calendars) - 1 == len(
        groupware_resource.list_collections(exclude_resource_root_collection=True)
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
        groupware_resource.list_collections(exclude_resource_root_collection=True)
    )
    assert calendar_to_delete.name not in current_calendars_display_name
    assert unchanged_calendar.name in current_calendars_display_name

    # assert all events are still there
    assert_all_collections_are_equals(dav_principal, groupware_resource)


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

    groupware_resource.update_collection_displayname(initial_collection.name(), new_name)

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


def test_akonadi_offline_sync_add_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Adding an item to a collection in the akonadi server, nothing happens
    When the resource is set online, the change is replayed on the server
    """

    # Create an initial calendar on both sides
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    groupware_resource.set_online(False)

    # Add an event in Akonadi, check it exists in the resource and not in the server
    AkonadiEventFactory.create(calendar=calendar.name)
    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) + 1
    assert len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events)

    # Synchronize, then check the event has been added server-side
    groupware_resource.set_online(True)

    wait_until(
        lambda: len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) + 1
    )


@pytest.mark.xfail(
    reason="Akonadi bug? The resource goes back to the old color once back online, see https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/101",
    strict=True,
)
def test_akonadi_offline_change_color_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Changing the color of a collection in the akonadi server, nothing happens
    When the resource is set online, the change is replayed on the server
    """
    calendar: GenericCalendar = DavCalendarFactory.create()
    new_color = fake.qcolor()
    groupware_resource.synchronize()
    assert calendar.name in [c.displayName() for c in groupware_resource.list_collections()]

    collection = groupware_resource.collection_from_display_name(calendar.name)
    old_color = groupware_resource.get_collection_color(collection.name())

    groupware_resource.set_online(False)

    groupware_resource.set_collection_color(collection.name(), new_color)

    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert groupware_resource.get_collection_color(collection.name()) == new_color
    assert dav_principal.calendar(calendar.name).get_property(ical.CalendarColor()) == old_color

    groupware_resource.set_online(True)
    assert groupware_resource.get_collection_color(collection.name()) == new_color
    wait_until(
        lambda: (
            dav_principal.calendar(calendar.name).get_property(ical.CalendarColor()) == new_color
        )
    )

    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_akonadi_offline_remove_item(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection in the akonadi server, nothing happens, when the resource is set online, the change is replayed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.id())
    item_to_delete = items[0]

    assert_collection_equal_calendar(collection.remoteId(), groupware_resource, dav_principal)

    groupware_resource.set_online(False)
    akonadi_client.delete_item(item_to_delete.id())

    # assert nothing happens
    assert len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events)

    # Synchronize is done when the resource is set online on Dav-Implementation, so no need to call synchronize()
    groupware_resource.set_online(True)

    # item should be removed after synchronization
    assert len(dav_principal.calendar(calendar.name).get_events()) == len(calendar.events) - 1
    assert_collection_equal_calendar(collection.remoteId(), groupware_resource, dav_principal)


def test_offline_rename_collection(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    """
    Renaming a collection in the akonadi server, nothing happens, when the resource is set online, the change is replayed on the server.
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()
    old_name, new_name = calendar.name, f"{calendar.name}{fake.word()}"
    initial_collection = groupware_resource.collection_from_display_name(old_name)
    initial_items = groupware_resource.list_items(initial_collection.id())

    assert_all_collections_are_equals(dav_principal, groupware_resource)

    groupware_resource.set_online(False)
    groupware_resource.update_collection_displayname(initial_collection.name(), new_name)

    # Check the rename occurred locally and not on remote
    updated_collection_names = [c.displayName() for c in groupware_resource.list_collections()]
    assert old_name not in updated_collection_names
    assert new_name in updated_collection_names

    unsynced_calendars = [c.get_display_name() for c in dav_principal.get_calendars()]
    assert old_name in unsynced_calendars
    assert new_name not in unsynced_calendars

    # Set online do a full sync
    groupware_resource.set_online(True)

    synced_calendars = [c.get_display_name() for c in dav_principal.get_calendars()]
    assert old_name not in synced_calendars
    assert new_name in synced_calendars

    updated_collection = groupware_resource.collection_from_display_name(new_name)
    updated_items = groupware_resource.list_items(updated_collection.id())
    assert len(initial_items) == len(updated_items)
    assert_akonadi_items_are_equal(initial_items, updated_items)

    # Check the items are matching between resource and server
    assert_all_collections_are_equals(dav_principal, groupware_resource)


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
    # Duration between 9 and 16 hours to avoid any equality with the duration of the generated event (between 1 and 8 hours)
    pytest.param("DURATION", f"PT{fake.random_int(min=9, max=16)}H", False, id="duration"),
]


@pytest.mark.parametrize("field, new_value, use_dtend", changed_field_data)
def test_akonadi_change_item_contents(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    field: str,
    new_value: str,
    use_dtend: bool,
) -> None:
    """
    Changing content of an item in the akonadi server (description, alarms, attachments… should all be tested), the change is replayed on the server
    """
    calendar = DavCalendarFactory.create(nb_items=0)
    DavEventFactory.create(calendar=calendar.name, use_dtend=use_dtend, dtstart=random_dtsart)
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

    assert item_event[field] == event.get_icalendar_component()[field]

    item_event[field] = new_value
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() == new_value
    wait_until(
        lambda: field_is_equal(
            field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
        )
    )


@pytest.mark.xfail(
    reason="Akonadi bug ? The content is not changed in the akonadi server after partial sync: https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/103",
    strict=True,
)
@pytest.mark.parametrize("field, new_value, use_dtend", changed_field_data)
def test_akonadi_partial_change_item_contents(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    field: str,
    new_value: str,
    use_dtend: bool,
) -> None:
    """
    Changing content of an item on the server (description, alarms, attachments… should all be tested)
    After requesting a partial sync, the content is also changed on the corresponding item in the akonadi server
    No other change occurred (other than timestamps book keeping)
    """
    calendar = DavCalendarFactory.create(nb_items=0)
    DavEventFactory.create(calendar=calendar.name, use_dtend=use_dtend, dtstart=random_dtsart)
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) == 1
    item = items[0]

    event = dav_principal.calendar(calendar.name).event_by_url(item.remoteId())

    payload = bytes(item.payloadData()).decode()
    item_calendar = Calendar.from_ical(payload)
    [item_event] = item_calendar.walk("VEVENT")
    assert item_event[field] == event.icalendar_component[field]

    event.icalendar_component[field] = new_value
    event.save()

    assert field_is_equal(
        field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.sync_collection(collection.remoteId())

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() == new_value
    assert field_is_equal(
        field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.parametrize("field, new_value, use_dtend", changed_field_data)
def test_akonadi_offline_change_item_contents(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    field: str,
    new_value: str,
    use_dtend: bool,
) -> None:
    """
    Changing the content of an item on the server (description, alarms, attachments… should all be tested), nothing happens
    When the resource is set online, the content is also changed on the corresponding item in the akonadi server, no other change occurred (other than timestamps book keeping)
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

    assert item_event[field] == event.get_icalendar_component()[field]

    groupware_resource.set_online(False)

    item_event[field] = new_value
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() == new_value
    assert not field_is_equal(
        field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.set_online(True)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() == new_value
    wait_until(
        lambda: field_is_equal(
            field, new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
        )
    )


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
def test_akonadi_change_item_rrule(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    existing_rrule: bool,
    base_rrule: dict,
    new_rrule: dict,
) -> None:
    """
    Changing the rrule of an item in the akonadi server, the change is replayed on the server
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
        assert "RRULE" not in event.get_icalendar_component()

    else:
        assert normalize_vrecur(item_event["RRULE"]) == normalize_vrecur(
            event.get_icalendar_component()["RRULE"]
        )

    new_value = vRecur(new_rrule)
    item_event["RRULE"] = new_value
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value)
    wait_until(
        lambda: rrule_are_equal(
            new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
        )
    )


@pytest.mark.xfail(
    reason="Akonadi bug ? The content is not changed in the akonadi server after partial sync: https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/103",
    strict=True,
)
@pytest.mark.parametrize("existing_rrule, base_rrule, new_rrule", rrules, ids=ids)
def test_akonadi_partial_change_item_rrule(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    existing_rrule: bool,
    base_rrule: dict,
    new_rrule: dict,
) -> None:
    """
    Changing content of an item on the server (description, alarms, attachments… should all be tested)
    After requesting a partial sync, the content is also changed on the corresponding item in the akonadi server
    No other change occurred (other than timestamps book keeping)
    Changing the rrule of an item in the akonadi server, the change is replayed on the server
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

    new_value = vRecur(new_rrule)
    event.icalendar_component["RRULE"] = new_value
    event.save()

    assert rrule_are_equal(
        new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.sync_collection(collection.remoteId())

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value)
    wait_until(
        lambda: rrule_are_equal(
            new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
        )
    )
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.parametrize("existing_rrule, base_rrule, new_rrule", rrules, ids=ids)
def test_akonadi_offline_change_item_rrule(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    existing_rrule: bool,
    base_rrule: dict,
    new_rrule: dict,
) -> None:
    """
    Changing the content of an item on the server (description, alarms, attachments… should all be tested), nothing happens
    When the resource is set online, the content is also changed on the corresponding item in the akonadi server, no other change occurred (other than timestamps book keeping)
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
        assert "RRULE" not in event.get_icalendar_component()

    else:
        assert normalize_vrecur(item_event["RRULE"]) == normalize_vrecur(
            event.get_icalendar_component()["RRULE"]
        )

    groupware_resource.set_online(False)

    new_value = vRecur(new_rrule)
    item_event["RRULE"] = new_value
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value)
    assert not rrule_are_equal(
        new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.set_online(True)

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value)
    wait_until(
        lambda: rrule_are_equal(
            new_value, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
        )
    )
