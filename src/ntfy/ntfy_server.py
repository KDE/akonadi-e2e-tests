# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import time
import uuid
from functools import cached_property
from logging import getLogger

from python_ntfy import NtfyClient
from testcontainers.core.container import DockerContainer  # type: ignore

log = getLogger(__name__)


class NtfyServer:
    DOCKER_IMAGE: str = "binwiederhier/ntfy"
    CONTAINER_NAME: str = "ntfy-akonadi-e2e-tests"
    PORT: int = 80

    def __init__(self):
        self.container = None
        self.client = None

    def start(self) -> None:
        log.info(f"Starting {self.__class__.__name__} container")
        # FIXME: This assumes image already exists!
        self.container = (
            DockerContainer(self.DOCKER_IMAGE)
            .with_exposed_ports(self.PORT)
            .with_name(f"{self.CONTAINER_NAME}-{str(uuid.uuid4())[:4]}")
            .with_kwargs(log_config={"type": "journald", "config": {"tag": self.CONTAINER_NAME}})
            .with_command("serve")
        )
        self.container.start()
        self.client = self.wait_ready()

    def stop(self) -> None:
        log.info(f"Stopping {self.__class__.__name__} container")
        if self.container:
            self.container.stop()

    @cached_property
    def host_or_ip(self) -> str:
        return self.container.get_container_host_ip()

    @cached_property
    def port(self) -> int:
        return int(self.container.get_exposed_port(80))

    def set_topic(self, topic: str) -> None:
        self.client.set_topic(topic)

    def get_topic(self) -> str:
        return self.client.get_topic()

    def send_message(self, message: str) -> None:
        self.client.send(message)

    def get_messages(self) -> list[dict]:
        return self.client.get_cached_messages()

    def setup_test(self) -> None:
        self.set_topic("test_topic")

    def wait_ready(self) -> NtfyClient:
        url = f"http://{self.host_or_ip}:{self.port}/"

        for _ in range(100):
            try:
                client = NtfyClient(topic="readiness_topic", server=url)
                client.send("Readiness test message")
                return client
            except Exception:
                time.sleep(0.2)

        raise TimeoutError("ntfy not ready")
