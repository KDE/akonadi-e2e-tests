# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import timedelta
from logging import getLogger

import pytest
from caldav.collection import Principal
from caldav.elements import dav
from caldav.lib.error import NotFoundError
from icalendar import Calendar, vRecur

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.utils import AkonadiUtils, WaitJobError
from src.dav.dav_server import DAVServer
from src.dav.radicale_server import RadicaleServer
from src.dav.test_utils import (
    assert_all_collections_are_equals,
    field_is_equal,
    normalize_vrecur,
    rrule_are_equal,
)
from src.factories.event_factory import (
    AkonadiEventFactory,
    DavCalendarFactory,
    DavEventFactory,
    fake,
)
from src.test import wait_until

log = getLogger(__name__)


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

    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
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
    reason="Akonadi bug, after conflict it takes the local name https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/146",
    strict=True,
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

    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource):
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


def test_conflict_remove_collection(
    dav_principal: Principal, groupware_resource: DAVResource, akonadi_client: AkonadiClient
) -> None:
    """
    Removing an item from a collection in the akonadi server, removing the collection on the server, nothing happens
    When the resource is set online, the collection is removed from the akonadi server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) > 0
    item = items[0]

    groupware_resource.set_online(False)

    akonadi_client.delete_item(item.id())

    dav_calendar = dav_principal.calendar(calendar.name)

    dav_calendar.delete()
    wait_until(
        lambda: calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    assert collection.id() in [c.id() for c in groupware_resource.list_collections()]
    assert len(groupware_resource.list_items(collection.id())) == len(calendar.events) - 1
    assert item.id() not in [i.id() for i in groupware_resource.list_items(collection.name())]

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.id() not in [c.id() for c in groupware_resource.list_collections()]


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
    pytest.param("DURATION", f"PT{fake.random_int(min=1, max=8)}H", False, id="duration"),
]


@pytest.mark.parametrize("field, new_value, use_dtend", changed_field_data)
def test_update_item_locally_in_collection_removed_on_server(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
    field: str,
    new_value: str,
    use_dtend: bool,
) -> None:
    """
    Changing the content of an item in the akonadi server, removing the collection on the server, nothing happens,
    when the resource is set online, the collection is removed from the akonadi server
    """
    calendar = DavCalendarFactory.create()
    DavEventFactory.create(calendar=calendar.name, use_dtend=use_dtend, dtstart=random_dtsart)

    groupware_resource.synchronize()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    items = groupware_resource.list_items(collection.name())
    assert len(items) > 0
    item = items[0]

    groupware_resource.set_online(False)

    payload = bytes(item.payloadData()).decode()
    item_calendar = Calendar.from_ical(payload)
    [item_event] = item_calendar.walk("VEVENT")
    item_event[field] = new_value
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    dav_calendar = dav_principal.calendar(calendar.name)

    dav_calendar.delete()
    wait_until(
        lambda: calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    )

    # Since we're still offline, ensure no change was made locally
    assert collection.id() in [c.id() for c in groupware_resource.list_collections()]

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.remoteId() not in [c.remoteId() for c in akonadi_client.list_collections()]


def test_conflict_add_item_akonadi_remove_collection_server(
    dav_principal: Principal, groupware_resource: DAVResource, akonadi_client: AkonadiClient
) -> None:
    """
    Adding an item to a collection in the akonadi server, removing the collection on the server, nothing happens;
    when the resource is set online, the collection is removed from the akonadi server, the item is removed as well
    """
    initial_factory = DavCalendarFactory.create()
    groupware_resource.synchronize()
    collection = groupware_resource.collection_from_display_name(initial_factory.name)
    calendar_to_delete = dav_principal.calendar(initial_factory.name)

    groupware_resource.set_online(False)

    # Add an event in Akonadi, check it exists in the resource and not in the server
    AkonadiEventFactory.create(calendar=initial_factory.name)
    items_from_collection_to_delete = groupware_resource.list_items(collection.id())

    assert len(groupware_resource.list_items(collection.id())) == len(initial_factory.events) + 1
    assert len(dav_principal.calendar(initial_factory.name).get_events()) == len(
        initial_factory.events
    )

    # Delete collection server side, check collection is deleted in the server and not in the resource
    calendar_to_delete.delete()

    assert initial_factory.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert initial_factory.name in [c.displayName() for c in groupware_resource.list_collections()]

    groupware_resource.set_online(True)

    # Check collection is deleted on both sides
    assert initial_factory.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert initial_factory.name not in [
        c.displayName() for c in groupware_resource.list_collections()
    ]

    # Check all items are deleted on akonadi side
    for item in items_from_collection_to_delete:
        with pytest.raises(WaitJobError):
            akonadi_client.item_by_id(item.id(), False)

    # Check other collections are still there
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_add_item_remotely_to_collection_removed_locally(
    dav_principal: Principal,
    groupware_resource: DAVResource,
) -> None:
    """
    Adding an item to a collection on the server, removing the collection in akonadi server, nothing happens, when the
    resource is set online, the collection is removed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    groupware_resource.set_online(False)

    DavEventFactory.create(calendar=calendar.name)

    collection = groupware_resource.collection_from_display_name(calendar.name)

    # No change was replicated on the server
    assert dav_principal.calendar(calendar.name) is not None
    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
        groupware_resource.delete_collection(collection.remoteId())

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.remoteId() not in [
        c.remoteId() for c in groupware_resource.list_collections()
    ]
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_delete_item_remotely_on_collection_removed_locally(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    akonadi_client: AkonadiClient,
) -> None:
    """
    Removing an item from a collection on the server, removing the collection in akonadi server, nothing happens, when
    the resource is set online, the collection is removed on the server
    """
    calendar = DavCalendarFactory.create()
    groupware_resource.synchronize()

    groupware_resource.set_online(False)

    event_to_delete = dav_principal.calendar(calendar.name).events()[0]
    event_to_delete.delete()

    collection = groupware_resource.collection_from_display_name(calendar.name)
    assert collection is not None
    with AkonadiUtils.wait_for_queued_change_replay(groupware_resource.instance):
        akonadi_client.delete_collection(collection.id())

    # No change was replicated on the server
    assert dav_principal.calendar(calendar.name) is not None

    groupware_resource.set_online(True)

    # assert the collection is deleted both in akonadi and in the server
    assert calendar.name not in [c.get_display_name() for c in dav_principal.get_calendars()]
    assert collection.remoteId() not in [
        c.remoteId() for c in groupware_resource.list_collections()
    ]
    assert_all_collections_are_equals(dav_principal, groupware_resource)


random_dtsart = fake.future_datetime()

changed_field_data = [
    pytest.param(
        "DESCRIPTION", fake.paragraph(), fake.paragraph(), fake.boolean(), id="description"
    ),
    pytest.param("SUMMARY", fake.sentence(), fake.sentence(), fake.boolean(), id="summary"),
    pytest.param(
        "DTSTART",
        fake.future_datetime().strftime("%Y%m%dT%H%M%S"),
        fake.future_datetime().strftime("%Y%m%dT%H%M%S"),
        fake.boolean(),
        id="dtstart",
    ),
    pytest.param(
        "DTEND",
        fake.date_time_between(
            start_date=random_dtsart, end_date=random_dtsart + timedelta(hours=8)
        ).strftime("%Y%m%dT%H%M%S"),
        fake.date_time_between(
            start_date=random_dtsart, end_date=random_dtsart + timedelta(hours=8)
        ).strftime("%Y%m%dT%H%M%S"),
        True,
        id="dtend",
    ),
    pytest.param(
        "DURATION",
        f"PT{fake.random_int(min=1, max=4)}H",
        f"PT{fake.random_int(min=5, max=8)}H",
        False,
        id="duration",
    ),
]


@pytest.mark.parametrize(
    "field, new_value_akonadi, new_value_server, use_dtend", changed_field_data
)
def test_akonadi_conflict_change_item_contents(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    field: str,
    new_value_akonadi: str,
    new_value_server: str,
    use_dtend: bool,
    dav_server: DAVServer,
) -> None:
    """
    Changing the content of an item on the server, changing the content of the same item in akonadi server, nothing happens
    When the resource is set online, the server's version of the item is kept
    """
    if isinstance(dav_server, RadicaleServer):
        pytest.skip("Radicale sometimes doesn't update etag in time leading to a flaky test")

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

    event.icalendar_component[field] = new_value_server
    event.save()

    item_event[field] = new_value_akonadi
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() == new_value_akonadi
    assert field_is_equal(
        field, new_value_server, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.set_online(True)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert updated_event[field].to_ical().decode() == new_value_server
    assert field_is_equal(
        field, new_value_server, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )


rrules = [
    (False, dict(), fake.rrule(), fake.rrule()),
    (True, {"FREQ": "MONTHLY"}, {"FREQ": "WEEKLY"}, {"FREQ": "YEARLY"}),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
    ),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL", "UNTIL"]),
        fake.rrule(["FREQ", "INTERVAL"]),
        fake.rrule(["FREQ", "INTERVAL"]),
    ),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT", "BYDAY"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT", "BYDAY"]),
    ),
    (
        True,
        fake.rrule(["FREQ", "INTERVAL", "COUNT"]),
        fake.rrule(["FREQ", "INTERVAL", "COUNT", "BYDAY", "BYSETPOS"]),
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


@pytest.mark.parametrize(
    "existing_rrule, base_rrule, new_rrule_akonadi, new_rrule_server", rrules, ids=ids
)
def test_akonadi_conflict_change_item_rrule(
    dav_principal: Principal,
    groupware_resource: DAVResource,
    existing_rrule: bool,
    base_rrule: dict,
    new_rrule_akonadi: dict,
    new_rrule_server: dict,
    dav_server: DAVServer,
) -> None:
    """
    Changing the content of an item on the server, changing the content of the same item in akonadi server, nothing happens
    When the resource is set online, the server's version of the item is kept
    This test is separated from other change_item_contents tests because it needs special formatting / equality operators
    """
    if isinstance(dav_server, RadicaleServer):
        pytest.skip("Radicale sometimes doesn't update etag in time leading to a flaky test")

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

    new_value_server = vRecur(new_rrule_server)
    event.icalendar_component["RRULE"] = new_value_server
    event.save()

    new_value_akonadi = vRecur(new_rrule_akonadi)
    item_event["RRULE"] = new_value_akonadi
    new_payload = item_calendar.to_ical()
    groupware_resource.modify_payload(item.id(), new_payload)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value_akonadi)
    assert rrule_are_equal(
        new_value_server, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )

    groupware_resource.set_online(True)

    updated_item = groupware_resource.akonadi_client.item_by_id(item.id())
    updated_payload = bytes(updated_item.payloadData()).decode()
    updated_calendar = Calendar.from_ical(updated_payload)
    [updated_event] = updated_calendar.walk("VEVENT")

    assert normalize_vrecur(updated_event["RRULE"]) == normalize_vrecur(new_value_server)
    assert rrule_are_equal(
        new_value_server, dav_principal.calendar(calendar.name).event_by_url(item.remoteId())
    )
