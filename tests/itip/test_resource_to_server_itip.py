# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from copy import deepcopy
from datetime import datetime, timedelta

from caldav.collection import Principal
from icalendar import PARTSTAT

from src.akonadi.dav_resource import DAVResource
from src.akonadi.itip_handler import ITIPHandler
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.itip.google_factory import GoogleITIPFactory
from src.factories.itip_factory import BaseITIP
from src.itip.const import ITIP_ACTION_ACCEPTED
from src.itip.test_utils import assert_akonadi_item_equal_itip
from src.test import wait_until


def test_itip_invitation_is_added_and_sync(
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation for a new single event is received, an item must be created in a collection (and this is replicated on the server)
    """
    itip: BaseITIP = GoogleITIPFactory.build()
    attendee = itip.get_first_non_organizer_attendee()
    assert attendee
    itip_handler.process_message(attendee.email, itip.to_ical(), ITIP_ACTION_ACCEPTED)
    attendee.partstat = PARTSTAT.ACCEPTED  # We just accepted the invitation

    # An event has been added in resource
    collection = groupware_resource.collection_from_display_name("Default Calendar")
    [item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equal_itip(item, itip)

    # An event has been added in server
    groupware_resource.synchronize()
    wait_until(lambda: len(dav_principal.calendar("Default Calendar").get_events()) == 1)
    assert_all_collections_are_equals(dav_principal, groupware_resource)


def test_itip_existing_invitation_update_is_updated_and_sync(
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
):
    """
    An invitation update for an existing single event is received (several properties to try), the corresponding item must be updated in its collection (and this is replicated on the server)
    """
    itip: BaseITIP = GoogleITIPFactory.build()
    attendee = itip.get_first_non_organizer_attendee()
    assert attendee
    itip_handler.process_message(attendee.email, itip.to_ical(), ITIP_ACTION_ACCEPTED)
    attendee.partstat = PARTSTAT.ACCEPTED

    # An event has been added in resource
    collection = groupware_resource.collection_from_display_name("Default Calendar")
    [original_item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equal_itip(original_item, itip)

    # An event has been added in server
    groupware_resource.synchronize()
    wait_until(lambda: len(dav_principal.calendar("Default Calendar").get_events()) == 1)
    assert_all_collections_are_equals(dav_principal, groupware_resource)

    # Update the invitation
    new_itip = deepcopy(itip)
    new_itip.dtstart = itip.dtstart + timedelta(hours=1)
    new_itip.dtend = itip.dtend + timedelta(hours=2)
    new_itip.location = f"Updated: {itip.location}"
    new_itip.summary = f"Updated: {itip.summary}"
    new_itip.description = f"Updated: {itip.description}"
    new_itip.last_modified_at = datetime.now()
    itip_handler.process_message(attendee.email, itip.to_ical(), ITIP_ACTION_ACCEPTED)

    # Existing event has been updated in resource
    collection = groupware_resource.collection_from_display_name("Default Calendar")
    [new_item] = groupware_resource.list_items(collection.id())
    assert_akonadi_item_equal_itip(new_item, new_itip)

    # Existing event has been updated in server
    groupware_resource.synchronize()
    wait_until(lambda: len(dav_principal.calendar("Default Calendar").get_events()) == 1)
    assert_all_collections_are_equals(dav_principal, groupware_resource)
