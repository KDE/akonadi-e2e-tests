# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import pytest

from src.imap.client import Mailbox, MailboxInfo, Message


@pytest.mark.parametrize(
    ("resp", "name", "flags", "delim"),
    [
        pytest.param(
            '(\\HasNoChildren) "." INBOX', "INBOX", ["\\HasNoChildren"], ".", id="INBOX"
        ),
        pytest.param(
            '(\\HasChildren \\UnMarked) "." KDE.bugs',
            "KDE.bugs",
            ["\\HasChildren", "\\UnMarked"],
            ".",
            id="KDE.bugs",
        ),
    ],
)
def test_parse_mailbox(resp: str, name: str, flags: list[str], delim: str):
    mbox = Mailbox.from_list_response(resp)
    assert mbox.name == name
    assert mbox.flags == flags
    assert mbox.delimiter == delim


@pytest.mark.parametrize(
    (
        "resp",
        "flags",
        "perm_flags",
        "exists",
        "recent",
        "unseen",
        "uidvalidity",
        "uidnext",
        "highestmodseq",
        "read_only",
    ),
    [
        pytest.param(
            [
                b"[CLOSED] Previous mailbox closed.",
                b"FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft $label1 $MDNSent $REPLIED receipt-handled $ATTACHMENT $ENCRYPTED $SIGNED $JUNK $FORWARDED $has_cal $TODO $SENT)",
                b"[PERMANENTFLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft $label1 $MDNSent $REPLIED receipt-handled $ATTACHMENT $ENCRYPTED $SIGNED $JUNK $FORWARDED $has_cal $TODO $SENT \\*)] Flags permitted.",
                b"6465 EXISTS",
                b"0 RECENT",
                b"[UNSEEN 5926] First unseen.",
                b"[UIDVALIDITY 1656617207] UIDs valid",
                b"[UIDNEXT 24889] Predicted next UID",
                b"[HIGHESTMODSEQ 44860] Highest",
                b"[READ-WRITE] Select completed (0.005 + 0.000 + 0.004 secs).",
            ],
            [
                "\\Answered",
                "\\Flagged",
                "\\Deleted",
                "\\Seen",
                "\\Draft",
                "$label1",
                "$MDNSent",
                "$REPLIED",
                "receipt-handled",
                "$ATTACHMENT",
                "$ENCRYPTED",
                "$SIGNED",
                "$JUNK",
                "$FORWARDED",
                "$has_cal",
                "$TODO",
                "$SENT",
            ],
            [
                "\\Answered",
                "\\Flagged",
                "\\Deleted",
                "\\Seen",
                "\\Draft",
                "$label1",
                "$MDNSent",
                "$REPLIED",
                "receipt-handled",
                "$ATTACHMENT",
                "$ENCRYPTED",
                "$SIGNED",
                "$JUNK",
                "$FORWARDED",
                "$has_cal",
                "$TODO",
                "$SENT",
                "\\*",
            ],
            6465,
            0,
            5926,
            1656617207,
            24889,
            44860,
            False,
            id="INBOX",
        ),
    ],
)
def test_parse_mailbox_info(
    resp: list[bytes],
    flags: list[str],
    perm_flags: list[str],
    exists: int,
    recent: int,
    unseen: int,
    uidvalidity: int,
    uidnext: int,
    highestmodseq: int | None,
    read_only: bool,
):
    info = MailboxInfo.from_select_response(resp)
    assert info.flags == flags
    assert info.permanent_flags == perm_flags
    assert info.exists == exists
    assert info.recent == recent
    assert info.unseen == unseen
    assert info.uidvalidity == uidvalidity
    assert info.uidnext == uidnext
    assert info.highestmodseq == highestmodseq
    assert info.read_only == read_only


def msg_1_body() -> EmailMessage:
    msg = EmailMessage()
    msg.set_content("Test Message")
    msg["From"] = "test@example.com"
    msg["To"] = "test2.example.com"
    msg["Subject"] = "Test Message"
    msg["Date"] = datetime(2025, 5, 18, 9, 29, 15, tzinfo=timezone(timedelta(hours=2)))
    return msg


@pytest.mark.parametrize(
    (
        "resp",
        "seq",
        "uid",
        "flags",
        "size",
        "internaldate",
        "body",
    ),
    [
        pytest.param(
            [
                b'1 FETCH (UID 6 FLAGS (\\Seen $label1) INTERNALDATE "18-May-2025 09:29:08 +0200" RFC822.SIZE 2348 BODY[] {2348}',
                b'Content-Type: text/plain; charset="utf-8"\r\n'
                b"Content-Transfer-Encoding: 7bit\r\n"
                b"MIME-Version: 1.0\r\n"
                b"From: test@example.com\r\n"
                b"To: test2.example.com\r\n"
                b"Subject: Test Message\r\n"
                b"Date: Sun, 18 May 2025 09:29:15 +0200\r\n"
                b"\r\n"
                b"Test Message\r\n",
                b")",
            ],
            1,
            6,
            ["\\Seen", "$label1"],
            2348,
            datetime(2025, 5, 18, 9, 29, 8, tzinfo=timezone(timedelta(hours=2))),
            msg_1_body(),
            id="message with body",
        ),
        pytest.param(
            [
                b'45643 FETCH (UID 854323 FLAGS (\\Seen) INTERNALDATE "18-May-2025 09:29:08 +0200" RFC822.SIZE 2348)',
            ],
            45643,
            854323,
            ["\\Seen"],
            2348,
            datetime(2025, 5, 18, 9, 29, 8, tzinfo=timezone(timedelta(hours=2))),
            None,
            id="message without body",
        ),
        pytest.param(
            [
                b'1 FETCH (UID 1 FLAGS () INTERNALDATE "18-May-2025 09:29:08 +0200" RFC822.SIZE 2348',
            ],
            1,
            1,
            [],
            2348,
            datetime(2025, 5, 18, 9, 29, 8, tzinfo=timezone(timedelta(hours=2))),
            None,
            id="empty flags",
        ),
    ],
)
def test_parse_message(
    resp: list[bytes],
    seq: int,
    uid: int,
    flags: list[str],
    size: int,
    internaldate: datetime,
    body: EmailMessage | None,
):
    msg = Message.from_fetch_response(resp)
    assert msg.seq == seq
    assert msg.uid == uid
    assert msg.flags == flags
    assert msg.size == size
    assert msg.internaldate == internaldate
    if body is None:
        assert msg.body is None
    else:
        assert msg.body is not None
        assert msg.body.as_string() == body.as_string()
