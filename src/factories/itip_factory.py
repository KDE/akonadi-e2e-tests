# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import abc
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import factory
from faker import Faker
from icalendar.enums import PARTSTAT

fake = Faker()


@dataclass
class ITIPAttendee(abc.ABC):
    name: str
    email: str
    partstat: PARTSTAT


class ITIPAttendeeFactory(factory.Factory):
    class Meta:
        model = ITIPAttendee

    name = factory.Faker("name")
    email = factory.Faker("email")
    partstat = PARTSTAT.NEEDS_ACTION

    @classmethod
    def _build(cls, model_class, **kwargs):
        return model_class(name=kwargs["name"], email=kwargs["email"], partstat=kwargs["partstat"])


@dataclass
class BaseITIP(abc.ABC):
    method: str
    uid: str
    organizer_name: str
    organizer_email: str
    summary: str
    description: str
    location: str
    dtstart: datetime
    dtend: datetime
    attendees: list[ITIPAttendee]
    created_at: datetime
    last_modified_at: datetime

    @abc.abstractmethod
    def to_ical(self) -> str:
        raise NotImplementedError("Abstract method")

    def organizer_cn(self) -> str:
        return self.organizer_name if self.organizer_name else self.organizer_email

    def organizer_ical(self) -> str:
        return f"ORGANIZER;CN={self.organizer_cn()}:mailto:{self.organizer_email}"

    def get_first_non_organizer_attendee(self) -> ITIPAttendee | None:
        for attendee in self.attendees:
            if attendee.email != self.organizer_email:
                return attendee
        return None


class BaseITIPFactory(factory.Factory):
    class Meta:
        model = BaseITIP
        abstract = True

    method = "REQUEST"
    uid = factory.Faker("uuid4")
    organizer_name = factory.Faker("name")
    organizer_email = factory.Faker("email")
    summary = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    location = factory.Faker("city")
    dtstart = factory.LazyFunction(lambda: fake.future_datetime(tzinfo=ZoneInfo("Europe/Paris")))
    duration_hours = factory.Faker("random_int", min=1, max=8)
    dtend = factory.LazyAttribute(lambda o: o.dtstart + timedelta(hours=o.duration_hours))
    nb_attendees = factory.Faker("random_int", min=1, max=2)
    created_at = datetime.now()
    last_modified_at = datetime.now()
