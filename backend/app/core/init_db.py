"""Initialize app database schema."""


from app.core.config import get_config_path, load_config
from app.core.db import get_connection, init_schema


def main() -> None:
    settings = load_config(get_config_path())
    conn = get_connection(settings.sqlite.path)
    try:
        init_schema(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
