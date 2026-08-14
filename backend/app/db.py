import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


load_dotenv(REPO_ROOT / ".env")


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("環境変数 DATABASE_URL が設定されていません。")


_url = make_url(DATABASE_URL)
if (
    _url.drivername.startswith("sqlite")
    and _url.database
    and _url.database != ":memory:"
    and not Path(_url.database).is_absolute()
):
    _url = _url.set(database=str(BACKEND_DIR / _url.database))

# DBエンジン作成
engine = create_engine(_url)


if _url.drivername.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# セッション作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベース
Base = declarative_base()


def apply_schema_updates() -> None:
    """Alembic導入前の既存DBへ、小さな後方互換スキーマ更新を適用する。"""
    inspector = inspect(engine)
    if "friendships" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("friendships")}
    if "accepted_at" in columns:
        return
    column_type = "TIMESTAMP" if engine.dialect.name == "postgresql" else "DATETIME"
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE friendships ADD COLUMN accepted_at {column_type}"))


def get_db():
    db: Session = SessionLocal()  # 新しいセッション
    try:
        yield db
    finally:
        db.close()
