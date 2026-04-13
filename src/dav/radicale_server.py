# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from logging import getLogger
from typing import override

from testcontainers.core.container import DockerContainer  # type: ignore

from src.dav.dav_server import DAVServer

log = getLogger(__name__)


class RadicaleServer(DAVServer):
    container: DockerContainer

    def __init__(self):
        pass

    @override
    async def start(self) -> None:
        log.debug("Starting Radicale server")
        # FIXME: This assumes image already exists!
        self.container = DockerContainer("akonadi-e2e-radicale:latest").with_exposed_ports(5232).with_name("radicale-akonadi-e2e-tests").with_kwargs(
        log_config={
            "type": "journald",
            "config": {
                "tag": "radicale-akonadi-e2e-tests"
            }
        }
        )
        await asyncio.get_running_loop().run_in_executor(None, self.container.start)
        log.debug(
            "Radicale server started at %s:%s",
            self.container.get_container_host_ip(),
            self.container.get_exposed_port(5232),
        )

        await self.wait_for_server(f"{self.base_url}/{self.username}/")

    async def stop(self) -> None:
        log.info("Stopping Radicale container")
        if self.container:
            await asyncio.get_running_loop().run_in_executor(None, self.container.stop)

    @override
    @property
    def base_url(self) -> str:
        host = self.container.get_container_host_ip()
        port = self.container.get_exposed_port(5232)

        return f"http://{host}:{port}"

    @override
    @property
    def username(self) -> str:
        return "test"

    @override
    @property
    def password(self) -> str:
        return "testtest"
