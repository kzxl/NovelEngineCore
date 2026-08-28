"""Deterministic Mock Adapter for zero-cost testing, CI, and local demos."""

import json
from typing import Callable, Optional, Type, TypeVar
from pydantic import BaseModel
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import (
    WorldBible,
    PowerTier,
    Faction,
    Location,
    CharacterDossier,
    PersonalityTraits,
    SpeechStyle,
    CharacterStatus,
    InventoryItem,
    ComicStoryboard,
    ComicPanel,
    CameraAngle,
    SceneContract
)

T = TypeVar("T", bound=BaseModel)


class MockLLMAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str = "mock-director-engine"):
        super().__init__(model_name=model_name)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        # Returns a high-quality sample prose in Vietnamese/English
        return (
            "Hoàng hôn đỏ quạch như máu nhuộm đỏ cả khoảng sân của Lâm Gia. "
            "Lâm Phong đứng thẳng người giữa sảnh Nghị Sự, bờ vai phải vẫn còn rỉ máu từ vết thương cũ, "
            "nhưng đôi mắt đen nhánh của chàng lại phẳng lặng như mặt hồ ngàn năm.\n\n"
            "\"Năm trăm linh thạch hạ phẩm, một viên không thiếu!\" – Giọng nói của Lâm Phong vang lên đanh gọn. "
            "Chàng giơ tay, một túi gấm nặng trịch rơi xuống bàn gỗ lim phát ra tiếng 'bộp' giòn giã.\n\n"
            "Phía trên chủ vị, Đại Trưởng Lão Triệu nheo cặp mắt ưng, khóe môi khẽ nhếch lên nụ cười mỉa mai: "
            "\"Lâm Phong, ngươi đùa với lão phu sao? Giá của Vân Hà Ngọc Bội hôm nay... là một ngàn linh thạch!\"\n\n"
            "Sát khí vô hình bỗng chốc tràn ngập cả gian phòng. Lâm Phong không lùi nửa bước, bàn tay trái giấu trong tay áo "
            "khẽ chạm vào chiếc nhẫn hắc thiết, ánh mắt lạnh băng khóa chặt vào gã trưởng lão tham lam."
        )

    async def stream_text(
        self,
        prompt: str,
        on_chunk: Callable[[str], None],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        text = await self.generate_text(prompt, system_prompt, temperature)
        words = text.split(" ")
        for word in words:
            on_chunk(word + " ")
        return text

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> T:
        # Deterministically generate mock instances based on requested model schema
        if response_model.__name__ == "WorldBible":
            return WorldBible(
                world_id="w_canglan",
                title="Thương Lam Giới (Canglan Realm)",
                genre="Xianxia",
                era_setting="Kỷ nguyên Mạt Pháp",
                energy_source="Thiên Địa Linh Khí",
                power_progression=[
                    PowerTier(rank=1, name="Luyện Khí Kỳ", description="Hấp thu linh khí tôi luyện gân cốt", hard_limits="Không thể bay lượn trên không trung"),
                    PowerTier(rank=2, name="Trúc Cơ Kỳ", description="Ngưng tụ linh dịch, thọ mệnh 200 năm", hard_limits="Chưa thể ngưng kết Kim Đan bất tử"),
                    PowerTier(rank=3, name="Kim Đan Kỳ", description="Kim đan bất hoại, ngự kiếm phi hành", hard_limits="Không thể phá toái hư không")
                ],
                canon_rules=[
                    "Phàm nhân không có linh căn vĩnh viễn không thể tu luyện chân khí.",
                    "Linh thạch một khi đã rút cạn năng lượng sẽ hóa thành tro bụi.",
                    "Chênh lệch mỗi một đại cảnh giới là khoảng cách một trời một vực."
                ],
                factions=[
                    Faction(faction_id="fac_lin", name="Lâm Gia", alignment="Trung lập suy tàn", core_doctrine="Bảo vệ gia tộc bằng mọi giá")
                ],
                locations=[
                    Location(location_id="loc_hall", name="Lâm Gia - Hội Nghị Đường", climate_and_vibe="Uy nghiêm, ngột ngạt", key_hazards="Trận pháp áp chế của trưởng lão")
                ]
            )  # type: ignore

        if response_model.__name__ == "ComicStoryboard":
            return ComicStoryboard(
                storyboard_id="sb_ch01_sc01",
                scene_id="SC01",
                chapter_id="CH01",
                panels=[
                    ComicPanel(
                        panel_index=1,
                        camera_angle=CameraAngle.WIDE_SHOT,
                        visual_composition="Góc rộng từ trên cao nhìn xuống sảnh đường Lâm Gia, hoàng hôn đỏ rực chiếu qua ô cửa sổ gỗ, Lâm Phong đứng cô độc đối diện hàng trưởng lão.",
                        active_characters=["Lâm Phong", "Đại Trưởng Lão"],
                        dialogue=[{"Lâm Phong": "Năm trăm linh thạch, một viên không thiếu!"}],
                        sound_effects_sfx="BỘP!",
                        image_prompt_for_ai="Wide cinematic shot, ancient chinese xianxia martial hall, sunset crimson light, young cultivator with black ponytail and ragged blue robes facing intimidating elders on thrones, dynamic lighting, 8k anime artstyle"
                    ),
                    ComicPanel(
                        panel_index=2,
                        camera_angle=CameraAngle.CLOSE_UP,
                        visual_composition="Cận cảnh nụ cười đểu cáng của Đại Trưởng Lão Triệu, ánh mắt thâm độc, tay vuốt chòm râu dê.",
                        active_characters=["Đại Trưởng Lão"],
                        dialogue=[{"Đại Trưởng Lão": "Hôm nay giá là một ngàn linh thạch!"}],
                        sound_effects_sfx="HẮC HẮC...",
                        image_prompt_for_ai="Close up shot of cunning old elder with long grey goatee, sinister smirk, luxurious embroidered silk robes, glowing jade ornaments, intense dramatic rim light, webtoon illustration"
                    ),
                    ComicPanel(
                        panel_index=3,
                        camera_angle=CameraAngle.DUTCH_ANGLE,
                        visual_composition="Góc nghiêng kịch tính đặc tả đôi mắt sắc lẹm của Lâm Phong, tay nắm chặt lại, luồng linh khí mờ ảo bắt đầu dao động quanh ngón tay.",
                        active_characters=["Lâm Phong"],
                        dialogue=[{"Lâm Phong": "..."}],
                        sound_effects_sfx="RẮC!",
                        image_prompt_for_ai="Dutch angle extreme focus on protagonist cold sharp eyes, black hair fluttering, subtle dark spiritual aura rising from iron ring on finger, high tension, manhwa action style"
                    )
                ]
            )  # type: ignore

        raise ValueError(f"Mock for schema {response_model.__name__} not implemented.")
