# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path

from jinja2 import StrictUndefined, Template

from src.factories.itip_factory import ITIPEvent


class ITIPScenario:
    """
    Methods will generate one or more iCals for a given scenario to reproduce given ITIP's provider behavior.
    """

    sample_dir = Path(__file__).parent / "template"

    @classmethod
    def _template_file(cls, iTIP: ITIPEvent, file_name: str):
        template_path = cls.sample_dir / iTIP.provider / file_name
        assert template_path.exists()
        template = Template(
            template_path.read_text(),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return template.render(iTIP=iTIP)

    @classmethod
    def create_invitation(cls, iTIP: ITIPEvent) -> str:
        return cls._template_file(iTIP, "invitation.ics")

    @classmethod
    def create_invitation_update(cls, iTIP: ITIPEvent) -> str:
        iTIP.increment_sequence()
        return cls._template_file(iTIP, "invitation.ics")
