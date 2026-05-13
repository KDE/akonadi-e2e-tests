# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from datetime import datetime
from zoneinfo import ZoneInfo

import icalendar
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Calendar, Event
from caldav.lib.error import NotFoundError

from src.factories.itip_factory import ITIPEvent


def assert_ical_event_equals_itip_event(event: icalendar.Event, itip: ITIPEvent) -> None:
    def norm_dt(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.replace(microsecond=0)

    assert itip.uid == event.get("UID")
    assert itip.organizer_email == event.get("ORGANIZER").email
    assert itip.organizer_name == event.get("ORGANIZER").CN
    assert norm_dt(itip.dtstart) == norm_dt(event.get("DTSTART").dt)
    assert norm_dt(itip.dtend) == norm_dt(event.get("DTEND").dt)
    assert itip.summary == event.get("SUMMARY").ical_value
    assert itip.description == event.get("DESCRIPTION").ical_value
    assert itip.location == event.get("LOCATION").ical_value
    assert [itip.rrule] == event.get("RRULE", {}).get("FREQ", [None])

    event_attendees = (
        event.get("ATTENDEE")
        if isinstance(event.get("ATTENDEE"), list)
        else [event.get("ATTENDEE")]
    )
    assert len(itip.attendees) == len(event_attendees)
    itip_attendees = sorted(itip.attendees, key=lambda a: a.email)
    event_attendees = sorted(event_attendees, key=lambda a: a.email)
    for itip_attendee, event_attendee in zip(itip_attendees, event_attendees, strict=True):
        assert itip_attendee.email == event_attendee.email
        assert itip_attendee.name == event_attendee.CN
        assert itip_attendee.partstat == event_attendee.PARTSTAT


def assert_akonadi_item_equals_itip_event(item: Akonadi.Item, itip: ITIPEvent):
    payload = bytes(item.payloadData()).decode()
    [item_event] = icalendar.Calendar.from_ical(payload).walk("VEVENT")
    assert_ical_event_equals_itip_event(item_event, itip)  # type: ignore[arg-type]


def event_by_uid(calendar: Calendar, uid: str) -> Event | None:
    try:
        return calendar.get_event_by_uid(uid)  # type: ignore[return-value]
    except NotFoundError:
        return None


def event_exists(calendar: Calendar, uid: str) -> bool:
    return event_by_uid(calendar, uid) is not None


def event_sequence_eq(calendar: Calendar, uid: str, sequence: int | None) -> bool:
    sequence = sequence or 0
    if event := event_by_uid(calendar, uid):
        return event.get_icalendar_component().get("SEQUENCE", 0) == sequence
    return False
