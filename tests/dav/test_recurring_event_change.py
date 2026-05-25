# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import copy
from datetime import timedelta

import pytest
from caldav.collection import Principal
from icalendar import Calendar, vDDDTypes

from src.akonadi.dav_resource import DAVResource
from src.dav.test_utils import assert_event_with_recurrence_exception_are_equal
from src.factories.event_factory import DavCalendarFactory, DavEventFactory


class RecurringEventHelper:
    def __init__(self, calendar_name: str, principal: Principal):
        self.calendar_name = calendar_name
        self.principal = principal
        self.calendar = Calendar()
        self.event = DavEventFactory.build(
            calendar=calendar_name, use_rrule=True, rrule={"FREQ": "DAILY"}
        ).event
        self.calendar.add_component(self.event)

    def add_exception(self, occurence_nth: int, delta_hours: int):
        exception = copy.copy(self.event)
        recurrence_id = copy.copy(self.event["DTSTART"])
        recurrence_id.dt += timedelta(hours=occurence_nth)
        exception["RECURRENCE-ID"] = recurrence_id
        exception.start += timedelta(hours=delta_hours)
        exception.end += timedelta(hours=delta_hours)
        exception.summary = f"Exception - {delta_hours} hours"
        exception["SEQUENCE"] = 1
        del exception["RRULE"]
        self.calendar.add_component(exception)
        return exception

    def delete_exception(self, recurrence_id: vDDDTypes):
        """Delete an exception by its recurrence ID. And add an exdate to the original event."""
        [exception] = [
            e for e in self.calendar.subcomponents if e.get("RECURRENCE-ID") == recurrence_id
        ]
        self.calendar.subcomponents.remove(exception)
        self.event["EXDATE"] = recurrence_id
        self.event["SEQUENCE"] = self.event.get("SEQUENCE", 0) + 1

    def modify_exception(self, recurrence_id: vDDDTypes, delta_hours: int):
        [exception] = [
            e for e in self.calendar.subcomponents if e.get("RECURRENCE-ID") == recurrence_id
        ]
        exception.start += timedelta(hours=delta_hours)
        exception.end += timedelta(hours=delta_hours)
        exception.summary = f"Exception - {delta_hours} hours"
        exception["SEQUENCE"] += 1

    def to_ical(self):
        return self.calendar.to_ical()

    def save(self):
        self.principal.calendar(self.calendar_name).save_event(self.to_ical())


@pytest.mark.xfail(
    reason="dav resource bug, event exception are deleted when resource have another change https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/137",
    strict=True,
)
def test_adding_exception_to_event_and_add_unrelated_event_to_calendar(
    dav_principal: Principal, groupware_resource: DAVResource
):
    """Test adding an exception to an event and add an unrelated event to the calendar, after sync we expect the exception to be still there."""
    calendar = DavCalendarFactory.create(nb_items=0)
    event_helper = RecurringEventHelper(calendar.name, dav_principal)
    event_helper.add_exception(occurence_nth=1, delta_hours=1)
    event_helper.save()

    groupware_resource.synchronize()
    collection = groupware_resource.collection_from_display_name(calendar.name)

    akonadi_items = groupware_resource.list_items(collection.id())
    akonadi_items_ids = [i.id() for i in akonadi_items]
    assert len(akonadi_items) == 2
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)

    DavEventFactory.create(calendar=calendar.name)
    groupware_resource.synchronize()

    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 3
    items_related_to_recurrence = [i for i in akonadi_items if i.id() in akonadi_items_ids]
    assert len(items_related_to_recurrence) == 2
    assert_event_with_recurrence_exception_are_equal(
        event_helper.calendar, items_related_to_recurrence
    )


@pytest.mark.xfail(
    reason="dav resource bug, event first exception is deleted when syncing another exception to the same event https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/137",
    strict=True,
)
def test_adding_exception_to_event_with_exception(
    dav_principal: Principal, groupware_resource: DAVResource
):
    """Test adding an exception to an event with an exception. Expecting the event to have 2 exceptions on the resource."""
    calendar = DavCalendarFactory.create(nb_items=0)
    event_helper = RecurringEventHelper(calendar.name, dav_principal)
    event_helper.add_exception(occurence_nth=1, delta_hours=1)
    event_helper.save()

    groupware_resource.synchronize()
    collection = groupware_resource.collection_from_display_name(calendar.name)

    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 2
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)

    event_helper.add_exception(occurence_nth=2, delta_hours=2)
    event_helper.save()
    groupware_resource.synchronize()
    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 3
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)


def test_modifying_exception_to_event_with_exception(
    dav_principal: Principal, groupware_resource: DAVResource
):
    """Test modification of an exception server-side. Expecting the exception to be modified too on the resource."""
    calendar = DavCalendarFactory.create(nb_items=0)
    event_helper = RecurringEventHelper(calendar.name, dav_principal)
    exception = event_helper.add_exception(occurence_nth=1, delta_hours=1)
    event_helper.save()
    groupware_resource.synchronize()
    collection = groupware_resource.collection_from_display_name(calendar.name)

    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 2
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)

    event_helper.modify_exception(recurrence_id=exception["RECURRENCE-ID"], delta_hours=6)
    event_helper.save()
    groupware_resource.synchronize()

    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 2
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)


@pytest.mark.xfail(
    reason="dav resource bug, exception are not deleted https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/137",
    strict=True,
)
def test_deleting_exception_to_event_with_exception(
    dav_principal: Principal, groupware_resource: DAVResource
):
    """Test deletion of an exception server-side. Expecting the exception to be deleted too on the resource."""
    calendar = DavCalendarFactory.create(nb_items=0)
    event_helper = RecurringEventHelper(calendar.name, dav_principal)
    exception = event_helper.add_exception(occurence_nth=1, delta_hours=1)
    event_helper.save()
    groupware_resource.synchronize()
    collection = groupware_resource.collection_from_display_name(calendar.name)
    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 2
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)
    print(type(exception["RECURRENCE-ID"]))
    event_helper.delete_exception(recurrence_id=exception["RECURRENCE-ID"])
    event_helper.save()
    groupware_resource.synchronize()

    akonadi_items = groupware_resource.list_items(collection.id())
    assert len(akonadi_items) == 1
    assert_event_with_recurrence_exception_are_equal(event_helper.calendar, akonadi_items)
