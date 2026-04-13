# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override

from src.dav.dav_server import DAVServer

log = getLogger(__name__)


class RadicaleServer(DAVServer):
    USERNAME = "test"
    PASSWORD = "testtest"
    DOCKER_IMAGE = "akonadi-e2e-radicale:latest"
    CONTAINER_NAME = "radicale-akonadi-e2e-tests"
    PORT = 5232

    @override
    @property
    def base_url(self) -> str:
        return f"http://{self.host_or_ip}:{self.port}"

    @override
    @property
    def readiness_url(self):
        return f"{self.base_url}/{self.username}/"
