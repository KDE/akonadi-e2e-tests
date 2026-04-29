# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from faker import Faker
from faker.providers import BaseProvider

fake = Faker()


class HexArgbProvider(BaseProvider):
    def hex_rgba(self):
        r = fake.pyint(min_value=0, max_value=255)
        g = fake.pyint(min_value=0, max_value=255)
        b = fake.pyint(min_value=0, max_value=255)
        a = fake.pyint(min_value=0, max_value=255)
        return f"#{r:02X}{g:02X}{b:02X}{a:02X}".lower()
