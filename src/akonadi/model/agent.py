# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from enum import Enum
from pydantic import BaseModel, ConfigDict, RootModel
from camel_converter import to_camel


class AgentStatus(Enum):
    IDLE = "idle"
    BROKEN = "broken"
    NOT_CONFIGURED = "not-configured"
    RUNNING = "running"


class Agent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    identifier: str
    is_online: bool
    name: str
    status: AgentStatus
    status_message: str
    type: str


ListAgentsResult = RootModel[list[Agent]]
