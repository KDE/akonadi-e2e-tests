# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import re


def argb_to_rgba(argb_color: str) -> str:
    assert bool(re.fullmatch(r"#[0-9A-Fa-f]{8}", argb_color))
    return f"#{argb_color[3:]}{argb_color[1:3]}"


def rgba_to_argb(rgba_color: str) -> str:
    assert bool(re.fullmatch(r"#[0-9A-Fa-f]{8}", rgba_color))
    return f"#{rgba_color[-2:]}{rgba_color[1:-2]}"
