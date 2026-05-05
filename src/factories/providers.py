# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from faker import Faker
from faker.providers import BaseProvider
from PySide6.QtGui import QColor  # type: ignore

fake = Faker()


class QColorProvider(BaseProvider):
    def qcolor(self, use_alpha: bool = False) -> QColor:
        r = fake.pyint(min_value=0, max_value=255)
        g = fake.pyint(min_value=0, max_value=255)
        b = fake.pyint(min_value=0, max_value=255)
        a = fake.pyint(min_value=0, max_value=255)
        return QColor(r, g, b, a if use_alpha else 255)
