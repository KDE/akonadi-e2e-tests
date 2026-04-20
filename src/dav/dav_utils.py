# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import uuid
from datetime import datetime
from icalendar import Event

MESSAGE_IDX_SUFFIX = 0


def create_event(
    day_start: datetime = None, day_end: datetime = None, title: str = None, description: str = None
) -> Event:
    # TODO: check required field
    event = Event()
    event.add("", f"{uuid.uuid4()}")

    if title is not None:
        event.add("SUMMARY", title)
    if day_start is not None:
        event.add("DTSTART", day_start)
    if day_end is not None:
        event.add("DTEND", day_end)
    if description is not None:
        event.add("DESCRIPTION", description)

    return event
