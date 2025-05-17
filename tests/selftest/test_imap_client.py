import pytest
from src.imap.client import MailboxInfo, Mailbox


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
                "[CLOSED] Previous mailbox closed.",
                "FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft $label1 $MDNSent $REPLIED receipt-handled $ATTACHMENT $ENCRYPTED $SIGNED $JUNK $FORWARDED $has_cal $TODO $SENT)",
                "[PERMANENTFLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft $label1 $MDNSent $REPLIED receipt-handled $ATTACHMENT $ENCRYPTED $SIGNED $JUNK $FORWARDED $has_cal $TODO $SENT \\*)] Flags permitted.",
                "6465 EXISTS",
                "0 RECENT",
                "[UNSEEN 5926] First unseen.",
                "[UIDVALIDITY 1656617207] UIDs valid",
                "[UIDNEXT 24889] Predicted next UID",
                "[HIGHESTMODSEQ 44860] Highest",
                "[READ-WRITE] Select completed (0.005 + 0.000 + 0.004 secs).",
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
    resp: list[str],
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
