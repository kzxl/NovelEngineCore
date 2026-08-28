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
    CharacterRole,
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
        name = response_model.__name__

        if name == "WorldBible":
            return WorldBible(
                world_id="w_canglan",
                title="Thương Lam Giới (Canglan Realm)",
                genre="Xianxia",
                era_setting="Kỷ nguyên Mạt Pháp Vạn Năm",
                energy_source="Thiên Địa Linh Khí & Cổ Ma Khí",
                power_progression=[
                    PowerTier(rank=1, name="Luyện Khí Kỳ", description="Hấp thu linh khí tôi luyện kinh mạch gân cốt", hard_limits="Không thể phi hành trên không"),
                    PowerTier(rank=2, name="Trúc Cơ Kỳ", description="Linh khí hóa dịch thể, thọ mệnh 200 năm", hard_limits="Chưa thể ngưng kết Kim Đan bất hoại"),
                    PowerTier(rank=3, name="Kim Đan Kỳ", description="Kim đan bất toái, ngự kiếm phi hành ngàn dặm", hard_limits="Chưa thể xuất hồn đoạt xá"),
                    PowerTier(rank=4, name="Nguyên Anh Kỳ", description="Nguyên anh xuất khiếu, dời non lấp biển", hard_limits="Không thể phá toái hư không")
                ],
                canon_rules=[
                    "Phàm nhân không có linh căn vĩnh viễn không thể hấp thu linh khí.",
                    "Linh thạch một khi đã rút cạn năng lượng sẽ tự động hóa thành cát bụi vô dụng.",
                    "Chênh lệch mỗi một đại cảnh giới là khoảng cách hồng hào không thể bù đắp bằng số lượng.",
                    "Cổ Ma Khí sẽ ăn mòn thần trí của bất kỳ tu sĩ nào chưa đạt Nguyên Anh."
                ],
                factions=[
                    Faction(faction_id="fac_lin", name="Lâm Gia", alignment="Trung lập suy tàn", core_doctrine="Bảo tồn gia tộc huyết mạch"),
                    Faction(faction_id="fac_trieu", name="Triệu Thị Gia Tộc", alignment="Phản diện bành trướng", core_doctrine="Thôn tính các gia tộc nhỏ yếu"),
                    Faction(faction_id="fac_van", name="Vân Lam Kiếm Tông", alignment="Chính đạo bá chủ", core_doctrine="Chưởng quản kiếm đạo phương bắc")
                ],
                locations=[
                    Location(location_id="loc_hall", name="Lâm Gia - Hội Nghị Đường", climate_and_vibe="Uy nghiêm, ngột ngạt, vương mùi trầm hương", key_hazards="Trận pháp áp chế tu vi của Trưởng lão"),
                    Location(location_id="loc_forest", name="Hắc Ám Sâm Lâm", climate_and_vibe="Mù mịt chướng khí, đêm tối vĩnh hằng", key_hazards="Yêu thú bậc 3 và bẫy độc tự nhiên"),
                    Location(location_id="loc_peak", name="Thiên Kiếm Phong", climate_and_vibe="Băng hàn thấu xương, mây mù bao phủ", key_hazards="Kiếm khí tàn lưu từ thời thượng cổ")
                ]
            )  # type: ignore

        if name == "GeneratedCharacterList":
            from novel_engine.engine import GeneratedCharacterList
            return GeneratedCharacterList(
                characters=[
                    CharacterDossier(
                        character_id="char_lin_feng",
                        name="Lâm Phong",
                        role=CharacterRole.PROTAGONIST,
                        visual_tags=["young male 18yo", "long black hair in high ponytail", "sharp piercing obsidian eyes", "tattered blue cultivator robe", "slender lean build", "silver ancient ring on thumb"],
                        personality=PersonalityTraits(
                            core_motivation="Bảo vệ muội muội Lâm Tuyết và rửa sạch mối oan cho gia phụ",
                            fatal_flaw="Cố chấp, cực kỳ đa nghi và ít tin tưởng người ngoài",
                            moral_boundary="Tuyệt đối không ra tay với phàm nhân vô tội",
                            hidden_secret="Đang chứa chấp tàn hồn Dược Lão vạn năm trong nhẫn hắc thiết"
                        ),
                        speech=SpeechStyle(vocabulary_level="Đanh thép, dứt khoát, kiệm lời"),
                        status=CharacterStatus(power_tier="Luyện Khí Tầng 3", health_condition="Bị thương vai phải do ám tiễn", mental_state="Lạnh lùng cảnh giác"),
                        inventory=[InventoryItem(item_id="item_ring", name="Hắc Thiết Nhẫn"), InventoryItem(item_id="item_pouch", name="Túi Trữ Vật 500 Linh Thạch")]
                    ),
                    CharacterDossier(
                        character_id="char_elder_zhao",
                        name="Đại Trưởng Lão Triệu Bá",
                        role=CharacterRole.ANTAGONIST,
                        visual_tags=["old male 65yo", "long grey goatee", "sinister cunning eyes", "luxurious crimson silk robes", "emerald jade thumb ring", "cruel arrogant smirk"],
                        personality=PersonalityTraits(
                            core_motivation="Thâu tóm toàn bộ gia sản Lâm Gia để mua Trúc Cơ Đan cho con trai",
                            fatal_flaw="Tham lam vô độ và khinh địch tột cùng",
                            moral_boundary="Không từ thủ đoạn để đạt được lợi ích",
                            hidden_secret="Đã ngầm cấu kết với Ma Tu Hắc Ma Môn"
                        ),
                        speech=SpeechStyle(vocabulary_level="Quan cách, mỉa mai, trịch thượng"),
                        status=CharacterStatus(power_tier="Luyện Khí Tầng 9 (Bán Bộ Trúc Cơ)", health_condition="Khỏe mạnh sung mãn", mental_state="Tự đắc"),
                        inventory=[InventoryItem(item_id="item_sword", name="Thanh Sương Kiếm"), InventoryItem(item_id="item_contract", name="Khế ước Vân Hà Ngọc Bội")]
                    ),
                    CharacterDossier(
                        character_id="char_lin_xue",
                        name="Lâm Tuyết",
                        role=CharacterRole.SIDEKICK,
                        visual_tags=["young female 15yo", "fair porcelain skin", "soft dark eyes", "pale lavender dress", "fragile graceful posture"],
                        personality=PersonalityTraits(
                            core_motivation="Không muốn trở thành gánh nặng cho ca ca",
                            fatal_flaw="Quá ngây thơ và dễ mềm lòng",
                            moral_boundary="Yêu thương gia đình tuyệt đối",
                            hidden_secret="Sở hữu Thể Chất Cửu Âm Tuyệt Mạch thức tỉnh"
                        ),
                        speech=SpeechStyle(vocabulary_level="Dịu dàng, ấm áp"),
                        status=CharacterStatus(power_tier="Chưa tu luyện (Phàm nhân)", health_condition="Hàn khí công tâm thường xuyên", mental_state="Lo lắng cho ca ca")
                    ),
                    CharacterDossier(
                        character_id="char_duoc_lao",
                        name="Dược Lão (Cổ Hồn)",
                        role=CharacterRole.MENTOR,
                        visual_tags=["ethereal translucent spirit", "ancient white beard and hair", "glowing ethereal white robes", "wise enigmatic smile"],
                        personality=PersonalityTraits(
                            core_motivation="Tìm kiếm thể xác hoàn mỹ để tái sinh và trả thù đệ tử phản bội",
                            fatal_flaw="Nghiện luyện đan kỳ dị và thích thử thách người khác",
                            moral_boundary="Chỉ giúp kẻ có ý chí kiên định",
                            hidden_secret="Từng là Bát Phẩm Đan Tôn chấn động Cửu Giới"
                        ),
                        speech=SpeechStyle(vocabulary_level="Cổ ngữ uyên bác, bông đùa sâu cay"),
                        status=CharacterStatus(power_tier="Linh hồn tàn khuyết (Tương đương Kim Đan)", health_condition="Linh hồn yếu ớt cần đan dược nuôi dưỡng", mental_state="Trầm ổn"),
                        inventory=[InventoryItem(item_id="item_flame", name="Cốt Linh Lãnh Hỏa (Dị Hỏa)")]
                    )
                ]
            )  # type: ignore

        if name == "WorldExpansionResult":
            from novel_engine.engine import WorldExpansionResult
            return WorldExpansionResult(
                new_factions=[
                    Faction(faction_id="fac_hac_ma", name="Hắc Ma Môn", alignment="Tà phái tàn độc", core_doctrine="Huyết tế tế linh để thăng cấp"),
                    Faction(faction_id="fac_dan_cac", name="Bách Thảo Đan Các", alignment="Trung lập thương gia", core_doctrine="Độc quyền thảo dược và đan dược toàn châu")
                ],
                new_locations=[
                    Location(location_id="loc_grave", name="Vạn Ma Cổ Mộ", climate_and_vibe="Âm phong gào thét, ngập tràn sát khí cổ đại", key_hazards="Thi độc ngàn năm và oán linh chiến trường"),
                    Location(location_id="loc_spring", name="Cửu U Băng Tuyền", climate_and_vibe="Hàn băng vĩnh cửu không tan", key_hazards="Nhiệt độ âm trăm độ đóng băng kinh mạch")
                ],
                new_canon_rules=[
                    "Dị Hỏa thiên địa khi dung hợp nếu không có đan dược áp chế sẽ thiêu rụi kinh mạch.",
                    "Linh hồn tàn khuyết chỉ có thể xuất hiện trong bóng tối hoặc bên trong kết giới cấm chế."
                ]
            )  # type: ignore

        if name == "ComicStoryboard":
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

        raise ValueError(f"Mock for schema {name} not implemented.")
