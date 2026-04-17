# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from logging import getLogger

from imap_tools import BaseMailBox

from src.akonadi.imap_resource import ImapResource
from src.imap.test_utils import assert_collection_equal_mailbox

log = getLogger(__name__)


def test_initial_sync(imap_resource: ImapResource, imap_client: BaseMailBox) -> None:
    assert_collection_equal_mailbox("Test", imap_resource, imap_client)
