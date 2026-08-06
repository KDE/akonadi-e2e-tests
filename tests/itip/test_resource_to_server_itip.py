# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import itertools
from datetime import timedelta
from operator import eq

import pytest
from caldav.collection import Principal
from icalendar.enums import PARTSTAT

from src.akonadi.dav_resource import DAVResource
from src.akonadi.itip_handler import ITIPHandler
from src.dav.test_utils import (
    assert_all_collections_are_equals,
    assert_event_with_recurrence_exception_are_equal,
)
from src.factories.itip_factory import (
    AkonadiITIPEventFactory,
    GoogleITIPEventFactory,
    ITIPEvent,
    ITIPEventFactory,
    MicrosoftITIPEventFactory,
)
from src.itip.const import ITIPAction
from src.itip.test_util import (
    assert_akonadi_item_equals_itip_event,
    event_exists,
    event_sequence_op,
)
from src.test import wait_until
from tests.itip.scenarios import ITIPScenario

default_factories = [
    GoogleITIPEventFactory,
    MicrosoftITIPEventFactory,
    AkonadiITIPEventFactory,
]


@pytest.mark.parametrize("factory", default_factories)
def test_accept_invitation_is_sync(
    factory: ITIPEventFactory,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation for a new single event is received, an item must be created in a collection (and this is replicated on the server)
    """
    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")

    itip: ITIPEvent = factory.build()
    ical = ITIPScenario.create_invitation(itip)
    attendee = itip.get_first_non_organizer_attendee()
    itip_handler.process_message(attendee.email, ical, ITIPAction.ACCEPTED)

    # An event has been added in resource and synchronized on server
    groupware_resource.synchronize()

    attendee.partstat = PARTSTAT.ACCEPTED
    [item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equals_itip_event(item, itip)

    wait_until(lambda: event_exists(dav_calendar, itip.uid))
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.parametrize("factory", default_factories)
def test_update_invitation_is_sync(
    factory: ITIPEventFactory,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for an existing single event is received (several properties to try)
    The corresponding item must be updated in its collection (and this is replicated on the server)
    """
    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")

    itip: ITIPEvent = factory.build()
    ical = ITIPScenario.create_invitation(itip)
    attendee = itip.get_first_non_organizer_attendee()
    itip_handler.process_message(attendee.email, ical, ITIPAction.ACCEPTED)
    groupware_resource.synchronize()
    wait_until(lambda: event_exists(dav_calendar, itip.uid))

    # Create and process an update
    new_itip = factory.create_from(
        itip, reset_fields=["dtstart", "dtend", "summary", "description", "location"]
    )
    new_ical = ITIPScenario.create_invitation_update(new_itip)
    new_attendee = new_itip.get_attendee_by_email(attendee.email)
    itip_handler.process_message(new_attendee.email, new_ical, ITIPAction.ACCEPTED)

    # Event updated in resource and synchronized on server
    groupware_resource.synchronize()

    new_attendee.partstat = PARTSTAT.ACCEPTED
    [new_item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equals_itip_event(new_item, new_itip)

    wait_until(lambda: event_sequence_op(eq, dav_calendar, itip.uid, new_itip.sequence))
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.parametrize("factory", default_factories)
def test_update_invitation_to_recurring_is_sync(
    factory: ITIPEventFactory,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for an existing single event is received, it changes the event to recurring (weekly or otherwise, ideally test several schemes)
    The corresponding item must be updated in its collection (and this is replicated on the server)
    """
    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")

    itip: ITIPEvent = factory.build(rrule=None)
    ical = ITIPScenario.create_invitation(itip)
    attendee = itip.get_first_non_organizer_attendee()
    itip_handler.process_message(attendee.email, ical, ITIPAction.ACCEPTED)
    groupware_resource.synchronize()
    wait_until(lambda: event_exists(dav_calendar, itip.uid))

    # Create and process an update
    new_itip = factory.create_from(itip, reset_fields=["rrule"], use_rrule=True)
    new_ical = ITIPScenario.create_invitation_update(new_itip)
    new_attendee = new_itip.get_attendee_by_email(attendee.email)
    itip_handler.process_message(new_attendee.email, new_ical, ITIPAction.ACCEPTED)

    # Event updated in resource and synchronized on server
    groupware_resource.synchronize()

    new_attendee.partstat = PARTSTAT.ACCEPTED
    [new_item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equals_itip_event(new_item, new_itip)

    wait_until(lambda: event_sequence_op(eq, dav_calendar, itip.uid, new_itip.sequence))
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.parametrize("factory", default_factories)
def test_update_without_invitation_is_sync(
    factory: ITIPEventFactory,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for an existing single event is received (several properties to try) but we didn't create the item yet
    (assuming we didn't receive the initial invitation or it's because we weren't in the initial invitation and part of the update is adding us as participant)
    The corresponding item must be updated in its collection (and this is replicated on the server)
    """
    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")

    # Create and process an update only
    itip: ITIPEvent = factory.build(use_rrule=True)
    new_itip = factory.create_from(
        itip, reset_fields=["dtstart", "dtend", "summary", "description", "location"]
    )
    new_ical = ITIPScenario.create_invitation_update(new_itip)
    new_attendee = new_itip.get_first_non_organizer_attendee()
    itip_handler.process_message(new_attendee.email, new_ical, ITIPAction.ACCEPTED)

    # Event updated in resource and synchronized on server
    groupware_resource.synchronize()

    new_attendee.partstat = PARTSTAT.ACCEPTED
    [new_item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equals_itip_event(new_item, new_itip)

    wait_until(lambda: event_sequence_op(eq, dav_calendar, itip.uid, new_itip.sequence))
    assert_all_collections_are_equals(dav_principal, groupware_resource)


@pytest.mark.parametrize("factory", default_factories)
def test_update_recurring_occurrence_is_sync(
    factory: ITIPEventFactory,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for a recurring event is received, it changes the time of one of the instances of the event
    The corresponding item must be updated in its collection (and this is replicated on the server)
    """
    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")

    itip: ITIPEvent = factory.build(use_rrule=True)
    ical = ITIPScenario.create_invitation(itip)
    attendee = itip.get_first_non_organizer_attendee()
    itip_handler.process_message(attendee.email, ical, ITIPAction.ACCEPTED)
    groupware_resource.synchronize()
    [item] = groupware_resource.list_items(collection.id())
    wait_until(lambda: event_exists(dav_calendar, itip.uid))

    # Create and process an occurrence update
    new_itip = itip.create_exception(1)
    new_itip.add_timedelta(timedelta(hours=2))
    new_ical = ITIPScenario.create_invitation(new_itip)
    new_attendee = new_itip.get_attendee_by_email(attendee.email)
    itip_handler.process_message(new_attendee.email, new_ical, ITIPAction.ACCEPTED)

    # Event updated in resource and synchronized on server

    new_attendee.partstat = PARTSTAT.ACCEPTED
    [new_item] = [i for i in groupware_resource.list_items(collection.id()) if i.id() != item.id()]
    assert_akonadi_item_equals_itip_event(new_item, new_itip)
    groupware_resource.wait_resource_is_idle()

    wait_until(
        lambda: len(dav_calendar.get_event_by_uid(itip.uid).icalendar_instance.walk("VEVENT")) == 2
    )
    assert len(groupware_resource.list_items(collection.id())) == 2
    assert_event_with_recurrence_exception_are_equal(
        dav_calendar.get_event_by_uid(itip.uid).icalendar_instance,
        groupware_resource.list_items(collection.id()),
    )

    # Ensure after a sync event is still there
    groupware_resource.wait_resource_is_idle()
    groupware_resource.synchronize()
    assert len(groupware_resource.list_items(collection.id())) == 2
    assert_event_with_recurrence_exception_are_equal(
        dav_calendar.get_event_by_uid(itip.uid).icalendar_instance,
        groupware_resource.list_items(collection.id()),
    )


@pytest.mark.parametrize("factory", default_factories)
def test_delete_recurring_occurrence_is_sync(
    factory: ITIPEventFactory,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for a recurring event is received, it cancels one of the instances of the event
    The corresponding item must be updated in its collection (and this is replicated on the server)
    """

    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")

    itip: ITIPEvent = factory.build(use_rrule=True)
    ical = ITIPScenario.create_invitation(itip)
    attendee = itip.get_first_non_organizer_attendee()
    itip_handler.process_message(attendee.email, ical, ITIPAction.ACCEPTED)
    groupware_resource.synchronize()
    [item] = groupware_resource.list_items(collection.id())
    wait_until(lambda: event_exists(dav_calendar, itip.uid))

    # Create and process an occurrence deletion
    new_itip = itip.create_exception(1)
    update_ical, new_ical = ITIPScenario.create_recurrence_exception_cancellation(itip, new_itip)
    new_attendee = new_itip.get_attendee_by_email(attendee.email)
    if update_ical:
        itip_handler.process_message(attendee.email, update_ical, ITIPAction.ACCEPTED)
    if new_ical:
        itip_handler.process_message(new_attendee.email, new_ical, ITIPAction.ACCEPTED)

    # Event updated in resource and synchronized on server
    groupware_resource.synchronize()

    if update_ical:
        update_item = groupware_resource.akonadi_client.item_by_id(item.id())
        attendee.partstat = PARTSTAT.ACCEPTED
        assert_akonadi_item_equals_itip_event(update_item, itip)
        wait_until(lambda: event_sequence_op(eq, dav_calendar, itip.uid, itip.sequence))
    if new_ical:
        [new_item] = [
            i for i in groupware_resource.list_items(collection.id()) if i.id() != item.id()
        ]
        new_attendee.partstat = PARTSTAT.ACCEPTED
        assert_akonadi_item_equals_itip_event(new_item, new_itip)
        wait_until(
            lambda: (
                len(dav_calendar.get_event_by_uid(itip.uid).icalendar_instance.walk("VEVENT")) == 2
            )
        )

    if update_ical:
        assert len(groupware_resource.list_items(collection.id())) == 1
    if new_ical:
        assert len(groupware_resource.list_items(collection.id())) == 2
    assert_event_with_recurrence_exception_are_equal(
        dav_calendar.get_event_by_uid(itip.uid).icalendar_instance,
        groupware_resource.list_items(collection.id()),
    )


@pytest.mark.parametrize("factory,rrule_offset", itertools.product(default_factories, [2, -2]))
def test_update_recurring_end_is_sync(
    factory: ITIPEventFactory,
    rrule_offset: int,
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for a recurring event is received, it changes the end of the recurrence (check both postponed and set to an earlier date)
    The corresponding item must be updated in its collection (and this is replicated on the server)
    """
    dav_calendar = dav_principal.calendar("Default Calendar")
    collection = groupware_resource.collection_from_display_name("Default Calendar")
    rrule_count = 10

    itip: ITIPEvent = factory.build(use_rrule=True)
    itip.set_rrule_until_utc(itip.get_occurrence_id(rrule_count))
    ical = ITIPScenario.create_invitation(itip)
    attendee = itip.get_first_non_organizer_attendee()
    itip_handler.process_message(attendee.email, ical, ITIPAction.ACCEPTED)

    groupware_resource.synchronize()
    [item] = groupware_resource.list_items(collection.id())
    attendee.partstat = PARTSTAT.ACCEPTED
    assert_akonadi_item_equals_itip_event(item, itip)
    wait_until(lambda: event_exists(dav_calendar, itip.uid))

    # Create and process a shorter end date update
    new_itip = factory.create_from(itip, reset_fields=["rrule_until"])
    new_itip.set_rrule_until_utc(itip.get_occurrence_id(rrule_count + rrule_offset))
    new_ical = ITIPScenario.create_invitation_update(new_itip)
    itip_handler.process_message(attendee.email, new_ical, ITIPAction.ACCEPTED)

    groupware_resource.synchronize()
    [item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equals_itip_event(item, new_itip)
    wait_until(lambda: event_sequence_op(eq, dav_calendar, itip.uid, new_itip.sequence))

    assert_all_collections_are_equals(dav_principal, groupware_resource)
