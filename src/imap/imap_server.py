# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import time
import uuid
from enum import Enum
from functools import cached_property
from logging import getLogger
from typing import ClassVar

from imap_tools import BaseMailBox, MailboxFolderDeleteError, MailBoxUnencrypted
from testcontainers.core.container import DockerContainer  # type: ignore

log = getLogger(__name__)


class ImapServerType(Enum):
    CYRUS = "cyrus"
    DOVECOT = "dovecot"


class ImapServer:
    DOCKER_IMAGE: ClassVar[str]
    USERNAME: ClassVar[str]
    PASSWORD: ClassVar[str]
    CONTAINER_NAME: ClassVar[str]

    def __init__(self):
        self.container = None

    def start(self) -> None:
        log.info(f"Starting {self.__class__.__name__} IMAP container")
        # FIXME: This assumes image already exists!
        self.container = (
            DockerContainer(self.DOCKER_IMAGE)
            .with_exposed_ports(143)
            .with_name(f"{self.CONTAINER_NAME}-{str(uuid.uuid4())[:4]}")
            .with_kwargs(log_config={"type": "journald", "config": {"tag": self.CONTAINER_NAME}})
        )
        self.container.start()

        client = self._wait_ready()
        self._ready_hook(client)
        client.logout()

    def stop(self):
        log.info(f"Stopping {self.__class__.__name__} container")
        if self.container:
            self.container.stop()

    @cached_property
    def host_or_ip(self) -> str:
        return self.container.get_container_host_ip()

    @cached_property
    def port(self) -> int:
        return int(self.container.get_exposed_port(143))

    @property
    def username(self) -> str:
        return self.USERNAME

    @property
    def password(self) -> str:
        return self.PASSWORD

    def cleanup_test_environment(self):
        """
        Some IMAP servers don't allow deleting the INBOX mailbox or deleting mailboxes containing other mailboxes.
        To circumvent this, we only empty the INBOX mailbox of it's messages and delete child mailboxes first.
        """
        log.info("Cleaning IMAP server for user %s", self.username)

        client = MailBoxUnencrypted(host=self.host_or_ip, port=self.port)
        client.login(self.username, self.password, initial_folder="INBOX")

        folder_list = client.folder.list()
        # Some IMAP servers require to delete child mailboxes first
        folder_list.sort(key=lambda f: len(f.name.split(f.delim)), reverse=True)
        for folder in folder_list:
            if folder.name == "INBOX":
                continue
            deleted = False
            # delete might fail at first if some operations are still ongoing, so we try serveral time
            for _ in range(5):
                try:
                    client.folder.delete(folder.name)
                    deleted = True
                    break
                except MailboxFolderDeleteError:
                    time.sleep(0.2)
            assert deleted

        # We can't delete INBOX mailbox, we have to empty its messages ourselves
        uids = client.uids("ALL")
        client.delete(uids)
        assert len(client.uids("ALL")) == 0
        client.logout()

        log.info("IMAP server cleanup complete")

    def _ready_hook(self, client: BaseMailBox):
        pass

    def _wait_ready(self) -> BaseMailBox:
        # wait until IMAP responds and user can login
        for _ in range(100):
            try:
                client = MailBoxUnencrypted(host=self.host_or_ip, port=self.port)
                client.login(self.username, self.password, initial_folder=None)
                return client
            except Exception:
                time.sleep(0.2)
        raise TimeoutError(f"{self.__class__.__name__} not ready after 20s")
