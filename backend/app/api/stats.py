"""Stats endpoints."""


from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.config import Settings
from app.core.db import get_connection

router = APIRouter(prefix="/dictionaries/{dictionary_id}/stats", tags=["stats"])


class SummaryResponse(BaseModel):
    total: int
    known: int
    unknown: int
    due_today: int
    study_time_total: int


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def fetch_dictionary(conn, dictionary_id: int):
    return conn.execute(
        "SELECT id, owner_id, visibility FROM dictionaries WHERE id = ?",
        (dictionary_id,),
    ).fetchone()


def can_read(dictionary_row, user_id: str) -> bool:
    return dictionary_row and (
        dictionary_row["owner_id"] == user_id or dictionary_row["visibility"] == "public"
    )


@router.get("/summary", response_model=SummaryResponse)
def summary(dictionary_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        dictionary_row = fetch_dictionary(conn, dictionary_id)
        if not can_read(dictionary_row, current_user["username"]):
            return {"total": 0, "known": 0, "unknown": 0, "due_today": 0, "study_time_total": 0}
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM characters WHERE dictionary_id = ?",
            (dictionary_id,),
        ).fetchone()["c"]
        known = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM study_records
            WHERE user_id = ? AND dictionary_id = ? AND repetitions > 0
            """,
            (current_user["username"], dictionary_id),
        ).fetchone()["c"]
        unknown = max(total - known, 0)
        now = datetime.now(timezone.utc).isoformat()
        due_today = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM study_records
            WHERE user_id = ? AND dictionary_id = ? AND next_review_at <= ?
            """,
            (current_user["username"], dictionary_id, now),
        ).fetchone()["c"]
        study_time_total = conn.execute(
            """
            SELECT COALESCE(SUM((julianday(ended_at) - julianday(started_at)) * 86400), 0) AS seconds
            FROM study_sessions
            WHERE user_id = ? AND dictionary_id = ? AND ended_at IS NOT NULL
            """,
            (current_user["username"], dictionary_id),
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
