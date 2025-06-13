# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from collections.abc import Callable

from caldav.davclient import DAVClient
from caldav.objects import Calendar, Event


async def run_async[T](func: Callable[..., T]) -> T:
    return await asyncio.get_running_loop().run_in_executor(None, func)


class DavClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.client = DAVClient(base_url, username=username, password=password)

    async def list_calendars(self) -> list[Calendar]:
        return await run_async(self.client.principal().calendars)

    async def list_events(self, calendar: Calendar) -> list[Event]:
        return await run_async(calendar.events)
