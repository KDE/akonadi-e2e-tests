from dataclasses import dataclass

from aioimaplib import IMAP4, Response  # type: ignore


class ImapError(Exception):
    def __init__(self, resp: Response):
        super().__init__(f"IMAP error: {resp.result}: {resp.lines[0].encode('utf-8')}")


@dataclass
class Mailbox:
    name: str
    flags: list[str]
    delimiter: str

    @classmethod
    def from_list_response(cls, response: str) -> "Mailbox":
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
    def from_select_response(cls, response: list[str]) -> "MailboxInfo":
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
            if line.endswith("EXISTS"):
                exists = int(line.split(" ")[0])
            elif line.endswith("RECENT"):
                recent = int(line.split(" ")[0])
            elif line.startswith("FLAGS"):
                line = line.removeprefix("FLAGS (")
                line = line.removesuffix(")")
                flags = line.split(" ")
            elif line.startswith("[READ-ONLY"):
                read_only = True
            elif line.startswith("[PERMANENTFLAGS ("):
                line = line.removeprefix("[PERMANENTFLAGS (")
                permanent_flags = line[: line.find(")]")].split(" ")
            elif line.startswith("[UIDVALIDITY"):
                line = line.removeprefix("[UIDVALIDITY ")
                uidvalidity = int(line[: line.find("]")])
            elif line.startswith("[UIDNEXT"):
                line = line.removeprefix("[UIDNEXT ")
                uidnext = int(line[: line.find("]")])
            elif line.startswith("[HIGHESTMODSEQ"):
                line = line.removeprefix("[HIGHESTMODSEQ ")
                highestmodseq = int(line[: line.find("]")])
            elif line.startswith("[UNSEEN"):
                line = line.removeprefix("[UNSEEN ")
                unseen = int(line[: line.find("]")])

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
        if resp.code != "OK":
            raise ImapError(resp)

        return [Mailbox.from_list_response(r) for r in resp.data]

    async def select_mailbox(self, mailbox: str) -> MailboxInfo:
        assert self._client is not None
        resp = await self._client.select(mailbox)
        if resp.code != "OK":
            raise ImapError(resp)

        return MailboxInfo.from_select_response(resp.lines)
