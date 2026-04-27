# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from enum import StrEnum


class ITIPAction(StrEnum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    DELEGATED = "delegated"
    COUNTER = "counter"
