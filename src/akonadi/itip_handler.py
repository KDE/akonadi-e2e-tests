# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from AkonadiCalendar import Akonadi as AkonadiCal  # type: ignore

from src.itip.utils import ITIPUtils

log = getLogger(__name__)


class ITIPHandler:
    handler: AkonadiCal.ITIPHandler

    def __init__(self) -> None:
        self.handler = AkonadiCal.ITIPHandler()
        self.handler.setShowDialogsOnError(False)

    def process_message(self, receiver: str, ical: str, action: str) -> None:
        ITIPUtils.itip_process_message(self.handler, receiver, ical, action)
