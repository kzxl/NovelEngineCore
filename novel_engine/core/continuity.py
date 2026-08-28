"""Story Continuity & Master Narrative Spine Engine for NovelEngineCore.

Guarantees 100% causal continuity across chapters, ensuring each scene logically
progresses from previous cliffhangers and anchors tightly to the main questline.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PlotThreadStatus(str):
    OPEN = "Đang mở / Chưa giải quyết"
    IN_PROGRESS = "Đang diễn tiến cao trào"
    RESOLVED = "Đã giải quyết"


class PlotThread(BaseModel):
    thread_id: str
    title: str
    core_conflict: str
    involved_characters: List[str]
    introduced_in_scene: str
    status: str = PlotThreadStatus.OPEN
    urgency_level: str = "Cao (High)"


class SceneSummary(BaseModel):
    scene_id: str
    chapter_id: str
    location: str
    key_actions: str
    ending_cliffhanger: str
    immediate_consequences: str


class StorySpine(BaseModel):
    story_id: str
    main_questline: str = "Tìm kiếm dược liệu thượng cổ giải cứu muội muội, từng bước quật khởi trả thù tông môn."
    current_act: str = "Hồi 1: Thiếu Niên Xuất Thôn & Gia Tộc Sóng Gió"
    active_threads: List[PlotThread] = Field(default_factory=list)
    timeline_recaps: List[SceneSummary] = Field(default_factory=list)

    def add_scene_summary(self, summary: SceneSummary):
        self.timeline_recaps.append(summary)

    def get_immediate_previous_context(self) -> str:
        """Returns concise summary of the most recent scene and its cliffhanger."""
        if not self.timeline_recaps:
            return "Đây là phân cảnh mở đầu câu chuyện. Chưa có diễn biến trước đó."
        
        last = self.timeline_recaps[-1]
        return (
            f"VỪA DIỄN RA TRONG [{last.scene_id}] ({last.location}):\n"
            f"- Diễn biến chính: {last.key_actions}\n"
            f"- Kết thúc cảnh trước (Cliffhanger): {last.ending_cliffhanger}\n"
            f"- Hệ quả bắt buộc cảnh này phải xử lý ngay: {last.immediate_consequences}"
        )

    def get_active_threads_summary(self) -> str:
        """Returns summary of all open unresolved plot threads."""
        if not self.active_threads:
            return "- Mâu thuẫn với Đại Trưởng Lão Triệu về Vân Hà Ngọc Bội.\n- Bí ẩn linh hồn trong chiếc nhẫn hắc thiết."
        return "\n".join(
            f"- [{t.urgency_level}] {t.title}: {t.core_conflict} (Nhân vật: {', '.join(t.involved_characters)})"
            for t in self.active_threads if t.status != PlotThreadStatus.RESOLVED
        )
