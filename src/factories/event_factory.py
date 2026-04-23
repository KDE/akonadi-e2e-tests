# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Kevin Ottens <kevin.ottens@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from dataclasses import dataclass, field
from datetime import timedelta
from typing import TypedDict

import factory
from AkonadiCore import Akonadi  # type: ignore
from caldav.collection import Principal
from caldav.elements import ical
from faker import Faker
from icalendar import Calendar, Event
from PySide6.QtGui import QColor  # type: ignore

from src.akonadi.dav_resource import DAVResource
from src.akonadi.utils import AkonadiUtils
from src.factories.providers import HexArgbProvider

fake = Faker()
fake.add_provider(HexArgbProvider)


class _Clients(TypedDict):
    dav: Principal
    akonadi: DAVResource


_clients: _Clients = {}  #  type: ignore[typeddict-item]


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

    def save_to_akonadi(self, collection: Akonadi.Collection | None):
        collection = collection or _clients["akonadi"].collection_from_display_name(self.calendar)
        _clients["akonadi"].akonadi_client.add_item(
            collection.id(), self.to_ical(), "application/x-vnd.akonadi.calendar.event"
        )

    def save_to_dav_server(self):
        _clients["dav"].calendar(self.calendar).add_event(self.event)


@dataclass
class GenericCalendar:
    name: str
    color: str
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
        event.save_to_dav_server()
        return event


class AkonadiEventFactory(BaseEventFactory):
    class Meta:
        model = GenericEvent

    @classmethod
    def _create(cls, model_class, **kwargs):
        event = cls._build(model_class, **kwargs)
        event.save_to_akonadi(kwargs.get("collection"))
        return event


class BaseCalendarFactory(factory.Factory):
    class Meta:
        model = GenericCalendar
        abstract = True

    nb_items = factory.Faker("random_int", min=1, max=8)
    event_factory: type[BaseEventFactory] | None = None
    name = factory.Faker("word")
    color = factory.LazyFunction(fake.hex_argb)

    @classmethod
    def _build(cls, model_class, **kwargs):
        calendar = model_class(name=kwargs["name"], color=kwargs.get("color"))
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
        calendar.set_properties([ical.CalendarColor(generic_calendar.color)])
        for event in generic_calendar.events:
            event.save_to_dav_server()
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
        attr = Akonadi.CollectionColorAttribute()
        attr.setColor(QColor.fromString(calendar.color))
        collection.addAttribute(attr.clone())  # clone to give an unmanaged object
        job = Akonadi.CollectionCreateJob(collection)
        AkonadiUtils.wait_for_job(job)
        collection = job.collection()
        for event in calendar.events:
            event.save_to_akonadi(collection)
        return calendar
