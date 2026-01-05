"""Character endpoints."""


from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.config import Settings
from app.core.db import get_connection
from app.services.dictionary.pinyin import get_pinyin
from app.services.dictionary.thuocl import get_common_words

router = APIRouter(prefix="/characters", tags=["characters"])


class CharacterInfoResponse(BaseModel):
    hanzi: str
    pinyin: str
    common_words: list


class ImportRequest(BaseModel):
    items: List[str]


class ImportResponse(BaseModel):
    imported: int
    skipped: int


class CharacterListItem(BaseModel):
    hanzi: str
    pinyin: str


class CharacterListResponse(BaseModel):
    items: List[CharacterListItem]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def ensure_character(conn, hanzi: str) -> bool:
    pinyin_text = get_pinyin(hanzi)
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT OR IGNORE INTO characters (hanzi, pinyin, cached_at) VALUES (?, ?, ?)",
        (hanzi, pinyin_text, now),
    )
    return cursor.rowcount > 0


@router.get("/{hanzi}/info", response_model=CharacterInfoResponse)
def character_info(hanzi: str, request: Request, _user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        row = conn.execute(
            "SELECT hanzi, pinyin FROM characters WHERE hanzi = ?",
            (hanzi,),
        ).fetchone()
        if row is None:
            ensure_character(conn, hanzi)
            row = conn.execute(
                "SELECT hanzi, pinyin FROM characters WHERE hanzi = ?",
                (hanzi,),
            ).fetchone()
        common_words = get_common_words(
            settings.sqlite.path, hanzi, settings.dictionary.max_common_words
        )
        return {"hanzi": row["hanzi"], "pinyin": row["pinyin"], "common_words": common_words}
    finally:
        conn.close()


@router.post("/import", response_model=ImportResponse)
def import_characters(payload: ImportRequest, request: Request, _user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        imported = 0
        skipped = 0
        for hanzi in payload.items:
            if len(hanzi) != 1:
                skipped += 1
                continue
            if not ("\u4e00" <= hanzi <= "\u9fff"):
                skipped += 1
                continue
            if ensure_character(conn, hanzi):
                imported += 1
            else:
                skipped += 1
        conn.commit()
        return {"imported": imported, "skipped": skipped}
    finally:
        conn.close()


@router.get("/list", response_model=CharacterListResponse)
def list_characters(request: Request, _user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        rows = conn.execute(
            "SELECT hanzi, pinyin FROM characters ORDER BY hanzi ASC"
        ).fetchall()
        return {
            "items": [{"hanzi": row["hanzi"], "pinyin": row["pinyin"]} for row in rows]
        }
    finally:
        conn.close()
