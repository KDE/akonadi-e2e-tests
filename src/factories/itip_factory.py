# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from __future__ import annotations

import abc
import string
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, get_args
from zoneinfo import ZoneInfo

import factory
from dateutil.relativedelta import relativedelta
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


ITIPEventRRule = Literal["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]


@dataclass
class ITIPEvent(abc.ABC):
    provider: str
    uid: str
    organizer_name: str
    organizer_email: str
    summary: str
    description: str | None
    location: str
    dtstart: datetime
    dtend: datetime
    rrule: ITIPEventRRule | None
    rrule_until: datetime | None
    recurrence_id: datetime | None
    sequence: int | None
    attendees: list[ITIPAttendee]
    exdate: list[datetime]

    def set_rrule_until_utc(self, rrule: datetime | None) -> None:
        self.rrule_until = rrule.astimezone(UTC) if rrule else None

    def clone(self) -> ITIPEvent:
        return deepcopy(self)

    def get_occurrence_id(self, occurrence_index: int) -> datetime:
        match self.rrule:
            case "DAILY":
                return self.dtstart + timedelta(days=occurrence_index)
            case "WEEKLY":
                return self.dtstart + timedelta(weeks=occurrence_index)
            case "MONTHLY":
                return self.dtstart + relativedelta(months=occurrence_index)
            case "YEARLY":
                return self.dtstart + relativedelta(years=occurrence_index)
            case _:
                raise ValueError(f"Unsupported rrule {self.rrule}")

    def create_exception(self, occurrence_index: int) -> ITIPEvent:
        new_itip = self.clone()
        new_itip.increment_sequence()
        new_itip.rrule = None
        new_itip.rrule_until = None
        new_itip.recurrence_id = self.get_occurrence_id(occurrence_index)
        new_itip.dtend = new_itip.recurrence_id + (self.dtend - self.dtstart)
        new_itip.dtstart = new_itip.recurrence_id
        return new_itip

    def get_attendee_by_email(self, email: str) -> ITIPAttendee:
        for attendee in self.attendees:
            if attendee.email == email:
                return attendee
        raise ValueError(f"Attendee with email {email} not found")

    def get_first_non_organizer_attendee(self) -> ITIPAttendee:
        for attendee in self.attendees:
            if attendee.email != self.organizer_email:
                return attendee
        raise ValueError(f"No attendee different from organizer {self.organizer_email}")

    def add_timedelta(self, time: timedelta) -> None:
        self.dtstart += time
        self.dtend += time

    def increment_sequence(self, value=1) -> None:
        self.sequence = (self.sequence or 0) + value

    def get_rrule_byday(self) -> str | None:
        WEEK_DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        match self.rrule:
            case None | "DAILY" | "YEARLY":
                return None
            case "WEEKLY":
                week_day = WEEK_DAYS[self.dtstart.weekday()]
                return f"{week_day}"
            case "MONTHLY":
                week_day = WEEK_DAYS[self.dtstart.weekday()]
                week_ith = (self.dtstart.day - 1) // 7 + 1
                return f"{week_ith}{week_day}"
            case _:
                raise ValueError(f"Unsupported rrule {self.rrule}")


class ITIPEventFactory(factory.Factory):
    class Meta:
        model = ITIPEvent
        abstract = True

    provider = ""
    uid = factory.Faker("uuid4")
    organizer_name = factory.Faker("name")
    organizer_email = factory.Faker("email")
    summary = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    location = factory.Faker("city")
    dtstart = factory.LazyFunction(lambda: fake.future_datetime(tzinfo=ZoneInfo("Europe/Paris")))
    dtend = factory.LazyAttribute(lambda o: o.dtstart + timedelta(hours=o.duration_hours))
    sequence: int | None = 0
    rrule = factory.Faker("random_element", elements=get_args(ITIPEventRRule))
    rrule_until: datetime | None = None
    recurrence_id: datetime | None = None
    attendees = factory.LazyFunction(list)
    exdate = factory.LazyFunction(list)

    duration_hours = factory.Faker("random_int", min=1, max=8)
    use_rrule = False
    nb_attendees = 1

    @classmethod
    def get_attendees(cls, **kwargs) -> list[ITIPAttendee]:
        if attendees := kwargs.get("attendees"):
            return attendees
        return ITIPAttendeeFactory.build_batch(kwargs.get("nb_attendees", 0))

    @classmethod
    def get_rrule(cls, **kwargs) -> list[ITIPAttendee] | None:
        if (rrule := kwargs.get("rrule")) is not None:
            return rrule
        if kwargs.get("use_rrule"):
            return fake.random_element(get_args(ITIPEventRRule))
        return None

    @classmethod
    def _build(cls, model_class, **kwargs) -> ITIPEvent:
        assert kwargs.get("provider"), (
            "ITIP requires provider to be overridden by factory child classes"
        )
        return model_class(
            provider=kwargs.get("provider"),
            uid=kwargs.get("uid"),
            organizer_name=kwargs.get("organizer_name"),
            organizer_email=kwargs.get("organizer_email"),
            summary=kwargs.get("summary"),
            description=kwargs.get("description"),
            location=kwargs.get("location"),
            dtstart=kwargs.get("dtstart"),
            dtend=kwargs.get("dtend"),
            sequence=kwargs.get("sequence"),
            rrule=cls.get_rrule(**kwargs),
            rrule_until=kwargs.get("rrule_until"),
            recurrence_id=kwargs.get("recurrence_id"),
            attendees=cls.get_attendees(**kwargs),
            exdate=kwargs.get("exdate"),
        )

    @classmethod
    def create_from(cls, obj: ITIPEvent, reset_fields: list[str], **kwargs) -> ITIPEvent:
        obj = obj.clone()
        values = obj.__dict__
        for key in reset_fields:
            if key not in values:
                raise ValueError(f"Key {key} not found in object")
            del values[key]
        values.update(kwargs)
        return cls.build(**values)


class GoogleITIPEventFactory(ITIPEventFactory):
    class Meta:
        abstract = False

    provider = "google"
    uid = factory.Faker(
        "lexify", text=26 * "?" + "@google.com", letters=string.ascii_lowercase + string.digits
    )

    @classmethod
    def get_attendees(cls, **kwargs) -> list[ITIPAttendee]:
        # Google adds the organizer as an attendee
        attendees = super().get_attendees(**kwargs)
        if kwargs.get("organizer_email") in [attendee.email for attendee in attendees]:
            return attendees
        return [
            ITIPAttendeeFactory.build(
                email=kwargs.get("organizer_email"),
                name=kwargs.get("organizer_name"),
                partstat=PARTSTAT.ACCEPTED,
            ),
            *attendees,
        ]


class MicrosoftITIPEventFactory(ITIPEventFactory):
    class Meta:
        abstract = False

    provider = "microsoft"
    uid = factory.Faker("lexify", text=112 * "?", letters=string.ascii_uppercase + string.digits)


class AkonadiITIPEventFactory(ITIPEventFactory):
    class Meta:
        abstract = False

    provider = "akonadi"
    sequence = None

    @classmethod
    def _build(cls, model_class, **kwargs) -> ITIPEvent:
        kwargs["dtstart"] = kwargs["dtstart"].astimezone(UTC)
        kwargs["dtend"] = kwargs["dtend"].astimezone(UTC)
        return super()._build(model_class, **kwargs)
