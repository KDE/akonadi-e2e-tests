# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import uuid
from datetime import datetime
from email.message import EmailMessage
from email.parser import BytesParser

MESSAGE_IDX_SUFFIX = 0


def create_message(subject: str | None = None, body: str | None = None) -> EmailMessage:
    message = EmailMessage()

    if body is None:
        # Use globally unique counter to ensure each message body is unique
        global MESSAGE_IDX_SUFFIX  # pylint: disable=global-statement
        MESSAGE_IDX_SUFFIX += 1
        suffix = "*" * MESSAGE_IDX_SUFFIX
        body = "Test message\r\nRandom suffix: " + suffix

    message.set_content(body)
    message["From"] = "test2@example.com"
    message["To"] = "test@example.com"
    message["Subject"] = subject or f"Test message {MESSAGE_IDX_SUFFIX}"
    message["Date"] = datetime.now().isoformat()
    message["Message-ID"] = f"<{uuid.uuid4()}@localhost>"

    return message


def parse_message(data: bytes) -> EmailMessage:
    return BytesParser(EmailMessage).parsebytes(data)
