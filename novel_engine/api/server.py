"""FastAPI Server exposing NovelEngineCore endpoints and serving Web Studio UI."""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from novel_engine.core.state import (
    WorldBible,
    CharacterDossier,
    SceneContract,
    SceneDraft,
    StoryState
)
from novel_engine.engine import NovelDirectorEngine
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin
from novel_engine.adapters.mock_adapter import MockLLMAdapter
from novel_engine.adapters.litellm_adapter import LiteLLMAdapter

app = FastAPI(
    title="NovelEngineCore Studio API",
    description="Universe Architecture v4.0 - Story Director & Comic Studio",
    version="0.1.0"
)

# Global engine instance
_engine: Optional[NovelDirectorEngine] = None


def get_or_create_engine(model_name: str = "mock", api_key: Optional[str] = None, base_url: Optional[str] = None) -> NovelDirectorEngine:
    global _engine
    if _engine is None:
        if model_name == "mock":
            adapter = MockLLMAdapter()
        else:
            adapter = LiteLLMAdapter(model_name=model_name, api_key=api_key, base_url=base_url)

        _engine = NovelDirectorEngine(adapter=adapter)
        # Register Galaxy Plugins
        _engine.register_plugin(ContinuityAuditPlugin(strict_mode=True))
        _engine.register_plugin(ComicStoryboardPlugin(enabled=True))
    return _engine


class InitStoryRequest(BaseModel):
    title: str
    logline: str
    genre: str
    provider_model: str = "mock"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@app.post("/api/story/init", response_model=StoryState)
async def init_story(req: InitStoryRequest):
    engine = get_or_create_engine(req.provider_model, req.api_key, req.base_url)
    state = await engine.initialize_story(title=req.title, logline=req.logline, genre=req.genre)
    return state


@app.post("/api/character/register")
async def register_character(char: CharacterDossier):
    engine = get_or_create_engine()
    if not engine.state:
        # Auto-init mock story if not initialized
        await engine.initialize_story(title="Default Universe", logline="Default", genre="Xianxia")
    engine.register_character(char)
    return {"status": "success", "character_id": char.character_id}


class DraftSceneRequest(BaseModel):
    contract: SceneContract
    generate_comic: bool = True


@app.post("/api/scene/draft", response_model=SceneDraft)
async def draft_scene(req: DraftSceneRequest):
    engine = get_or_create_engine()
    if not engine.state:
        # Auto-initialize default story state
        await engine.initialize_story(
            title="Thương Lam Tiên Tôn",
            logline="Thiếu niên quật khởi",
            genre="Xianxia"
        )
    draft = await engine.draft_scene(contract=req.contract)
    return draft


# Mount Web UI static files
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
