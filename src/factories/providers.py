# SPDX-FileCopyrightText: 2026 Dominique Michel <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from datetime import UTC

from faker import Faker
from faker.providers import BaseProvider
from PySide6.QtGui import QColor  # type: ignore

fake = Faker()


def generate_byday_value() -> list[str]:
    days = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"]
    length = fake.random_int(min=1, max=3)
    selected = list(fake.random_elements(elements=days, length=length, unique=True))
    # optional positional prefix
    if fake.boolean():
        selected = [f"{fake.random_element([-2, -1, 1, 2])}{d}" for d in selected]
    return selected


class QColorProvider(BaseProvider):
    def qcolor(self, use_alpha: bool = False) -> QColor:
        r = fake.pyint(min_value=0, max_value=255)
        g = fake.pyint(min_value=0, max_value=255)
        b = fake.pyint(min_value=0, max_value=255)
        a = fake.pyint(min_value=0, max_value=255)
        return QColor(r, g, b, a if use_alpha else 255)


class RruleProvider(BaseProvider):
    """
    Generates a dict representing a rrule
    The generated_field argument keys represent the fields that will appear in our rrule
    You can set the value of each field to None to have it randomly generated, or set a value yourself
    """

    def rrule(self, field_list: list[str] | None = None):
        field_list = field_list or []
        fake_dict = {
            "FREQ": fake.random_element(["HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"]),
            "INTERVAL": fake.random_int(min=2, max=30),
            "COUNT": fake.random_int(min=2, max=30),
            "UNTIL": fake.future_datetime().replace(tzinfo=UTC, microsecond=0),
            # MO, being the default value for WKST, is automatically removed from the rrule by the DAV servers
            # To avoid unecessary rrule comparison problems, we remove MO from the list of possible WKST values
            "WKST": fake.random_element(["SU", "TU", "WE", "TH", "FR", "SA"]),
            "BYDAY": generate_byday_value(),
            "BYMONTH": fake.random_elements(list(range(1, 13)), fake.random_int(min=1, max=6)),
            "BYMONTHDAY": fake.random_elements(
                list(range(1, 29)), length=fake.random_int(min=1, max=5)
            ),
            "BYYEARDAY": fake.random_elements(list(range(1, 366)), fake.random_int(min=1, max=5)),
            "BYWEEKNO": fake.random_elements(list(range(1, 52)), fake.random_int(min=1, max=4)),
            "BYSETPOS": fake.random_elements([-3, -2, -1, 1, 2, 3], fake.random_int(min=1, max=3)),
        }

        rrule = {"FREQ": fake_dict["FREQ"]}

        assert not ("COUNT" in field_list and "UNTIL" in field_list)

        by_items = [x for x in field_list if x.startswith("BY") and x != "BYSETPOS"]
        assert len(by_items) <= 1
        assert not ("BYSETPOS" in field_list and len(by_items) == 0)

        for key in field_list:
            rrule[key] = fake_dict[key]

        return rrule
