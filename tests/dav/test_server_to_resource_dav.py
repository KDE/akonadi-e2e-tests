# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny LORIN <kenny.lorin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import logging

from caldav.collection import Principal

from src.akonadi.dav_resource import DAVResource

from src.dav.test_utils import assert_collection_equal_calendar

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
