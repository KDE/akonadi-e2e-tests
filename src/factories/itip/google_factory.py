# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import string
from dataclasses import dataclass

import factory
from faker import Faker
from icalendar.enums import PARTSTAT

from src.factories.itip_factory import BaseITIP, BaseITIPFactory, ITIPAttendeeFactory

fake = Faker()


@dataclass
class GoogleITIP(BaseITIP):
    microsoft_cdo_ownerapptid: str

    def attendee_ical(self, cn: str, email: str, partstat: PARTSTAT) -> str:
        return f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT={partstat};RSVP=TRUE;CN={cn};X-NUM-GUESTS=0:mailto:{email}"

    def attendees_ical(self) -> str:
        return "\n".join([self.attendee_ical(a.name, a.email, a.partstat) for a in self.attendees])

    def to_ical(self) -> str:
        return f"""
BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:{self.method}
BEGIN:VTIMEZONE
TZID:Europe/Paris
X-LIC-LOCATION:Europe/Paris
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:GMT+2
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:GMT+1
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTART;TZID={self.dtstart.tzinfo}:{self.dtstart.strftime("%Y%m%dT%H%M%S")}
DTEND;TZID={self.dtend.tzinfo}:{self.dtend.strftime("%Y%m%dT%H%M%S")}
DTSTAMP:20260427T153105Z
{self.organizer_ical()}
UID:{self.uid}
{self.attendees_ical()}
X-MICROSOFT-CDO-OWNERAPPTID:{self.microsoft_cdo_ownerapptid}
CREATED:{self.created_at.strftime("%Y%m%dT%H%M%SZ")}
DESCRIPTION:{self.description}
LAST-MODIFIED:{self.last_modified_at.strftime("%Y%m%dT%H%M%SZ")}
LOCATION:{self.location}
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:{self.summary}
TRANSP:OPAQUE
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:This is an event reminder
TRIGGER:-P0DT0H30M0S
END:VALARM
END:VEVENT
END:VCALENDAR
"""


class GoogleITIPFactory(BaseITIPFactory):
    class Meta:
        model = GoogleITIP

    uid = factory.Faker(
        "lexify", text=26 * "?" + "@google.com", letters=string.ascii_lowercase + string.digits
    )
    microsoft_cdo_ownerapptid = factory.Faker("numerify", text="##########")

    @classmethod
    def _build(cls, model_class, **kwargs):
        attendees = ITIPAttendeeFactory.build_batch(kwargs.get("nb_attendees"))
        # Google behavior is to add the organizer as an attendee
        attendees.insert(
            0,
            ITIPAttendeeFactory(
                name=kwargs.get("organizer_name"),
                email=kwargs.get("organizer_email"),
                partstat=PARTSTAT.ACCEPTED,
            ),
        )
        itip = model_class(
            method=kwargs.get("method"),
            uid=kwargs.get("uid"),
            organizer_name=kwargs.get("organizer_name"),
            organizer_email=kwargs.get("organizer_email"),
            summary=kwargs.get("summary"),
            description=kwargs.get("description"),
            location=kwargs.get("location"),
            dtstart=kwargs.get("dtstart"),
            dtend=kwargs.get("dtend"),
            microsoft_cdo_ownerapptid=kwargs.get("microsoft_cdo_ownerapptid"),
            attendees=attendees,
            created_at=kwargs.get("created_at"),
            last_modified_at=kwargs.get("last_modified_at"),
        )
        return itip
