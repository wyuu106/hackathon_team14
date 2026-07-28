import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import Models, Schemas


class UsernameAlreadyExistsError(Exception):
    """ユーザー名が既に登録されている"""


BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """パスワードをbcryptでハッシュ化する"""
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """平文パスワードとハッシュを照合する"""
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


# --- ユーザー関連 ---
def create_user(db: Session, user: Schemas.UserCreate) -> Models.User:
    """ユーザーを新規登録する

    ユーザー名が既に使われている場合はUsernameAlreadyExistsErrorを送出する。
    """
    if get_user_by_username(db, user.username) is not None:
        raise UsernameAlreadyExistsError(user.username)

    db_user = Models.User(
        username=user.username,
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as e:
        # 同時リクエストが上の存在チェックをすり抜けた場合の保険。
        # rollbackしないとセッションが失敗状態のまま後続クエリも全て失敗する
        db.rollback()
        raise UsernameAlreadyExistsError(user.username) from e
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Models.User | None:
    """IDでユーザーを取得する"""
    return db.get(Models.User, user_id)


def get_user_by_username(db: Session, username: str) -> Models.User | None:
    """ユーザー名でユーザーを取得する"""
    return db.scalars(
        select(Models.User).where(Models.User.username == username)
    ).first()


# --- 投稿関連 ---
def create_post(db: Session, post: Schemas.PostCreate, user_id: int) -> Models.Post:
    """投稿を作成する"""
    db_post = Models.Post(content=post.content, user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_timeline(db: Session, current_user_id: int) -> list[Models.Post]:
    """自分とフォロー中ユーザーの投稿を新しい順で取得する"""
    # フォロー中のユーザーIDを取得
    followed_ids = db.scalars(
        select(Models.follows_table.c.followed_id).where(
            Models.follows_table.c.follower_id == current_user_id
        )
    ).all()

    # 自分の投稿もタイムラインに含める
    author_ids = [*followed_ids, current_user_id]

    return list(
        db.scalars(
            select(Models.Post)
            .where(Models.Post.user_id.in_(author_ids))
            .order_by(Models.Post.created_at.desc(), Models.Post.id.desc())
        ).all()
    )


# --- フォロー関連 ---
def follow_user(db: Session, follower_id: int, followed_id: int) -> None:
    """ユーザーをフォローする"""
    if follower_id == followed_id:
        raise ValueError("自分自身をフォローすることはできません")

    # フォロー元・フォロー先の存在確認
    if get_user(db, follower_id) is None or get_user(db, followed_id) is None:
        raise ValueError("ユーザーが存在しません")

    # 既にフォロー済みかを確認
    if is_following(db, follower_id, followed_id):
        raise ValueError("既にフォローしています")

    db.execute(
        Models.follows_table.insert().values(
            follower_id=follower_id, followed_id=followed_id
        )
    )
    db.commit()


def is_following(db: Session, follower_id: int, followed_id: int) -> bool:
    """フォロー済みかどうかを返す"""
    return (
        db.execute(
            select(Models.follows_table).where(
                Models.follows_table.c.follower_id == follower_id,
                Models.follows_table.c.followed_id == followed_id,
            )
        ).first()
        is not None
    )
