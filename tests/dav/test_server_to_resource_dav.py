# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-FileCopyrightText: 2026 Kenny LORIN <kenny.lorin@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import logging

from caldav.collection import Principal
from src.akonadi.dav_resource import DAVResource


log = logging.getLogger("caldav")

def test_add_collection_to_server_is_sync(
    dav_principal: Principal, groupware_resource: DAVResource
) -> None:
    calendars = dav_principal.calendars()
    log.error(f"hello {calendars=}")
    # dav_client.calendar(url="http://example.com/some-calendar", parent=None, name="SomeCalendar")