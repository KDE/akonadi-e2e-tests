# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import time
import uuid
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
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

    def prepare_test_environment(self):
        log.info("Populating IMAP server for user %s", self.username)
        client = MailBoxUnencrypted(host=self.host_or_ip, port=self.port)
        client.login(self.username, self.password, initial_folder=None)

        folder_to_create = ["Trash", "Sent", "Templates", "Test", "Test2"]
        for name in folder_to_create:
            client.folder.create(name)
        assert len(client.folder.list()) == len(folder_to_create) + 1, (
            "Failed to create all folders"
        )  # + 1 for INBOX

        for mailbox in ["INBOX", "Test", "Test2"]:
            msg = EmailMessage()
            msg.set_content("Hello, world!\r\n")
            msg["Subject"] = "Test message"
            msg["From"] = "test1@example.com"
            msg["To"] = "test@example.com"
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()
            resp = client.append(
                msg.as_bytes().replace(b"\n", b"\r\n"), mailbox, flag_set=["\\Seen"]
            )
            assert resp[0] == "OK", f"Error from IMAP: {resp}"

            msg = EmailMessage()
            msg.set_content("Hello, world!\r\n")
            msg["Subject"] = "Test message 2"
            msg["From"] = "test2@example.com"
            msg["To"] = "test@example.com"
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()
            resp = client.append(msg.as_bytes().replace(b"\n", b"\r\n"), mailbox)
            assert resp[0] == "OK", f"Error from IMAP: {resp}"

        log.info("IMAP server populated with messages")

        client.logout()

    def cleanup_test_environment(self):
        """
        Currently, aioimaplib does not include a way to list mailboxes at top level (list method does not work with empty string as reference_name, contrary to imaplib2)
        So we just delete every mailbox created in the setup and empty INBOX mailbox of all its messages
        Additional mailboxes created inside of the tests must be deleted at the end of said tests, or added to the list of deleted mailboxes here, to guarantee test isolation

        This could be fixed by using imaplib2 package (and coupling it manually with asyncio) instead of aioimaplib
        """
        log.info("Cleaning IMAP server for user %s", self.username)

        client = MailBoxUnencrypted(host=self.host_or_ip, port=self.port)
        client.login(self.username, self.password, initial_folder="INBOX")

        folder_list = client.folder.list()
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
