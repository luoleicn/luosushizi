"""App config loader."""


import os
from typing import Any, Dict, List

import yaml


class AppConfig:
    def __init__(self, name: str, secret_key: str, token_expire_minutes: int) -> None:
        self.name = name
        self.secret_key = secret_key
        self.token_expire_minutes = token_expire_minutes


class AccountConfig:
    def __init__(self, username: str, password_hash: str) -> None:
        self.username = username
        self.password_hash = password_hash


class SqliteConfig:
    def __init__(self, path: str) -> None:
        self.path = path


class DictionaryConfig:
    def __init__(self, source: str, max_common_words: int) -> None:
        self.source = source
        self.max_common_words = max_common_words


class CORSConfig:
    def __init__(
        self,
        env: str,
        dev_origins: List[str],
        prod_origins: List[str],
        allow_credentials: bool,
    ) -> None:
        self.env = env
        self.dev_origins = dev_origins
        self.prod_origins = prod_origins
        self.allow_credentials = allow_credentials


class Settings:
    def __init__(
        self,
        app: AppConfig,
        accounts: List[AccountConfig],
        sqlite: SqliteConfig,
        dictionary: DictionaryConfig,
        cors: CORSConfig,
    ) -> None:
        self.app = app
        self.accounts = accounts
        self.sqlite = sqlite
        self.dictionary = dictionary
        self.cors = cors


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
    cors_raw = _require_key(raw, "cors")

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
    cors = CORSConfig(
        env=_require_key(cors_raw, "env"),
        dev_origins=_require_key(cors_raw, "dev_origins"),
        prod_origins=_require_key(cors_raw, "prod_origins"),
        allow_credentials=bool(_require_key(cors_raw, "allow_credentials")),
    )

    return Settings(
        app=app,
        accounts=accounts,
        sqlite=sqlite,
        dictionary=dictionary,
        cors=cors,
    )


def get_config_path() -> str:
    env_path = os.environ.get("HANZI_CARDS_CONFIG")
    if env_path:
        return env_path
    # Default to the config.yaml next to this file for stable resolution.
    path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Missing config.yaml. Copy backend/app/core/config.yaml.example to config.yaml."
        )
    return path
