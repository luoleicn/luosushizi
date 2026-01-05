"""Stats endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.config import Settings
from app.core.db import get_connection

router = APIRouter(prefix="/stats", tags=["stats"])


class SummaryResponse(BaseModel):
    total: int
    known: int
    unknown: int
    due_today: int
    study_time_total: int


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("/summary", response_model=SummaryResponse)
def summary(request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM characters").fetchone()["c"]
        known = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM study_records
            WHERE user_id = ? AND repetitions > 0
            """,
            (current_user["username"],),
        ).fetchone()["c"]
        unknown = max(total - known, 0)
        now = datetime.now(timezone.utc).isoformat()
        due_today = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM study_records
            WHERE user_id = ? AND next_review_at <= ?
            """,
            (current_user["username"], now),
        ).fetchone()["c"]
        study_time_total = conn.execute(
            """
            SELECT COALESCE(SUM((julianday(ended_at) - julianday(started_at)) * 86400), 0) AS seconds
            FROM study_sessions
            WHERE user_id = ? AND ended_at IS NOT NULL
            """,
            (current_user["username"],),
        ).fetchone()["seconds"]
        return {
            "total": total,
            "known": known,
            "unknown": unknown,
            "due_today": due_today,
            "study_time_total": int(study_time_total),
        }
    finally:
        conn.close()
