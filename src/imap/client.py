# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage

from aioimaplib import IMAP4, Response  # type: ignore

from src.imap.email_utils import create_message, parse_message


class ImapError(Exception):
    def __init__(self, resp: Response):
        super().__init__(f"IMAP error: {resp.result}: {resp.lines[0].decode('utf-8')}")


@dataclass
class Mailbox:
    name: str
    flags: list[str]
    delimiter: str

    @classmethod
    def from_list_response(cls, response: str) -> "Mailbox":
        # This is a rather naive parser - its purpose is to be able to parse enough
        # of the response so that we can use it in the tests.
        pos = 0
        flags: list[str] = []
        if response[pos] == "(":
            end = response.find(")", pos)
            flags = response[pos + 1 : end].split(" ")
            pos = end + 1

        while response[pos] == " ":
            pos += 1

        delim = ""
        while response[pos] != " ":
            delim += response[pos]
            pos += 1

        if delim.startswith('"') and delim.endswith('"'):
            delim = delim[1:-1]

        while response[pos] == " ":
            pos += 1

        mailbox_name = response[pos:]

        return cls(
            name=mailbox_name,
            flags=flags,
            delimiter=delim,
        )


@dataclass
class MailboxInfo:
    flags: list[str]
    permanent_flags: list[str]
    exists: int
    recent: int
    unseen: int
    uidvalidity: int
    uidnext: int
    highestmodseq: int | None = None
    read_only: bool = False

    @classmethod
    def from_select_response(cls, response: list[bytes]) -> "MailboxInfo":
        # This is a rather naive and simplistic parser - its purpose is to be able to
        # parse enough of the response so that we can use it in the tests.
        flags: list[str] = []
        permanent_flags: list[str] = []
        exists = 0
        recent = 0
        unseen = 0
        uidvalidity = 0
        uidnext = 0
        highestmodseq = None
        read_only = False

        for line in response:
            if line.endswith(b"EXISTS"):
                exists = int(line.split(b" ")[0])
            elif line.endswith(b"RECENT"):
                recent = int(line.split(b" ")[0])
            elif line.startswith(b"FLAGS"):
                line = line.removeprefix(b"FLAGS (")
                line = line.removesuffix(b")")
                flags = list(map(lambda f: f.decode("utf-8"), line.split(b" ")))
            elif line.startswith(b"[READ-ONLY"):
                read_only = True
            elif line.startswith(b"[PERMANENTFLAGS ("):
                line = line.removeprefix(b"[PERMANENTFLAGS (")
                permanent_flags = list(
                    map(
                        lambda f: f.decode("utf-8"),
                        line[: line.find(b")]")].split(b" "),
                    )
                )
            elif line.startswith(b"[UIDVALIDITY"):
                line = line.removeprefix(b"[UIDVALIDITY ")
                uidvalidity = int(line[: line.find(b"]")])
            elif line.startswith(b"[UIDNEXT"):
                line = line.removeprefix(b"[UIDNEXT ")
                uidnext = int(line[: line.find(b"]")])
            elif line.startswith(b"[HIGHESTMODSEQ"):
                line = line.removeprefix(b"[HIGHESTMODSEQ ")
                highestmodseq = int(line[: line.find(b"]")])
            elif line.startswith(b"[UNSEEN"):
                line = line.removeprefix(b"[UNSEEN ")
                unseen = int(line[: line.find(b"]")])

        return MailboxInfo(
            flags,
            permanent_flags,
            exists,
            recent,
            unseen,
            uidvalidity,
            uidnext,
            highestmodseq,
            read_only,
        )


@dataclass
class Message:
    seq: int
    uid: int
    flags: list[str]
    size: int
    internaldate: datetime

    body: EmailMessage | None = None

    @classmethod
    def from_fetch_response(cls, lines: list[bytes]) -> "Message":
        # This is a rather naive parser - its purpose is to be able to parse enough
        # of the response so that we can use it in the tests.
        response = lines[0]
        if len(lines) > 1:
            response += lines[-1]

        pos = 0
        sep = response.find(b" ")
        seq = int(response[:sep])
        pos = sep + 1
        response = response[pos:].removeprefix(b"FETCH (")
        response = response.removesuffix(b")")

        flags: list[str] = []
        size = 0
        uid = 0
        internaldate: datetime
        body: EmailMessage | None = None
        while True:
            sep = response.find(b" ")
            if sep == -1:
                break
            attr = response[:sep].strip()
            response = response[sep + 1 :].strip()
            if response.startswith(b"("):
                pos = response.find(b")")
                value = response[1:pos].strip()
                response = response[pos + 1 :].strip()
            elif response.startswith(b'"'):
                pos = response.find(b'"', 1)
                value = response[1:pos].strip()
                response = response[pos + 1 :].strip()
            elif response.startswith(b"{"):
                pos = response.find(b"}")
                value = response[1:pos].strip()
                response = response[pos + 1 :].strip()
            else:
                sep = response.find(b" ")
                if sep == -1:
                    sep = len(response)
                value = response[:sep].strip()
                response = response[sep + 1 :].strip()

            if attr == b"FLAGS":
                if value:
                    flags = list(map(lambda f: f.decode("utf-8"), value.split(b" ")))
            elif attr == b"RFC822.SIZE":
                size = int(value)
            elif attr == b"INTERNALDATE":
                internaldate = datetime.strptime(value.decode("utf-8"), "%d-%b-%Y %H:%M:%S %z")
            elif attr == b"UID":
                uid = int(value)
            elif attr == b"BODY[]":
                literal_size = int(value)
                literal = lines[1][0:literal_size]
                body = parse_message(literal)

        return cls(seq, uid, flags, size, internaldate, body)


class ImapClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._client: IMAP4 | None = None

    async def connect(self, username: str, password: str):
        self._client = IMAP4(host=self.host, port=self.port)
        await self._client.wait_hello_from_server()
        await self._client.login(username, password)

    async def disconnect(self):
        if self._client is not None:
            await self._client.logout()

    async def list_mailboxes(self) -> list[Mailbox]:
        assert self._client is not None
        resp = await self._client.list("", "*")
        if resp.result != "OK":
            raise ImapError(resp)

        return [Mailbox.from_list_response(r) for r in resp.data]

    async def select_mailbox(self, mailbox: str) -> MailboxInfo:
        assert self._client is not None
        resp = await self._client.select(mailbox)
        if resp.result != "OK":
            raise ImapError(resp)

        return MailboxInfo.from_select_response(resp.lines)

    async def create_mailbox(self, mailbox: str) -> None:
        assert self._client is not None
        resp = await self._client.create(mailbox)
        if resp.result != "OK":
            raise ImapError(resp)

    async def delete_mailbox(self, mailbox: str) -> None:
        assert self._client is not None
        resp = await self._client.delete(mailbox)
        if resp.result != "OK":
            raise ImapError(resp)

    async def list_messages(self, mailbox: Mailbox | str, with_body: bool = False) -> list[Message]:
        assert self._client is not None
        if isinstance(mailbox, Mailbox):
            mailbox = mailbox.name

        await self.select_mailbox(mailbox)

        parts = ["UID", "FLAGS", "INTERNALDATE", "RFC822.SIZE"]
        if with_body:
            parts.append("BODY.PEEK[]")

        resp = await self._client.fetch("1:*", f"({' '.join(parts)})")
        if resp.result != "OK":
            raise ImapError(resp)

        lines_per_msg = 3 if with_body else 1

        return [
            Message.from_fetch_response(resp.lines[i : i + lines_per_msg])
            for i in range(0, len(resp.lines) - 1, lines_per_msg)
        ]

    async def expunge(self, mailbox: str) -> None:
        assert self._client is not None
        await self.select_mailbox(mailbox)
        resp = await self._client.expunge()
        if resp.result != "OK":
            raise ImapError(resp)

    async def fetch_message(
        self,
        mailbox: str,
        *,
        uid: int | None = None,
        seq: int | None = None,
        with_body: bool = False,
    ) -> Message | None:
        if uid is None and seq is None:
            raise ValueError("Either uid or seq must be provided")

        assert self._client is not None

        await self.select_mailbox(mailbox)

        parts = ["UID", "FLAGS", "INTERNALDATE", "RFC822.SIZE"]
        if with_body:
            parts.append("BODY.PEEK[]")

        if uid is not None:
            resp = await self._client.uid("FETCH", f"{uid}", f"({' '.join(parts)})")
        else:
            resp = await self._client.fetch(f"{seq}", f"({' '.join(parts)})")

        if resp.result != "OK":
            raise ImapError(resp)

        lines = resp.lines[:-1]
        if not lines:
            return None

        return Message.from_fetch_response(lines)

    async def add_flag(self, mailbox: str, uid: int, flag: str) -> None:
        assert self._client is not None
        await self.select_mailbox(mailbox)

        resp = await self._client.uid("STORE", f"{uid}", "+FLAGS", flag)
        if resp.result != "OK":
            raise ImapError(resp)

    async def remove_message(self, mailbox: str, uid: int) -> None:
        assert self._client is not None
        await self.select_mailbox(mailbox)

        resp = await self._client.uid("STORE", f"{uid}", "+FLAGS", "\\Deleted")
        if resp.result != "OK":
            raise ImapError(resp)

        resp = await self._client.expunge()
        if resp.result != "OK":
            raise ImapError(resp)

    async def add_new_message(
        self,
        mailbox: str,
        message: EmailMessage | None = None,
        flags: list[str] | None = None,
    ) -> None:
        assert self._client is not None
        await self.select_mailbox(mailbox)

        if message is None:
            message = create_message()

        resp = await self._client.append(
            message.as_bytes().replace(b"\n", b"\r\n"),
            mailbox,
            flags=" ".join(flags) if flags else None,
        )
        if resp.result != "OK":
            raise ImapError(resp)
