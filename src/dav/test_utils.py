# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from urllib.parse import unquote, unquote_plus

import icalendar
from AkonadiCore import Akonadi  # type: ignore
from caldav.calendarobjectresource import Event
from caldav.collection import Calendar, Principal
from caldav.elements import ical

from src.akonadi.dav_resource import DAVResource


def item_to_event(item: Akonadi.Item) -> icalendar.Event:
    calendar = icalendar.Calendar.from_ical(item.payloadData().data().decode())
    if not isinstance(calendar, icalendar.Calendar):
        raise ValueError("Invalid item payload")
    return calendar.events[0]


def assert_all_collections_are_equals(
    dav_principal: Principal, dav_resource: DAVResource, payload_test: bool = True
) -> None:
    calendars = dav_principal.calendars()
    calendars.sort(key=lambda c: unquote(c.canonical_url))

    collections = dav_resource.list_collections(exclude_resource_root_collection=True)
    collections.sort(key=lambda c: unquote(c.remoteId()))

    assert len(calendars) == len(collections)
    for calendar, collection in zip(calendars, collections, strict=True):
        assert unquote(calendar.canonical_url) == unquote(collection.remoteId())
        assert_collection_equal_calendar(
            calendar.canonical_url, dav_resource, dav_principal, payload_test
        )


def assert_collection_equal_calendar(
    name: str, dav_resource: DAVResource, dav_principal: Principal, payload_test: bool = True
) -> None:
    calendar = dav_principal.calendar(cal_url=name)
    [collection] = [
        c for c in dav_resource.list_collections() if unquote_plus(c.name()) == unquote_plus(name)
    ]
    assert_collection_attributes_are_equal(collection, calendar)

    items = dav_resource.list_items(name)
    items.sort(key=lambda i: unquote_plus(i.remoteId()) or "-1")

    events = calendar.get_events()
    events.sort(key=lambda e: unquote_plus(e.canonical_url) or "-1")
    assert len(events) == len(items)

    for event, item in zip(events, items, strict=False):
        assert unquote_plus(event.canonical_url) == unquote_plus(item.remoteId())
        if payload_test:
            assert_payload_are_equal(item, event)


def assert_collection_attributes_are_equal(
    collection: Akonadi.Collection, calendar: Calendar
) -> None:
    assert calendar.get_display_name() == collection.displayName()
    attr = DAVResource.get_collection_attribute(collection, Akonadi.CollectionColorAttribute)
    resource_color = attr.color() if attr else None
    assert calendar.get_property(ical.CalendarColor()) == resource_color


IGNORED_PROPERTIES = {"CREATED", "LAST-MODIFIED", "DTSTAMP", "TRANSP"}


# Sort rrule line so that we can properly test equality between rrules
def sort_rrule(rrule: str) -> str:
    fields = rrule.split(";")
    sorted_fields = []
    for field in fields:
        key_values = field.split("=")
        values = key_values[1].split(",")
        values.sort()
        sorted_fields.append(f"{key_values[0]}={','.join(values)}")
    return ";".join(sorted_fields)


def assert_payload_are_equal(akonadi_item: Akonadi.Item, dav_event: Event) -> None:
    def _filter_lines(lines):
        splitted = (line.split(":", maxsplit=1) for line in lines if line)
        filtered = ((key, value) for key, value in splitted if key not in IGNORED_PROPERTIES)
        return [
            f"RRULE:{sort_rrule(value)}" if key == "RRULE" else f"{key}:{value}"
            for key, value in filtered
        ]

    akonadi_event = _filter_lines(item_to_event(akonadi_item).content_lines())
    server_event = _filter_lines(dav_event.icalendar_instance.events[0].content_lines())
    assert akonadi_event == server_event


# Unify vrecur format (sorted lists for every field of the vrecur) so that we can properly compare two vrecur
def normalize_vrecur(rrule: icalendar.vRecur) -> icalendar.vRecur:
    for key in rrule:
        val = rrule[key]
        rrule[key] = sorted(val) if isinstance(val, list) else [val]

    return rrule


def field_is_equal(field: str, expected: str, event: Event) -> bool:
    icalendar_component = event.get_icalendar_component()
    if field in icalendar_component:
        field = icalendar_component[field].to_ical().decode()
        return field == expected
    return False


def rrule_are_equal(expected: icalendar.vRecur, event: Event) -> bool:
    icalendar_component = event.get_icalendar_component()
    if "RRULE" in icalendar_component:
        rrule = normalize_vrecur(icalendar_component["RRULE"])
        return rrule == normalize_vrecur(expected)
    return False
