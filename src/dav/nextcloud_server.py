# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from logging import getLogger
from typing import override

from testcontainers.core.container import DockerContainer  # type: ignore

from src.dav.dav_server import DAVServer

log = getLogger(__name__)


class NextCloudServer(DAVServer):
    container: DockerContainer

    def __init__(self):
        pass

    @override
    async def start(self) -> None:
        log.debug("Starting NextCloud server")
        # FIXME: This assumes image already exists!
        self.container = DockerContainer(
            "akonadi-e2e-nextcloud:latest"
        ).with_exposed_ports(80)
        await asyncio.get_running_loop().run_in_executor(None, self.container.start)
        log.debug(
            "NextCloud server started at %s:%s",
            self.container.get_container_host_ip(),
            self.container.get_exposed_port(80),
        )

    async def stop(self) -> None:
        await asyncio.get_running_loop().run_in_executor(None, self.container.stop)

    @override
    @property
    def base_url(self) -> str:
        host = self.container.get_container_host_ip()
        port = self.container.get_exposed_port(80)

        return f"http://{host}:{port}/remote.php/dav"

    @override
    @property
    def username(self) -> str:
        return "test"

    @override
    @property
    def password(self) -> str:
        return "testtest"
