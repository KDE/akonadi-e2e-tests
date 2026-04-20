# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Kevin Ottens <kevin.ottens@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from dataclasses import dataclass, field
from datetime import timedelta

import factory
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Principal
from faker import Faker
from icalendar import Calendar, Event

from src.akonadi.dav_resource import DAVResource
from src.akonadi.utils import AkonadiUtils

fake = Faker()

_clients: dict[str, Principal | DAVResource] = {}


def set_clients(dav: Principal, akonadi: DAVResource):
    _clients["dav"] = dav
    _clients["akonadi"] = akonadi


@dataclass
class GenericEvent:
    event: Event
    calendar: str

    def to_ical(self) -> bytes:
        cal = Calendar()
        cal.add_component(self.event)
        return cal.to_ical()


@dataclass
class GenericCalendar:
    name: str
    events: list[GenericEvent] = field(default_factory=list)


class BaseEventFactory(factory.Factory):
    class Meta:
        model = GenericEvent
        abstract = True

    uid = factory.Faker("uuid4")
    summary = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    location = factory.Faker("city")

    dtstart = factory.Faker("future_datetime")
    duration_hours = factory.Faker("random_int", min=1, max=8)
    use_dtend = factory.Faker("boolean")

    @factory.lazy_attribute
    def dtend(obj):
        return obj.dtstart + timedelta(hours=obj.duration_hours)

    @factory.lazy_attribute
    def duration(obj):
        return obj.dtend - obj.dtstart

    @classmethod
    def _build(cls, model_class, **kwargs):
        assert "calendar" in kwargs, "Event requires calendar parameter"
        event = Event()
        event.add("uid", kwargs.get("uid"))
        event.add("summary", kwargs.get("summary"))
        event.add("description", kwargs.get("description"))
        event.add("dtstart", kwargs.get("dtstart"))
        if kwargs.get("use_dtend"):
            event.add("dtend", kwargs.get("dtend"))
        else:
            event.add("duration", kwargs.get("duration"))
        return model_class(event=event, calendar=kwargs["calendar"])


class DavEventFactory(BaseEventFactory):
    class Meta:
        model = GenericEvent

    @classmethod
    def _create(cls, model_class, **kwargs):
        event = cls._build(model_class, **kwargs)
        _clients["dav"].calendar(event.calendar).add_event(event.event)
        return event


class AkonadiEventFactory(BaseEventFactory):
    class Meta:
        model = GenericEvent

    @classmethod
    def _create(cls, model_class, **kwargs):
        event = cls._build(model_class, **kwargs)
        collection = kwargs.get("collection") or _clients["akonadi"].collection_from_display_name(
            event.calendar
        )
        _clients["akonadi"].akonadi_client.add_item(
            collection.id(), event.to_ical(), "application/x-vnd.akonadi.calendar.event"
        )
        return event


class BaseCalendarFactory(factory.Factory):
    class Meta:
        model = GenericCalendar
        abstract = True

    nb_items = factory.Faker("random_int", min=1, max=8)
    event_factory: type[BaseEventFactory] | None = None
    name = factory.Faker("word")

    @classmethod
    def _build(cls, model_class, **kwargs):
        calendar = model_class(name=kwargs["name"])
        calendar.events = cls.event_factory.build_batch(
            kwargs.get("nb_items"), calendar=calendar.name
        )
        return calendar


class DavCalendarFactory(BaseCalendarFactory):
    class Meta:
        model = GenericCalendar

    event_factory = DavEventFactory

    @classmethod
    def _create(cls, model_class, **kwargs):
        generic_calendar = cls._build(model_class, **kwargs)
        client = _clients["dav"]
        calendar = client.make_calendar(generic_calendar.name)
        for event in generic_calendar.events:
            calendar.add_event(event.event)
        return generic_calendar


class AkonadiCalendarFactory(BaseCalendarFactory):
    class Meta:
        model = GenericCalendar

    event_factory = AkonadiEventFactory

    @classmethod
    def _create(cls, model_class, **kwargs):
        calendar = cls._build(model_class, **kwargs)
        client = _clients["akonadi"]

        root = client.get_root_collection()
        collection = Akonadi.Collection()
        collection.setName(calendar.name)
        collection.setContentMimeTypes(
            ["inode/directory", "application/x-vnd.akonadi.calendar.event"]
        )
        collection.setParentCollection(root)
        job = Akonadi.CollectionCreateJob(collection)
        AkonadiUtils.wait_for_job(job)
        collection = job.collection()
        for event in calendar.events:
            client.akonadi_client.add_item(
                collection.id(), event.as_bytes(), "message/rfc822"
            )  # TODO mime types
        return calendar
