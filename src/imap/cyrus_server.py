# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from imap_tools import BaseMailBox

from src.imap.imap_server import ImapServer

log = getLogger(__name__)


class CyrusServer(ImapServer):
    USERNAME = "admin"
    PASSWORD = "admin"
    DOCKER_IMAGE = "akonadi-e2e-cyrus:latest"
    CONTAINER_NAME = "cyrus-akonadi-e2e-tests"

    def _ready_hook(self, client: BaseMailBox):
        client.folder.create("INBOX")
        assert client.folder.exists("INBOX")
