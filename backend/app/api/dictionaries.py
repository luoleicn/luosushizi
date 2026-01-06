"""Dictionary endpoints."""

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.config import Settings
from app.core.db import get_connection


router = APIRouter(prefix="/dictionaries", tags=["dictionaries"])


class DictionaryCreateRequest(BaseModel):
    name: str
    visibility: Optional[str] = "private"


class DictionaryUpdateRequest(BaseModel):
    name: Optional[str] = None
    visibility: Optional[str] = None


class DictionaryItem(BaseModel):
    id: int
    name: str
    visibility: str
    owner_id: str
    is_owner: bool


class DictionaryListResponse(BaseModel):
    items: List[DictionaryItem]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def fetch_dictionary(conn, dictionary_id: int):
    return conn.execute(
        "SELECT id, owner_id, name, visibility FROM dictionaries WHERE id = ?",
        (dictionary_id,),
    ).fetchone()


@router.get("", response_model=DictionaryListResponse)
def list_dictionaries(request: Request, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        owner_count = conn.execute(
            "SELECT COUNT(*) AS c FROM dictionaries WHERE owner_id = ?",
            (current_user["username"],),
        ).fetchone()["c"]
        if owner_count == 0:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO dictionaries (owner_id, name, visibility, created_at, updated_at)
                VALUES (?, ?, 'private', ?, ?)
                """,
                (current_user["username"], "我的字库", now, now),
            )
            conn.commit()
        rows = conn.execute(
            """
            SELECT id, owner_id, name, visibility
            FROM dictionaries
            WHERE owner_id = ? OR visibility = 'public'
            ORDER BY owner_id = ? DESC, name ASC
            """,
            (current_user["username"], current_user["username"]),
        ).fetchall()
        items = [
            {
                "id": row["id"],
                "name": row["name"],
                "visibility": row["visibility"],
                "owner_id": row["owner_id"],
                "is_owner": row["owner_id"] == current_user["username"],
            }
            for row in rows
        ]
        return {"items": items}
    finally:
        conn.close()


@router.post("", response_model=DictionaryItem)
def create_dictionary(
    payload: DictionaryCreateRequest, request: Request, current_user: dict = Depends(get_current_user)
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        try:
            cursor = conn.execute(
                """
                INSERT INTO dictionaries (owner_id, name, visibility, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    current_user["username"],
                    payload.name,
                    payload.visibility or "private",
                    now,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dictionary name already exists.",
            )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "name": payload.name,
            "visibility": payload.visibility or "private",
            "owner_id": current_user["username"],
            "is_owner": True,
        }
    finally:
        conn.close()


@router.patch("/{dictionary_id}", response_model=DictionaryItem)
def update_dictionary(
    dictionary_id: int,
    payload: DictionaryUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        row = fetch_dictionary(conn, dictionary_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictionary not found")
        if row["owner_id"] != current_user["username"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        name = payload.name or row["name"]
        visibility = payload.visibility or row["visibility"]
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                """
                UPDATE dictionaries
                SET name = ?, visibility = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, visibility, now, dictionary_id),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dictionary name already exists.",
            )
        conn.commit()
        return {
            "id": dictionary_id,
            "name": name,
            "visibility": visibility,
            "owner_id": row["owner_id"],
            "is_owner": True,
        }
    finally:
        conn.close()


@router.get("/{dictionary_id}", response_model=DictionaryItem)
def get_dictionary(
    dictionary_id: int, request: Request, current_user: dict = Depends(get_current_user)
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        row = fetch_dictionary(conn, dictionary_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictionary not found")
        if row["visibility"] != "public" and row["owner_id"] != current_user["username"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return {
            "id": row["id"],
            "name": row["name"],
            "visibility": row["visibility"],
            "owner_id": row["owner_id"],
            "is_owner": row["owner_id"] == current_user["username"],
        }
    finally:
        conn.close()


@router.delete("/{dictionary_id}")
def delete_dictionary(
    dictionary_id: int, request: Request, current_user: dict = Depends(get_current_user)
):
    settings = get_settings(request)
    conn = get_connection(settings.sqlite.path)
    try:
        row = fetch_dictionary(conn, dictionary_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dictionary not found")
        if row["owner_id"] != current_user["username"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        conn.execute(
            "DELETE FROM study_records WHERE dictionary_id = ?",
            (dictionary_id,),
        )
        conn.execute(
            "DELETE FROM study_sessions WHERE dictionary_id = ?",
            (dictionary_id,),
        )
        conn.execute(
            "DELETE FROM characters WHERE dictionary_id = ?",
            (dictionary_id,),
        )
        conn.execute(
            "DELETE FROM dictionaries WHERE id = ?",
            (dictionary_id,),
        )
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()
