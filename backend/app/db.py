import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
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

# セッション作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベース
Base = declarative_base()


def get_db():
    db: Session = SessionLocal()  # 新しいセッション
    try:
        yield db
    finally:
        db.close()
