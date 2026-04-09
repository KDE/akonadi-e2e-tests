# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from abc import abstractmethod
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from enum import Enum
from logging import getLogger

from aioimaplib import IMAP4  # type: ignore

log = getLogger(__name__)


class ImapServerType(Enum):
    CYRUS = "cyrus"
    DOVECOT = "dovecot"


class ImapServer:
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @property
    @abstractmethod
    def port(self) -> int: ...

    @property
    @abstractmethod
    def host_or_ip(self) -> str: ...

    @property
    @abstractmethod
    def username(self) -> str: ...

    @property
    @abstractmethod
    def password(self) -> str: ...

    async def prepare_test_environment(self):
        log.info("Populating IMAP server for user %s", self.username)
        imap = IMAP4(host=self.host_or_ip, port=self.port)
        await imap.wait_hello_from_server()
        resp = await imap.login(self.username, self.password)
        assert resp.result == "OK"

        for name in ["Trash", "Sent", "Templates", "Test", "Test2"]:
            resp = await imap.create(name)
            assert resp.result == "OK"

        for mailbox in ["INBOX", "Test", "Test2"]:
            msg = EmailMessage()
            msg.set_content("Hello, world!\r\n")
            msg["Subject"] = "Test message"
            msg["From"] = "test1@example.com"
            msg["To"] = "test@example.com"
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()
            resp = await imap.append(
                msg.as_bytes().replace(b"\n", b"\r\n"), mailbox, flags="\\Seen"
            )
            assert resp.result == "OK", f"Error from IMAP: {resp.result} {resp.lines}"

            msg = EmailMessage()
            msg.set_content("Hello, world!\r\n")
            msg["Subject"] = "Test message 2"
            msg["From"] = "test2@example.com"
            msg["To"] = "test@example.com"
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()
            resp = await imap.append(msg.as_bytes().replace(b"\n", b"\r\n"), mailbox)
            assert resp.result == "OK", f"Error from IMAP: {resp.result} {resp.lines}"

        log.info("IMAP server populated with messages")

        await imap.logout()

    async def cleanup_test_environment(self):
        """
        Currently, aioimaplib does not include a way to list mailboxes at top level (list method does not work with empty string as reference_name, contrary to imaplib2)
        So we just delete every mailbox created in the setup and empty INBOX mailbox of all its messages
        Additional mailboxes created inside of the tests must be deleted at the end of said tests, or added to the list of deleted mailboxes here, to guarantee test isolation

        This could be fixed by using imaplib2 package (and coupling it manually with asyncio) instead of aioimaplib
        """
        log.info("Cleaning IMAP server for user %s", self.username)

        imap = IMAP4(host=self.host_or_ip, port=self.port)
        await imap.wait_hello_from_server()

        resp = await imap.login(self.username, self.password)
        assert resp.result == "OK"
        resp = await imap.select()
        assert resp.result == "OK"

        for name in ["Trash", "Sent", "Templates", "Test", "Test2", "Test3"]:
            # check that the mailbox exists:
            resp = await imap.status(name, "(MESSAGES)")
            if resp.result == "OK":
                deleted = False
                # delete might fail at first if some operations are still ongoing, so we try serveral time
                for _ in range(5):
                    resp = await imap.delete(name)
                    if resp.result == "OK":
                        deleted = True
                        break
                    await asyncio.sleep(0.2)
                assert deleted

        # We can't delete INBOX mailbox, we have to empty its messages ourselves
        resp = await imap.search("ALL")
        if resp.result == "OK" and resp.lines and resp.lines[0]:
            msg_ids = resp.lines[0].decode().strip().split()

            if msg_ids and len(msg_ids) > 0:
                for num in msg_ids:
                    resp = await imap.store(num, "+FLAGS", "(\\Deleted)")
                    assert resp.result == "OK"

                resp = await imap.expunge()
                assert resp.result == "OK"

        await imap.logout()

        log.info("IMAP server cleanup complete")
