"""Study queue and review endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.config import Settings
from app.core.db import get_connection
from app.services.scheduler.sm2 import apply_sm2

router = APIRouter(prefix="/study", tags=["study"])


class QueueItem(BaseModel):
    hanzi: str
    pinyin: str
    due_at: str | None
    is_new: bool


class QueueResponse(BaseModel):
    items: list[QueueItem]


class ReviewRequest(BaseModel):
    hanzi: str
    rating: int
    reviewed_at: str | None = None


class ReviewResponse(BaseModel):
    next_review_at: str
    interval: int
    ease_factor: float


class SessionStartResponse(BaseModel):
    session_id: int
    started_at: str


class SessionEndRequest(BaseModel):
    session_id: int
    ended_at: str | None = None


class SessionEndResponse(BaseModel):
    session_id: int
    ended_at: str


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("/queue", response_model=QueueResponse)
def get_queue(request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(settings.sqlite.path)
    try:
        rows = conn.execute(
            """
            SELECT c.hanzi, c.pinyin, sr.next_review_at
            FROM characters c
            LEFT JOIN study_records sr
              ON sr.character_id = c.id AND sr.user_id = ?
            WHERE sr.next_review_at IS NULL OR sr.next_review_at <= ?
            ORDER BY sr.next_review_at IS NULL DESC, sr.next_review_at ASC
            """,
            (current_user["username"], now),
        ).fetchall()
        items = []
        for row in rows:
            items.append(
                {
                    "hanzi": row["hanzi"],
                    "pinyin": row["pinyin"],
                    "due_at": row["next_review_at"],
                    "is_new": row["next_review_at"] is None,
                }
            )
        return {"items": items}
    finally:
        conn.close()


@router.post("/review", response_model=ReviewResponse)
def review_card(payload: ReviewRequest, request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        row = conn.execute(
            "SELECT id FROM characters WHERE hanzi = ?",
            (payload.hanzi,),
        ).fetchone()
        if row is None:
            return {"next_review_at": "", "interval": 0, "ease_factor": 2.5}
        character_id = row["id"]

        sr = conn.execute(
            """
            SELECT ease_factor, interval, repetitions
            FROM study_records
            WHERE user_id = ? AND character_id = ?
            """,
            (current_user["username"], character_id),
        ).fetchone()

        ease_factor = sr["ease_factor"] if sr else 2.5
        interval = sr["interval"] if sr else 0
        repetitions = sr["repetitions"] if sr else 0

        reviewed_at = (
            datetime.fromisoformat(payload.reviewed_at)
            if payload.reviewed_at
            else datetime.now(timezone.utc)
        )
        result = apply_sm2(
            ease_factor=ease_factor,
            interval=interval,
            repetitions=repetitions,
            rating=payload.rating,
            reviewed_at=reviewed_at,
        )

        conn.execute(
            """
            INSERT INTO study_records (user_id, character_id, ease_factor, interval, repetitions, last_reviewed_at, next_review_at, last_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, character_id) DO UPDATE SET
              ease_factor = excluded.ease_factor,
              interval = excluded.interval,
              repetitions = excluded.repetitions,
              last_reviewed_at = excluded.last_reviewed_at,
              next_review_at = excluded.next_review_at,
              last_rating = excluded.last_rating
            """,
            (
                current_user["username"],
                character_id,
                result.ease_factor,
                result.interval,
                result.repetitions,
                reviewed_at.isoformat(),
                result.next_review_at.isoformat(),
                payload.rating,
            ),
        )
        conn.commit()
        return {
            "next_review_at": result.next_review_at.isoformat(),
            "interval": result.interval,
            "ease_factor": result.ease_factor,
        }
    finally:
        conn.close()


@router.post("/session/start", response_model=SessionStartResponse)
def start_session(request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        started_at = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """
            INSERT INTO study_sessions (user_id, started_at)
            VALUES (?, ?)
            """,
            (current_user["username"], started_at),
        )
        conn.commit()
        return {"session_id": cursor.lastrowid, "started_at": started_at}
    finally:
        conn.close()


@router.post("/session/end", response_model=SessionEndResponse)
def end_session(
    payload: SessionEndRequest, request: Request, current_user: dict = Depends(get_current_user)
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        ended_at = (
            datetime.fromisoformat(payload.ended_at).isoformat()
            if payload.ended_at
            else datetime.now(timezone.utc).isoformat()
        )
        conn.execute(
            """
            UPDATE study_sessions
            SET ended_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (ended_at, payload.session_id, current_user["username"]),
        )
        conn.commit()
        return {"session_id": payload.session_id, "ended_at": ended_at}
    finally:
        conn.close()
