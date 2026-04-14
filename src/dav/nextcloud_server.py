# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override

from src.dav.dav_server import DAVServer

log = getLogger(__name__)


class NextCloudServer(DAVServer):
    USERNAME = "test"
    PASSWORD = "testtest"
    DOCKER_IMAGE = "akonadi-e2e-nextcloud:latest"
    CONTAINER_NAME = "nextcloud-akonadi-e2e-tests"
    PORT = 80

    @override
    @property
    def base_url(self) -> str:
        return f"http://{self.host_or_ip}:{self.port}/remote.php/dav"

    @override
    @property
    def readiness_url(self):
        return f"{self.base_url}/calendars/{self.username}/"
