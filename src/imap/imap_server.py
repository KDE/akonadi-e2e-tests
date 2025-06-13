from abc import abstractmethod
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from enum import Enum
from logging import getLogger

from aioimaplib import IMAP4  # type: ignore

log = getLogger(__name__)

class ImapServerType(Enum):
    CYRUS = "cyrus"


class ImapServer:
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...

    @abstractmethod
    @property
    def port(self) -> int:
        ...

    @abstractmethod
    @property
    def host_or_ip(self) -> str:
        ...

    @abstractmethod
    @property
    def username(self) -> str:
        ...

    @abstractmethod
    @property
    def password(self) -> str:
        ...

    async def prepare_test_environment(self):
        log.info("Populating IMAP server for user %s", self.username)
        imap = IMAP4(host=self.host_or_ip, port=self.port)
        await imap.wait_hello_from_server()
        resp = await imap.login(self.username, self.password)
        assert resp.result == "OK"

        for name in ["INBOX", "Trash", "Sent", "Templates", "Test"]:
            resp = await imap.create(name)
            assert resp.result == "OK"

        for mailbox in ["INBOX", "Test"]:
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