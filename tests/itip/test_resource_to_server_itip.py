# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import pytest
from caldav.collection import Principal
from icalendar import PARTSTAT

from src.akonadi.dav_resource import DAVResource
from src.akonadi.itip_handler import ITIPHandler
from src.dav.test_utils import assert_all_collections_are_equals
from src.factories.itip.google_factory import GoogleITIPFactory
from src.factories.itip.microsoft_factory import MicrosoftITIPFactory
from src.factories.itip_factory import BaseITIP, BaseITIPFactory
from src.itip.const import ITIP_ACTION_ACCEPTED
from src.itip.test_utils import assert_akonadi_item_equal_itip
from src.test import wait_until


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(GoogleITIPFactory, id="google"),
        pytest.param(
            MicrosoftITIPFactory,
            marks=pytest.mark.xfail(
                reason="Akonadi bug? Radicale all data after comma is lost when syncing to server. https://invent.kde.org/pim/pim-technical-roadmap/-/work_items/99"
            ),
            id="microsoft",
        ),
    ],
)
def test_itip_invitation_is_added_and_sync(
    itip_handler: ITIPHandler,
    dav_principal: Principal,
    groupware_resource: DAVResource,
    factory: BaseITIPFactory,
):
    """
    An invitation for a new single event is received, an item must be created in a collection (and this is replicated on the server)
    """
    itip: BaseITIP = factory.build()
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
