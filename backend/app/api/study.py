"""Study queue and review endpoints."""


from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.config import Settings
from app.core.db import get_connection
from app.services.scheduler.sm2 import apply_sm2

router = APIRouter(prefix="/dictionaries/{dictionary_id}/study", tags=["study"])


class QueueItem(BaseModel):
    hanzi: str
    pinyin: str
    due_at: Optional[str]
    is_new: bool


class QueueResponse(BaseModel):
    items: List[QueueItem]


class ReviewRequest(BaseModel):
    hanzi: str
    rating: int
    reviewed_at: Optional[str] = None


class ReviewResponse(BaseModel):
    next_review_at: str
    interval: int
    ease_factor: float


class SessionStartResponse(BaseModel):
    session_id: int
    started_at: str


class SessionEndRequest(BaseModel):
    session_id: int
    ended_at: Optional[str] = None


class SessionEndResponse(BaseModel):
    session_id: int
    ended_at: str


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


@router.get("/queue", response_model=QueueResponse)
def get_queue(dictionary_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(settings.sqlite.path)
    try:
        dictionary_row = fetch_dictionary(conn, dictionary_id)
        if not can_read(dictionary_row, current_user["username"]):
            return {"items": []}
        rows = conn.execute(
            """
            SELECT c.hanzi, c.pinyin, sr.next_review_at
            FROM characters c
            LEFT JOIN study_records sr
              ON sr.character_id = c.id AND sr.user_id = ? AND sr.dictionary_id = ?
            WHERE c.dictionary_id = ?
              AND (sr.next_review_at IS NULL OR sr.next_review_at <= ?)
            ORDER BY sr.next_review_at IS NULL DESC, sr.next_review_at ASC
            """,
            (current_user["username"], dictionary_id, dictionary_id, now),
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
def review_card(
    dictionary_id: int, payload: ReviewRequest, request: Request, current_user: dict = Depends(get_current_user)
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        dictionary_row = fetch_dictionary(conn, dictionary_id)
        if not can_read(dictionary_row, current_user["username"]):
            return {"next_review_at": "", "interval": 0, "ease_factor": 2.5}
        row = conn.execute(
            "SELECT id FROM characters WHERE dictionary_id = ? AND hanzi = ?",
            (dictionary_id, payload.hanzi),
        ).fetchone()
        if row is None:
            return {"next_review_at": "", "interval": 0, "ease_factor": 2.5}
        character_id = row["id"]

        sr = conn.execute(
            """
            SELECT ease_factor, interval, repetitions
            FROM study_records
            WHERE user_id = ? AND dictionary_id = ? AND character_id = ?
            """,
            (current_user["username"], dictionary_id, character_id),
        ).fetchone()

        ease_factor = sr["ease_factor"] if sr else 2.5
        interval = sr["interval"] if sr else 0
        repetitions = sr["repetitions"] if sr else 0

        reviewed_at = parse_iso_datetime(payload.reviewed_at)
        result = apply_sm2(
            ease_factor=ease_factor,
            interval=interval,
            repetitions=repetitions,
            rating=payload.rating,
            reviewed_at=reviewed_at,
        )

        conn.execute(
            """
            INSERT INTO study_records (user_id, dictionary_id, character_id, ease_factor, interval, repetitions, last_reviewed_at, next_review_at, last_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, dictionary_id, character_id) DO UPDATE SET
              ease_factor = excluded.ease_factor,
              interval = excluded.interval,
              repetitions = excluded.repetitions,
              last_reviewed_at = excluded.last_reviewed_at,
              next_review_at = excluded.next_review_at,
              last_rating = excluded.last_rating
            """,
            (
                current_user["username"],
                dictionary_id,
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
def start_session(dictionary_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        dictionary_row = fetch_dictionary(conn, dictionary_id)
        if not can_read(dictionary_row, current_user["username"]):
            return {"session_id": 0, "started_at": ""}
        started_at = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """
            INSERT INTO study_sessions (user_id, dictionary_id, started_at)
            VALUES (?, ?, ?)
            """,
            (current_user["username"], dictionary_id, started_at),
        )
        conn.commit()
        return {"session_id": cursor.lastrowid, "started_at": started_at}
    finally:
        conn.close()


@router.post("/session/end", response_model=SessionEndResponse)
def end_session(
    dictionary_id: int,
    payload: SessionEndRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        dictionary_row = fetch_dictionary(conn, dictionary_id)
        if not can_read(dictionary_row, current_user["username"]):
            return {"session_id": payload.session_id, "ended_at": ""}
        ended_at = parse_iso_datetime(payload.ended_at).isoformat()
        conn.execute(
            """
            UPDATE study_sessions
            SET ended_at = ?
            WHERE id = ? AND user_id = ? AND dictionary_id = ?
            """,
            (ended_at, payload.session_id, current_user["username"], dictionary_id),
        )
        conn.commit()
        return {"session_id": payload.session_id, "ended_at": ended_at}
    finally:
        conn.close()


def parse_iso_datetime(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    iso_value = value.replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(iso_value, fmt)
        except ValueError:
            continue
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(iso_value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)
