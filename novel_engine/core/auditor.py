"""Continuity & Rule Auditor for drafted prose."""

from typing import List, Optional
from pydantic import BaseModel, Field
from novel_engine.core.state import SceneContract, WorldBible


class Violation(BaseModel):
    rule_type: str = Field(description="'CANON_LAW', 'HARD_CONSTRAINT', or 'OOC_VIOLATION'")
    description: str
    offending_text: Optional[str] = None
    suggested_fix: str


class AuditReport(BaseModel):
    passed: bool
    violations: List[Violation] = Field(default_factory=list)
    overall_quality_score: int = Field(ge=1, le=10, default=8)


class ContinuityAuditor:
    @staticmethod
    def build_audit_prompt(prose: str, contract: SceneContract, world_bible: WorldBible) -> str:
        """Constructs prompt for the Auditor LLM to inspect prose against rules."""
        canon_text = "\n".join(f"- {rule}" for rule in world_bible.canon_rules)
        constraints_text = "\n".join(f"- {c}" for c in contract.hard_constraints)

        return f"""
You are a meticulous Literary Continuity Auditor.
Inspect the drafted prose below against the Canon Rules and Scene Hard Constraints.

CANON RULES:
{canon_text}

SCENE HARD CONSTRAINTS:
{constraints_text}

DRAFT PROSE:
{prose}

Evaluate if any constraint was broken. Output an AuditReport in JSON format.
"""
