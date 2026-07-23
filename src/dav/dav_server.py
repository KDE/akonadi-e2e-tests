# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import abc
import uuid
from abc import abstractmethod
from enum import Enum
from functools import cached_property
from logging import getLogger
from typing import ClassVar

import requests
from caldav.davclient import get_davclient
from testcontainers.core.container import DockerContainer  # type: ignore

from src.test import wait_until

log = getLogger(__name__)


class DAVServerType(Enum):
    NEXTCLOUD = "nextcloud"
    RADICALE = "radicale"


class DAVPushNotificationServerType(Enum):
    NEXTCLOUD = "nextcloud-push-notifications"


class DAVServer(abc.ABC):
    DOCKER_IMAGE: ClassVar[str]
    USERNAME: ClassVar[str]
    PASSWORD: ClassVar[str]
    CONTAINER_NAME: ClassVar[str]
    PORT: ClassVar[int]

    def __init__(self):
        self.container = None

    def start(self) -> None:
        log.info(f"Starting {self.__class__.__name__} DAV container")
        # FIXME: This assumes image already exists!
        self.container = (
            DockerContainer(self.DOCKER_IMAGE)
            .with_exposed_ports(self.PORT)
            .with_name(f"{self.CONTAINER_NAME}-{str(uuid.uuid4())[:4]}")
            .with_kwargs(log_config={"type": "journald", "config": {"tag": self.CONTAINER_NAME}})
        )
        self.container.start()

        self.wait_for_server(self.readiness_url)

    def stop(self) -> None:
        log.info(f"Stopping {self.__class__.__name__} container")
        if self.container:
            self.container.stop()

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @property
    @abstractmethod
    def readiness_url(self) -> str: ...

    @cached_property
    def host_or_ip(self) -> str:
        return self.container.get_container_host_ip()

    @cached_property
    def port(self) -> int:
        return self.container.get_exposed_port(self.PORT)

    @property
    def username(self) -> str:
        return self.USERNAME

    @property
    def password(self) -> str:
        return self.PASSWORD

    def wait_for_server(self, url: str):
        def server_is_ready():
            try:
                resp = requests.request(
                    "PROPFIND", url, auth=(self.username, self.password), headers={"Depth": "0"}
                )
                return resp.status_code == 207
            except Exception:
                return False

        wait_until(server_is_ready)

    def cleanup_test_environment(self):
        dav_client = get_davclient(
            url=self.base_url, username=self.username, password=self.password
        )
        dav_principal = dav_client.principal()
        for calendar in dav_principal.calendars():
            if calendar.get_display_name() != "Default Calendar":
                calendar.delete()
            else:
                for event in calendar.get_events():
                    event.delete()
        assert len(dav_principal.calendars()) == 1
        assert len(dav_principal.calendar("Default Calendar").get_events()) == 0
        dav_client.close()
