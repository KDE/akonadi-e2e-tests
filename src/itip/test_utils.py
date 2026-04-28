# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime
from zoneinfo import ZoneInfo

from AkonadiCore import Akonadi  # type: ignore
from icalendar import Calendar, Event

from src.factories.itip_factory import BaseITIP


def assert_dav_event_equal_itip(event: Event, itip: BaseITIP) -> None:
    def norm_dt(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.replace(microsecond=0)

    assert itip.uid == event.get("UID")
    assert itip.organizer_name == event.get("ORGANIZER").CN
    assert itip.organizer_email == event.get("ORGANIZER").email
    assert itip.summary == event.get("SUMMARY").ical_value
    assert itip.description == event.get("DESCRIPTION").ical_value
    assert itip.location == event.get("LOCATION").ical_value
    assert norm_dt(itip.dtstart) == norm_dt(event.get("DTSTART").dt)
    assert norm_dt(itip.dtend) == norm_dt(event.get("DTEND").dt)
    assert norm_dt(itip.created_at) == norm_dt(event.get("CREATED").dt)
    assert norm_dt(itip.last_modified_at) == norm_dt(event.get("LAST-MODIFIED").dt)

    assert len(itip.attendees) == len(event.get("ATTENDEE"))
    itip_attendees = sorted(itip.attendees, key=lambda a: a.email)
    event_attendees = sorted(event.get("ATTENDEE"), key=lambda a: a.email)
    for itip_attendee, event_attendee in zip(itip_attendees, event_attendees, strict=True):
        assert itip_attendee.email == event_attendee.email
        assert itip_attendee.name == event_attendee.CN
        assert itip_attendee.partstat == event_attendee.PARTSTAT


def assert_akonadi_item_equal_itip(item: Akonadi.Item, itip: BaseITIP):
    payload = bytes(item.payloadData()).decode()
    item_calendar = Calendar.from_ical(payload)
    [item_event] = item_calendar.walk("VEVENT")
    assert_dav_event_equal_itip(item_event, itip)  # type: ignore[arg-type]
