"""NovelEngine Plugins package (Universe Architecture Stars)."""
from novel_engine.plugins.base import INovelPlugin
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin

__all__ = ["INovelPlugin", "ComicStoryboardPlugin", "ContinuityAuditPlugin"]
