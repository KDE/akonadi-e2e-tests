# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from urllib.parse import unquote, unquote_plus

import icalendar
from AkonadiCore import Akonadi  # type: ignore
from caldav.calendarobjectresource import Event
from caldav.collection import Principal

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

    collections = [c for c in dav_resource.list_collections() if c.parentCollection().id() != 0]
    collections.sort(key=lambda c: unquote(c.remoteId()))

    for calendar, collection in zip(calendars, collections, strict=False):
        assert unquote(calendar.canonical_url) == unquote(collection.remoteId())
        assert_collection_equal_calendar(
            calendar.canonical_url, dav_resource, dav_principal, payload_test
        )


def assert_collection_equal_calendar(
    name: str, dav_resource: DAVResource, dav_principal: Principal, payload_test: bool = True
) -> None:
    items = dav_resource.list_items(name)
    items.sort(key=lambda i: unquote_plus(i.remoteId()) or "-1")

    calendar = dav_principal.calendar(cal_url=name)

    events = calendar.get_events()
    events.sort(key=lambda e: unquote_plus(e.canonical_url) or "-1")
    assert len(events) == len(items)

    for event, item in zip(events, items, strict=False):
        assert unquote_plus(event.canonical_url) == unquote_plus(item.remoteId())
        if payload_test:
            assert_payload_are_equal(item, event)


IGNORED_PROPERTIES = {"CREATED", "LAST-MODIFIED", "DTSTAMP", "TRANSP"}


def assert_payload_are_equal(akonadi_item: Akonadi.Item, dav_event: Event) -> None:
    def _filter_lines(lines):
        return [line for line in lines if line.split(":")[0] not in IGNORED_PROPERTIES]

    akonadi_event = _filter_lines(item_to_event(akonadi_item).content_lines())
    server_event = _filter_lines(dav_event.icalendar_instance.events[0].content_lines())
    assert akonadi_event == server_event


def get_collection_attributes(
        name: str, dav_resource: DAVResource, dav_principal: Principal, payload_test: bool = True
) -> dict[str, str]:
    return {
        attr.type().data().decode("utf-8"): attr.serialized().data().decode("utf-8")
        for attr in dav_resource.resolve_collection(name).attributes()
    }
