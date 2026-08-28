"""Dynamic World & Plot Events Engine for NovelEngineCore.

Generates logically interconnected story events, plot twists, and faction crises
derived from character motives, hidden secrets, and world canon laws.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EventSeverity(str, Enum):
    MINOR = "Tiểu Biến Cố (Minor Conflict)"
    MAJOR = "Đại Sự Kiện (Major Crisis)"
    CALAMITY = "Thiên Địa Dị Biến / Đại Họa (Calamity)"


class PlotEvent(BaseModel):
    event_id: str
    title: str
    severity: EventSeverity
    category: str = "Tông Môn Tranh Đấu"
    trigger_cause: str
    involved_characters: List[str] = Field(default_factory=list)
    location: str
    impact_summary: str
    suggested_scene_goal: str
    suggested_conflict: str
    suggested_cliffhanger: str


class GeneratedEventList(BaseModel):
    events: List[PlotEvent] = Field(default_factory=list)
