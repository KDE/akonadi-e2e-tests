import asyncio
from testcontainers.core.container import DockerContainer  # type: ignore

from logging import getLogger

log = getLogger(__name__)

class NextCloudServer:
    container: DockerContainer

    def __init__(self):
        pass

    async def start(self) -> None:
        log.debug("Starting NextCloud server")
        # FIXME: This assumes image already exists!
        self.container = DockerContainer(
            "akonadi-e2e-nextcloud:latest"
        ).with_exposed_ports(80)
        await asyncio.get_running_loop().run_in_executor(None, self.container.start)
        log.debug("NextCloud server started at %s:%s", *self.get_host_and_port())

    def get_host_and_port(self) -> tuple[str, int]:
        host = self.container.get_container_host_ip()
        port = self.container.get_exposed_port(80)
        return host, port

    async def stop(self) -> None:
        await asyncio.get_running_loop().run_in_executor(None, self.container.stop)
