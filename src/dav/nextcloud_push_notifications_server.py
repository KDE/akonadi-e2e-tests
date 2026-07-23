# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override

from src.dav.dav_server import DAVServer
from src.test.docker_utils import get_image_name

log = getLogger(__name__)


class NextCloudPushNotificationsServer(DAVServer):
    USERNAME = "test"
    PASSWORD = "testtest"
    DOCKER_IMAGE = get_image_name("nextcloud-push-notifications")
    CONTAINER_NAME = "nextcloud-push-notifications-akonadi-e2e-tests"
    PORT = 80

    @override
    @property
    def base_url(self) -> str:
        return f"http://{self.host_or_ip}:{self.port}/remote.php/dav"

    @override
    @property
    def readiness_url(self):
        return f"{self.base_url}/calendars/{self.username}/"
