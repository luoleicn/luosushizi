"""App config loader."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

import yaml


@dataclass
class AppConfig:
    name: str
    secret_key: str
    token_expire_minutes: int


@dataclass
class AccountConfig:
    username: str
    password_hash: str


@dataclass
class SqliteConfig:
    path: str


@dataclass
class DictionaryConfig:
    source: str
    max_common_words: int


@dataclass
class Settings:
    app: AppConfig
    accounts: List[AccountConfig]
    sqlite: SqliteConfig
    dictionary: DictionaryConfig


def _require_key(data: Dict[str, Any], key: str) -> Any:
    if key not in data:
        raise KeyError(f"Missing config key: {key}")
    return data[key]


def load_config(path: str) -> Settings:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    app_raw = _require_key(raw, "app")
    accounts_raw = _require_key(raw, "accounts")
    sqlite_raw = _require_key(raw, "sqlite")
    dict_raw = _require_key(raw, "dictionary")

    app = AppConfig(
        name=_require_key(app_raw, "name"),
        secret_key=_require_key(app_raw, "secret_key"),
        token_expire_minutes=int(_require_key(app_raw, "token_expire_minutes")),
    )
    accounts = [
        AccountConfig(
            username=_require_key(item, "username"),
            password_hash=_require_key(item, "password_hash"),
        )
        for item in accounts_raw
    ]
    sqlite_path = _require_key(sqlite_raw, "path")
    if not os.path.isabs(sqlite_path):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        sqlite_path = os.path.join(base_dir, sqlite_path)
    sqlite = SqliteConfig(path=sqlite_path)
    dictionary = DictionaryConfig(
        source=_require_key(dict_raw, "source"),
        max_common_words=int(_require_key(dict_raw, "max_common_words")),
    )

    return Settings(
        app=app,
        accounts=accounts,
        sqlite=sqlite,
        dictionary=dictionary,
    )


def get_config_path() -> str:
    env_path = os.environ.get("HANZI_CARDS_CONFIG")
    if env_path:
        return env_path
    # Default to the config.yaml next to this file for stable resolution.
    return os.path.join(os.path.dirname(__file__), "config.yaml")
