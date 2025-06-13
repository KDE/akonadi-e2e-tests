# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from abc import abstractmethod
from enum import Enum


class DAVServerType(Enum):
    NEXTCLOUD = "nextcloud"

class DAVServer:
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
    
    @abstractmethod
    @property
    def base_url(self) -> str:
        ...

    @abstractmethod
    @property
    def username(self) -> str:
        ...

    @abstractmethod
    @property
    def password(self) -> str:
        ...