# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import abc
import asyncio
from abc import abstractmethod
from enum import Enum

import aiohttp


class DAVServerType(Enum):
    NEXTCLOUD = "nextcloud"
    RADICALE = "radicale"


class DAVServer(abc.ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @property
    @abstractmethod
    def username(self) -> str: ...

    @property
    @abstractmethod
    def password(self) -> str: ...

    async def wait_for_server(self, url: str):
        deadline = asyncio.get_event_loop().time() + 20

        while True:
            if asyncio.get_event_loop().time() > deadline:
                raise TimeoutError(f"DAV server not responding at {url}")

            try:
                async with (
                    aiohttp.ClientSession(
                        auth=aiohttp.BasicAuth(self.username, self.password)
                    ) as session,
                    session.request(
                        "PROPFIND",
                        url,
                        headers={"Depth": "0"},
                    ) as resp,
                ):
                    if resp.status == 207:
                        return
            except Exception:
                pass

            await asyncio.sleep(0.2)
