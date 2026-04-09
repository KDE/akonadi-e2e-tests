import asyncio
from logging import getLogger
from typing import override

from aioimaplib import IMAP4  # type: ignore
from testcontainers.core.container import DockerContainer  # type: ignore

from src.imap.imap_server import ImapServer

log = getLogger(__name__)


class DovecotServer(ImapServer):
    # Default user created by the image
    USERNAME = "admin"
    PASSWORD = "admin"

    def __init__(self):
        self.container = None

    @override
    @property
    def host_or_ip(self) -> str:
        return self.container.get_container_host_ip()  # type: ignore

    @override
    @property
    def port(self) -> int:
        return int(self.container.get_exposed_port(143))  # type: ignore

    @override
    @property
    def username(self) -> str:
        return self.USERNAME

    @override
    @property
    def password(self) -> str:
        return self.PASSWORD

    @override
    async def start(self):
        log.info("Starting Dovecot IMAP container")
        # FIXME: This assumes image already exists!
        self.container = DockerContainer("akonadi-e2e-dovecot:latest").with_exposed_ports(143)

        await asyncio.get_running_loop().run_in_executor(None, self.container.start)

        client = await self._wait_ready()

        # DOVECOT image already has INBOX mailbox, so no need to create it manually

        await client.logout()

    @override
    async def stop(self):
        log.info("Stopping Dovecot IMAP container")
        if self.container:
            await asyncio.get_running_loop().run_in_executor(None, self.container.stop)

    async def _wait_ready(self) -> IMAP4:
        # wait until IMAP responds and user can login
        for _ in range(5):
            try:
                client = IMAP4(host=self.host_or_ip, port=self.port)
                # default timeout for the client is 10 seconds
                await client.wait_hello_from_server()
                resp = await client.login(self.username, self.password)
                if resp.result.startswith("OK"):
                    return client
            except Exception:
                await asyncio.sleep(0.5)
        raise TimeoutError("Dovecot IMAP not ready after 50s")
