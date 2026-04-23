# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny LORIN <kenny.lorin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import logging

from caldav.collection import Principal
from caldav.elements import dav
from caldav.elements.ical import CalendarColor

from src.akonadi.dav_resource import DAVResource

from src.dav.test_utils import assert_collection_equal_calendar, get_collection_attributes

log = logging.getLogger("caldav")

def test_add_collection_to_server_is_sync(
        dav_principal: Principal,
        groupware_resource: DAVResource,
) -> None:
    """
    Adding a calendar to the DAV server gets replicated to the akonadi server
    """
    created_calendar = dav_principal.make_calendar(name="SomeCalendar")
    groupware_resource.synchronize()

    assert_collection_equal_calendar(str(created_calendar.url), dav_resource=groupware_resource, dav_principal=dav_principal)


def test_delete_collection_to_server_is_sync(
        dav_principal: Principal,
        groupware_resource: DAVResource,
) -> None:
    """
    Removing a calendar from the DAV server gets deleted from the akonadi server
    """
    created_calendar = dav_principal.make_calendar(name="SomeCalendar")
    groupware_resource.synchronize()
    assert_collection_equal_calendar(str(created_calendar.url), dav_resource=groupware_resource, dav_principal=dav_principal)

    created_calendar.delete()
    groupware_resource.synchronize()

    assert str(created_calendar.url) not in (c.name() for c in groupware_resource.list_collections())
    assert "SomeCalendar" not in (c.displayName() for c in groupware_resource.list_collections())


def test_update_collection_name_on_server_is_sync(
        dav_principal: Principal,
        groupware_resource: DAVResource,
) -> None:
    """
    Changing the display name of a calendar on the DAV server gets updated on the akonadi server
    """
    created_calendar = dav_principal.make_calendar(name="SomeCalendar")
    groupware_resource.synchronize()
    created_calendar.set_properties([dav.DisplayName("some_new_name")])
    updated_calendar = next(c for c in dav_principal.get_calendars() if c.get_display_name() == "some_new_name")
    assert updated_calendar is not None
    assert created_calendar.url == updated_calendar.url
    assert_collection_equal_calendar(str(updated_calendar.url), dav_resource=groupware_resource, dav_principal=dav_principal)


def test_update_collection_color_on_server_is_sync(
        dav_principal: Principal,
        groupware_resource: DAVResource,
) -> None:
    """
    Changing the color of a calendar on the DAV server gets updated on the akonadi server
    """
    new_color_on_server = "#5000ab" # RGB
    new_color_on_resource = "#ff5000ab" # ARGB
    color_attribute_key = "collectioncolor"

    created_calendar = dav_principal.make_calendar(name="SomeCalendar")
    assert created_calendar.get_property(CalendarColor()) is None
    groupware_resource.synchronize()

    attrs = get_collection_attributes(str(created_calendar.url), groupware_resource, dav_principal)
    assert color_attribute_key not in attrs

    created_calendar.set_properties([CalendarColor(new_color_on_server)])
    assert created_calendar.get_property(CalendarColor()) == new_color_on_server
    groupware_resource.synchronize()

    attrs = get_collection_attributes(str(created_calendar.url), groupware_resource, dav_principal)
    assert attrs[color_attribute_key] == new_color_on_resource
