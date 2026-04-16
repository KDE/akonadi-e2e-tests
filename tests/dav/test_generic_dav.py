# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from urllib.parse import unquote_plus

from caldav import Principal

from src.akonadi.dav_resource import DAVResource
from src.dav.test_utils import assert_all_collections_are_equals


def test_list_calendars(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    server_calendars = dav_principal.calendars()
    # Skip root collection
    akonadi_calendars = [
        c for c in groupware_resource.list_collections() if c.parentCollection().id() != 0
    ]

    assert len(server_calendars) == len(akonadi_calendars)
    for server_calendar, akonadi_calendar in zip(server_calendars, akonadi_calendars, strict=False):
        assert unquote_plus(str(server_calendar.url)) == akonadi_calendar.name()


def test_initial_sync(dav_principal: Principal, groupware_resource: DAVResource) -> None:
    assert (
        len(groupware_resource.list_collections()) == 5
    )  # parent collection + Default calendar + 3 calendars
    assert len(dav_principal.calendars()) == 4
    assert_all_collections_are_equals(dav_principal, groupware_resource)
