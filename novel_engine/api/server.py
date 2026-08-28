"""FastAPI Server exposing NovelEngineCore endpoints and serving Web Studio UI."""

import os
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
from novel_engine.engine import NovelDirectorEngine, WorldExpansionResult
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin
from novel_engine.adapters.mock_adapter import MockLLMAdapter
from novel_engine.adapters.ollama_adapter import OllamaAdapter
from novel_engine.adapters.litellm_adapter import LiteLLMAdapter

app = FastAPI(
    title="NovelEngineCore Studio API",
    description="Universe Architecture v4.0 - Story Director & Comic Studio",
    version="0.2.0"
)

# Global engine instance
_engine: Optional[NovelDirectorEngine] = None


def get_or_create_engine(model_name: str = "mock", api_key: Optional[str] = None, base_url: Optional[str] = None) -> NovelDirectorEngine:
    global _engine
    
    if _engine is None:
        if model_name.startswith("ollama/") or ("qwen" in model_name.lower() or "llama" in model_name.lower()) and not api_key:
            actual_model = model_name.replace("ollama/", "")
            adapter = OllamaAdapter(model_name=actual_model, base_url=base_url or "http://localhost:11434")
        elif model_name == "mock":
            adapter = MockLLMAdapter()
        else:
            adapter = LiteLLMAdapter(model_name=model_name, api_key=api_key, base_url=base_url)

        _engine = NovelDirectorEngine(adapter=adapter)
        _engine.register_plugin(ContinuityAuditPlugin(strict_mode=True))
        _engine.register_plugin(ComicStoryboardPlugin(enabled=True))
        _engine.register_plugin(FilePersistencePlugin(base_output_dir="output/stories"))
    return _engine


# ----------------------------------------------------------------------
# Story & State Endpoints
# ----------------------------------------------------------------------

class InitStoryRequest(BaseModel):
    title: str = "Thương Lam Tiên Tôn"
    logline: str = "Một thiếu niên phế vật tìm được chiếc nhẫn cổ quật khởi đối đầu tông môn."
    genre: str = "Xianxia"
    provider_model: str = "mock"
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
    _engine = None  # Reset engine with new model/config
    engine = get_or_create_engine(req.provider_model, req.api_key, req.base_url)
    state = await engine.initialize_story(title=req.title, logline=req.logline, genre=req.genre)
    return state


# ----------------------------------------------------------------------
# World Genesis & Auto-Evolution Endpoints
# ----------------------------------------------------------------------

class AutoWorldRequest(BaseModel):
    title: str = "Thương Lam Giới"
    genre: str = "Xianxia"
    logline: str = "Thế giới tu tiên mạt pháp ngập tràn bí ẩn và di tích thượng cổ."
    provider_model: str = "mock"


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


# ----------------------------------------------------------------------
# Character Matrix & Auto-Generation Endpoints
# ----------------------------------------------------------------------

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
# Scene Drafting & Comic Storyboard Endpoints
# ----------------------------------------------------------------------

class DraftSceneRequest(BaseModel):
    contract: SceneContract
    provider_model: str = "mock"
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
