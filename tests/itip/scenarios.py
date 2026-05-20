# SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path

from jinja2 import StrictUndefined, Template

from src.factories.itip_factory import (
    AkonadiITIPEventFactory,
    GoogleITIPEventFactory,
    ITIPEvent,
    MicrosoftITIPEventFactory,
)


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
        )
        return template.render(iTIP=iTIP)

    @classmethod
    def create_invitation(cls, iTIP: ITIPEvent) -> str:
        return cls._template_file(iTIP, "invitation.ics")

    @classmethod
    def create_invitation_update(cls, iTIP: ITIPEvent) -> str:
        iTIP.increment_sequence()
        return cls._template_file(iTIP, "invitation.ics")

    @classmethod
    def create_recurrence_exception_cancellation(
        cls, eventITIP: ITIPEvent, occurrenceITIP: ITIPEvent
    ) -> tuple[str | None, str | None]:
        """Returns resp. original and recurrence iTIP invitations"""
        if occurrenceITIP.recurrence_id is None:
            raise ValueError("OccurrenceITIP was missing a recurrence_id")
        match eventITIP.provider:
            case AkonadiITIPEventFactory.provider:
                eventITIP.exdate.append(occurrenceITIP.recurrence_id)
                return cls.create_invitation_update(eventITIP), None
            case GoogleITIPEventFactory.provider:
                return None, cls._template_file(occurrenceITIP, "cancellation.ics")
            case MicrosoftITIPEventFactory.provider:
                occurrenceITIP.description = None
                return None, cls._template_file(occurrenceITIP, "cancellation.ics")
            case _:
                raise ValueError(f"Unsupported provider {eventITIP.provider}")
