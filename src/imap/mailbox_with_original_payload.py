# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import email

from imap_tools import MailBoxUnencrypted, MailMessage


class MailMessageWithOriginalPayload(MailMessage):
    def __init__(self, fetch_data: list) -> None:
        raw_message_data, raw_uid_data, raw_flag_data = self._get_message_data_parts(fetch_data)
        self.raw_message_data = raw_message_data
        self._raw_uid_data = raw_uid_data
        self._raw_flag_data = raw_flag_data
        self.obj = email.message_from_bytes(raw_message_data)


class MailBoxUnencryptedWithOriginalPayload(MailBoxUnencrypted):
    email_message_class = MailMessageWithOriginalPayload
    delimiter: str
