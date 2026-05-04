# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import string
from dataclasses import dataclass
from urllib.parse import quote

import factory
from faker import Faker
from icalendar.enums import PARTSTAT

from src.factories.itip_factory import BaseITIP, BaseITIPFactory, ITIPAttendeeFactory

fake = Faker()


@dataclass
class MicrosoftITIP(BaseITIP):
    microsoft_cdo_ownerapptid: str
    meeting_id: str
    meeting_tid: str
    meeting_oid: str

    def attendee_ical(self, cn: str, email: str, partstat: PARTSTAT) -> str:
        return f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT={partstat};RSVP=TRUE;CN={cn}:mailto:{email}"

    def attendees_ical(self) -> str:
        return "\n".join([self.attendee_ical(a.name, a.email, a.partstat) for a in self.attendees])

    def to_ical(self) -> str:
        return rf"""
BEGIN:VCALENDAR
METHOD:REQUEST
PRODID:Microsoft Exchange Server 2010
VERSION:2.0
BEGIN:VTIMEZONE
TZID:Romance Standard Time
BEGIN:STANDARD
DTSTART:16010101T030000
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
RRULE:FREQ=YEARLY;INTERVAL=1;BYDAY=-1SU;BYMONTH=10
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:16010101T020000
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
RRULE:FREQ=YEARLY;INTERVAL=1;BYDAY=-1SU;BYMONTH=3
END:DAYLIGHT
END:VTIMEZONE
BEGIN:VEVENT
{self.organizer_ical()}
{self.attendees_ical()}
DESCRIPTION;LANGUAGE=en-US:{self.description}
UID:{self.uid}
SUMMARY;LANGUAGE=en-US:{self.summary}
DTSTART;TZID={self.dtstart.tzinfo}:{self.dtstart.strftime("%Y%m%dT%H%M%S")}
DTEND;TZID={self.dtend.tzinfo}:{self.dtend.strftime("%Y%m%dT%H%M%S")}
CLASS:PUBLIC
PRIORITY:5
DTSTAMP:20260430T120145Z
TRANSP:OPAQUE
STATUS:CONFIRMED
SEQUENCE:0
LOCATION;LANGUAGE=en-US:{self.location}
X-MICROSOFT-CDO-APPT-SEQUENCE:0
X-MICROSOFT-CDO-OWNERAPPTID:2124739021
X-MICROSOFT-CDO-BUSYSTATUS:TENTATIVE
X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY
X-MICROSOFT-CDO-ALLDAYEVENT:FALSE
X-MICROSOFT-CDO-IMPORTANCE:1
X-MICROSOFT-CDO-INSTTYPE:0
X-MICROSOFT-ONLINEMEETINGINFORMATION:{{"OnlineMeetingChannelId":null\,"OnlineMeetingProvider":3}}
X-MICROSOFT-SKYPETEAMSMEETINGURL:https://teams.microsoft.com/l/meetup-join/{quote(self.meeting_id)}/0?context=%7b%22Tid%22%3a%22{self.meeting_tid}%22%2c%22Oid%22%3a%22{self.meeting_oid}%22%7d
X-MICROSOFT-SCHEDULINGSERVICEUPDATEURL:https://api.scheduler.teams.microsoft.com/teams/{self.meeting_tid}/{self.meeting_oid}/{self.meeting_id}/0
X-MICROSOFT-SKYPETEAMSPROPERTIES:{{"cid":"19:{self.meeting_id}"\,"rid":0\,"mid":0\,"uid":null\,"private":true\,"type":0}}
X-MICROSOFT-DONOTFORWARDMEETING:FALSE
X-MICROSOFT-DISALLOW-COUNTER:FALSE
X-MICROSOFT-REQUESTEDATTENDANCEMODE:DEFAULT
X-MICROSOFT-ISRESPONSEREQUESTED:TRUE
X-MICROSOFT-LOCATIONDISPLAYNAME:{self.location}
X-MICROSOFT-LOCATIONSOURCE:None
X-MICROSOFT-LOCATIONS:[{{"DisplayName":"{self.location}"\,"LocationAnnotation":""\,"LocationUri":""\,"LocationStreet":""\,"LocationCity":""\,"LocationState":""\,"LocationCountry":""\,"LocationPostalCode":""\,"LocationFullAddress":""}}]
BEGIN:VALARM
DESCRIPTION:REMINDER
TRIGGER;RELATED=START:-PT15M
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
"""


class MicrosoftITIPFactory(BaseITIPFactory):
    class Meta:
        model = MicrosoftITIP

    uid = factory.Faker("lexify", text=112 * "?", letters=string.ascii_uppercase + string.digits)
    microsoft_cdo_ownerapptid = factory.Faker("numerify", text="##########")
    meeting_id = factory.Faker(
        "lexify",
        text="meeting_" + (48 * "?") + "@thread.v2",
        letters=string.ascii_uppercase + string.digits,
    )
    meeting_tid = factory.Faker("uuid4")
    meeting_iod = factory.Faker("uuid4")

    @classmethod
    def _build(cls, model_class, **kwargs):
        attendees = ITIPAttendeeFactory.build_batch(kwargs.get("nb_attendees"))
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
            attendees=attendees,
            created_at=None,
            last_modified_at=None,
            microsoft_cdo_ownerapptid=kwargs.get("microsoft_cdo_ownerapptid"),
            meeting_id=kwargs.get("meeting_id"),
            meeting_tid=kwargs.get("meeting_tid"),
            meeting_oid=kwargs.get("meeting_oid"),
        )
        return itip
