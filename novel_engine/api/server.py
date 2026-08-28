"""FastAPI Server exposing NovelEngineCore endpoints, Dynamic Model Discovery, RPG Codex & Web Studio UI."""

import os
import httpx
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from novel_engine.core.state import (
    WorldBible,
    CharacterDossier,
    SceneContract,
    SceneDraft,
    StoryState
)
from novel_engine.core.game_engine import (
    DiscoveryCodex,
    DiscoveryEntry,
    FateChoice,
    ChapterPlanningConfig
)
from novel_engine.engine import NovelDirectorEngine, WorldExpansionResult
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin
from novel_engine.plugins.file_persistence_plugin import FilePersistencePlugin
from novel_engine.plugins.rpg_discovery_plugin import RPGDiscoveryPlugin
from novel_engine.adapters.ollama_adapter import OllamaAdapter
from novel_engine.adapters.litellm_adapter import LiteLLMAdapter

app = FastAPI(
    title="NovelEngineCore Studio API",
    description="Universe Architecture v4.0 - RPG Story Director & Comic Studio",
    version="0.4.0"
)

# Global engine instance
_engine: Optional[NovelDirectorEngine] = None
_rpg_plugin: Optional[RPGDiscoveryPlugin] = None


def get_or_create_engine(model_name: str = "ollama/qwen2.5-coder:3b", api_key: Optional[str] = None, base_url: Optional[str] = None) -> NovelDirectorEngine:
    global _engine, _rpg_plugin
    
    if _engine is None or (_engine.adapter and getattr(_engine.adapter, "model_name", None) != model_name.replace("ollama/", "")):
        if model_name.startswith("ollama/") or ("qwen" in model_name.lower() or "llama" in model_name.lower()) and not api_key:
            actual_model = model_name.replace("ollama/", "")
            adapter = OllamaAdapter(model_name=actual_model, base_url=base_url or "http://localhost:11434")
        else:
            adapter = LiteLLMAdapter(model_name=model_name, api_key=api_key, base_url=base_url)

        _engine = NovelDirectorEngine(adapter=adapter)
        _rpg_plugin = RPGDiscoveryPlugin()

        _engine.register_plugin(ContinuityAuditPlugin(strict_mode=True))
        _engine.register_plugin(ComicStoryboardPlugin(enabled=True))
        _engine.register_plugin(FilePersistencePlugin(base_output_dir="output/stories"))
        _engine.register_plugin(_rpg_plugin)
    return _engine


# ----------------------------------------------------------------------
# Dynamic Model Discovery Endpoints (Scans Local Ollama & Cloud)
# ----------------------------------------------------------------------

class ModelInfo(BaseModel):
    id: str
    name: str
    category: str  # "Local Ollama" or "Cloud API"
    description: str
    is_available: bool = True
    size_mb: Optional[int] = None


@app.get("/api/models", response_model=List[ModelInfo])
async def get_available_models():
    """Scans local Ollama instance for installed models and returns full list."""
    models: List[ModelInfo] = []

    # 1. Probe Local Ollama API (http://localhost:11434/api/tags)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("models", []):
                    raw_name = m.get("name", "")
                    size_bytes = m.get("size", 0)
                    size_mb = round(size_bytes / (1024 * 1024))
                    models.append(
                        ModelInfo(
                            id=f"ollama/{raw_name}",
                            name=f"🟢 Local: {raw_name} ({size_mb} MB)",
                            category="Local Ollama (Đang Chạy)",
                            description=f"Model cục bộ chạy trên CPU/GPU, bảo mật 100%, phản hồi nhanh.",
                            is_available=True,
                            size_mb=size_mb
                        )
                    )
    except Exception as e:
        # If Ollama is offline, provide informative notice
        models.append(
            ModelInfo(
                id="ollama_offline",
                name="⚠️ Local Ollama Chưa Bật (Chạy `ollama serve`)",
                category="Local Ollama",
                description="Không tìm thấy Ollama trên http://localhost:11434",
                is_available=False
            )
        )

    # 2. Add Standard Cloud Model Options
    models.extend([
        ModelInfo(
            id="deepseek/deepseek-chat",
            name="☁️ DeepSeek-V3 (Cloud API - Siêu Rẻ & Thông Minh)",
            category="Cloud API",
            description="DeepSeek-V3 văn phong mượt mà, định dạng chặt chẽ."
        ),
        ModelInfo(
            id="claude-3-5-sonnet",
            name="☁️ Claude 3.5 Sonnet (Cloud API - Bậc Thầy Văn Học)",
            category="Cloud API",
            description="Anthropic Claude 3.5 đỉnh cao sáng tác văn học nghệ thuật."
        ),
        ModelInfo(
            id="gpt-4o",
            name="☁️ OpenAI GPT-4o (Cloud API)",
            category="Cloud API",
            description="Mô hình đa nhiệm mạnh mẽ của OpenAI."
        ),
        ModelInfo(
            id="gemini/gemini-1.5-flash",
            name="☁️ Google Gemini 1.5 Flash (Cloud API)",
            category="Cloud API",
            description="Tốc độ cao, ngữ cảnh triệu tokens."
        )
    ])

    return models


class TestModelRequest(BaseModel):
    model_name: str = "ollama/qwen2.5-coder:3b"
    prompt: Optional[str] = "Hãy trả lời trong 1 câu ngắn bằng tiếng Việt: Bạn tên là gì và đã sẵn sàng chưa?"


class TestModelResponse(BaseModel):
    success: bool
    latency_ms: int
    reply: str
    model_name: str
    error: Optional[str] = None


@app.post("/api/model/test", response_model=TestModelResponse)
async def test_model_connection(req: TestModelRequest):
    """Tests connection and measures latency for the selected LLM."""
    import time
    start_time = time.time()
    try:
        if req.model_name.startswith("ollama/"):
            actual_model = req.model_name.replace("ollama/", "")
            adapter = OllamaAdapter(model_name=actual_model)
        else:
            adapter = LiteLLMAdapter(model_name=req.model_name)

        reply = await adapter.generate_text(
            prompt=req.prompt or "Hãy chào bằng tiếng Việt ngắn gọn.",
            system_prompt="You are an AI assistant. Reply in one short Vietnamese sentence.",
            max_tokens=100
        )
        latency = round((time.time() - start_time) * 1000)
        return TestModelResponse(
            success=True,
            latency_ms=latency,
            reply=reply.strip(),
            model_name=req.model_name
        )
    except Exception as e:
        latency = round((time.time() - start_time) * 1000)
        return TestModelResponse(
            success=False,
            latency_ms=latency,
            reply="",
            model_name=req.model_name,
            error=str(e)
        )


# ----------------------------------------------------------------------
# Story & State Endpoints
# ----------------------------------------------------------------------

class InitStoryRequest(BaseModel):
    title: str = "Thương Lam Tiên Tôn"
    logline: str = "Một thiếu niên phế vật tìm được chiếc nhẫn cổ quật khởi đối đầu tông môn."
    genre: str = "Xianxia"
    provider_model: str = "ollama/qwen2.5-coder:3b"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@app.get("/api/state", response_model=StoryState)
async def get_state():
    engine = get_or_create_engine()
    if not engine.state:
        await engine.initialize_story(
            title="Thương Lam Tiên Tôn",
            logline="Một thiếu niên phế vật tìm được chiếc nhẫn cổ quật khởi đối đầu tông môn.",
            genre="Xianxia"
        )
    return engine.state


@app.post("/api/story/init", response_model=StoryState)
async def init_story(req: InitStoryRequest):
    global _engine
    _engine = None
    engine = get_or_create_engine(req.provider_model, req.api_key, req.base_url)
    state = await engine.initialize_story(title=req.title, logline=req.logline, genre=req.genre)
    return state


# ----------------------------------------------------------------------
# RPG Discovery Codex & Game Directives Endpoints
# ----------------------------------------------------------------------

@app.get("/api/discovery/codex")
async def get_discovery_codex():
    engine = get_or_create_engine()
    if not engine.state:
        await engine.initialize_story("Thương Lam Giới", "Tu tiên", "Xianxia")
    if _rpg_plugin and _rpg_plugin.codex:
        return _rpg_plugin.codex
    return {"total_discoveries": 0, "entries": [], "rpg_character_stats": {}, "active_fate_options": []}


class SelectFateRequest(BaseModel):
    choice_id: str
    custom_directive: Optional[str] = None


@app.post("/api/fate/select")
async def select_fate_directive(req: SelectFateRequest):
    return {
        "status": "selected",
        "choice_id": req.choice_id,
        "custom_directive": req.custom_directive,
        "message": "Đã thiết lập hướng đi số phận cho nhân vật trong phân cảnh tiếp theo!"
    }


# ----------------------------------------------------------------------
# World Genesis & Character Matrix Endpoints
# ----------------------------------------------------------------------

class AutoWorldRequest(BaseModel):
    title: str = "Thương Lam Giới"
    genre: str = "Xianxia"
    logline: str = "Thế giới tu tiên mạt pháp ngập tràn bí ẩn."
    provider_model: str = "ollama/qwen2.5-coder:3b"


@app.post("/api/world/auto-generate", response_model=WorldBible)
async def auto_generate_world(req: AutoWorldRequest):
    engine = get_or_create_engine(req.provider_model)
    state = await engine.initialize_story(title=req.title, logline=req.logline, genre=req.genre)
    return state.world_bible


class EvolveWorldRequest(BaseModel):
    focus_topic: str = "Các Tông Môn Bí Ẩn & Cấm Địa Cổ Xưa"


@app.post("/api/world/evolve", response_model=WorldExpansionResult)
async def auto_evolve_world(req: EvolveWorldRequest):
    engine = get_or_create_engine()
    if not engine.state:
        await engine.initialize_story("Thương Lam Giới", "Tu tiên", "Xianxia")
    result = await engine.auto_evolve_world(focus_topic=req.focus_topic)
    return result


class AutoCharRequest(BaseModel):
    count: int = 4
    roles_focus: str = "Protagonist, Antagonist, Mentor, Sidekick"


@app.post("/api/character/auto-generate", response_model=List[CharacterDossier])
async def auto_generate_characters(req: AutoCharRequest):
    engine = get_or_create_engine()
    if not engine.state:
        await engine.initialize_story("Thương Lam Giới", "Tu tiên", "Xianxia")
    chars = await engine.auto_generate_characters(count=req.count, roles_focus=req.roles_focus)
    return chars


@app.post("/api/character/add", response_model=CharacterDossier)
async def add_character(char: CharacterDossier):
    engine = get_or_create_engine()
    if not engine.state:
        await engine.initialize_story("Thương Lam Giới", "Tu tiên", "Xianxia")
    engine.register_character(char)
    return char


@app.delete("/api/character/{character_id}")
async def delete_character(character_id: str):
    engine = get_or_create_engine()
    if engine.state and character_id in engine.state.characters:
        engine.delete_character(character_id)
        return {"status": "deleted", "character_id": character_id}
    raise HTTPException(status_code=404, detail="Character not found.")


# ----------------------------------------------------------------------
# Scene Drafting Endpoints
# ----------------------------------------------------------------------

class DraftSceneRequest(BaseModel):
    contract: SceneContract
    provider_model: str = "ollama/qwen2.5-coder:3b"
    generate_comic: bool = True


@app.post("/api/scene/draft", response_model=SceneDraft)
async def draft_scene(req: DraftSceneRequest):
    engine = get_or_create_engine(model_name=req.provider_model)
    if not engine.state:
        await engine.initialize_story(
            title="Thương Lam Tiên Tôn",
            logline="Thiếu niên quật khởi",
            genre="Xianxia"
        )
    draft = await engine.draft_scene(contract=req.contract)
    return draft


# ----------------------------------------------------------------------
# Static Web Mounting
# ----------------------------------------------------------------------
web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(web_dir, "index.html"))

    @app.get("/style.css")
    async def serve_css():
        return FileResponse(os.path.join(web_dir, "style.css"))

    @app.get("/app.js")
    async def serve_js():
        return FileResponse(os.path.join(web_dir, "app.js"))
