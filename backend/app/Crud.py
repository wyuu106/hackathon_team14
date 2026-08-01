import bcrypt
from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from app import Models, Schemas


class UserIdAlreadyExistsError(Exception):
    """ログインID(user_id)が既に登録されている"""


UsernameAlreadyExistsError = UserIdAlreadyExistsError


class TemplateAlreadyExistsError(Exception):
    """同じ本文の定型文が既に登録されている"""


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
    """ユーザーを新規登録する"""

    
    if get_user_by_user_id(db, user.user_id) is not None:
        raise UserIdAlreadyExistsError(user.user_id)

    db_user = Models.User(
        user_id=user.user_id,
        username=user.username,
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as e:
       
        db.rollback()
        raise UserIdAlreadyExistsError(user.user_id) from e
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_pk: int) -> Models.User | None:
    
    return db.get(Models.User, user_pk)


def get_user_by_user_id(db: Session, user_id: str) -> Models.User | None:
    """ログインIDでユーザーを取得する"""
    return db.scalars(
        select(Models.User).where(Models.User.user_id == user_id)
    ).first()


# --- 投稿関連 ---
def create_post(db: Session, post: Schemas.PostCreate, user_pk: int) -> Models.Post:
    """投稿を作成する（user_pkはusers.idの数値PK）"""
    db_post = Models.Post(content=post.content, user_id=user_pk)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_timeline(db: Session, current_user_pk: int) -> list[Models.Post]:
    """自分とフォロー中ユーザーの投稿を新しい順で取得する"""
    # フォロー中のユーザーの数値PKを取得
    followed_ids = db.scalars(
        select(Models.follows_table.c.followed_id).where(
            Models.follows_table.c.follower_id == current_user_pk
        )
    ).all()

    # 自分の投稿もタイムラインに含める
    author_ids = [*followed_ids, current_user_pk]

    return list(
        db.scalars(
            select(Models.Post)
            .where(Models.Post.user_id.in_(author_ids))
            .order_by(Models.Post.created_at.desc(), Models.Post.id.desc())
        ).all()
    )


# --- フォロー関連 ---
def follow_user(db: Session, follower_id: int, followed_id: int) -> None:
    """ユーザーをフォローする（引数はどちらもusers.idの数値PK）"""
    if follower_id == followed_id:
        raise ValueError("自分自身をフォローすることはできません")

    # フォロー元・フォロー先の存在確認
    if get_user(db, follower_id) is None or get_user(db, followed_id) is None:
        raise ValueError("ユーザーが存在しません")

    # 既にフォロー済みかを確認
    if is_following(db, follower_id, followed_id):
        raise ValueError("既にフォローしています")

    # フォローした時点を既読の起点にする。
    db.execute(
        Models.follows_table.insert().values(
            follower_id=follower_id,
            followed_id=followed_id,
            last_read_at=datetime.utcnow(),
        )
    )
    db.commit()


def is_following(db: Session, follower_id: int, followed_id: int) -> bool:
    """フォロー済みかどうかを返す（引数はどちらもusers.idの数値PK）"""
    return (
        db.execute(
            select(Models.follows_table).where(
                Models.follows_table.c.follower_id == follower_id,
                Models.follows_table.c.followed_id == followed_id,
            )
        ).first()
        is not None
    )


def get_followed_users(db: Session, current_user_pk: int) -> list[dict]:
    """フォロー中ユーザーを最新メッセージと既読状態つきで返す

    Inbox.jsxが読むキー（user_id / username / read_status / latest_message）で返す。
    最新メッセージが新しい順、メッセージのない相手は末尾に並べる。
    """
    # 相手ごとの最新投稿。idは自動連番なので最大値が最新
    latest_post = aliased(Models.Post)
    latest_post_id = (
        select(func.max(Models.Post.id))
        .where(Models.Post.user_id == Models.follows_table.c.followed_id)
        .correlate(Models.follows_table)
        .scalar_subquery()
    )

    rows = db.execute(
        select(
            Models.User.user_id,
            Models.User.username,
            Models.follows_table.c.last_read_at,
            latest_post.content,
            latest_post.created_at,
        )
        .join(Models.User, Models.User.id == Models.follows_table.c.followed_id)
        .outerjoin(latest_post, latest_post.id == latest_post_id)
        .where(Models.follows_table.c.follower_id == current_user_pk)
    ).all()

    result = []
    for user_id, username, last_read_at, content, created_at in rows:
        if created_at is None:
            # メッセージが1件もなければ未読ドットは出さない
            read_status = True
        elif last_read_at is None:
            read_status = False
        else:
            read_status = created_at <= last_read_at

        result.append(
            {
                "user_id": user_id,
                "username": username,
                "read_status": read_status,
                "latest_message": content,
                "_sort_key": created_at,
            }
        )

    
    result.sort(key=lambda r: (r["_sort_key"] is not None, r["_sort_key"]), reverse=True)
    for row in result:
        del row["_sort_key"]

    return result


def mark_as_read(db: Session, reader_pk: int, target_pk: int) -> None:
    """相手のメッセージを既読にする

    フォローしていない相手なら何もしない（更新対象の行がない）。
    """
    db.execute(
        Models.follows_table.update()
        .where(
            Models.follows_table.c.follower_id == reader_pk,
            Models.follows_table.c.followed_id == target_pk,
        )
        .values(last_read_at=datetime.utcnow())
    )
    db.commit()


# --- 定型文関連 ---
def create_template(
    db: Session, template: Schemas.TemplateCreate, user_pk: int
) -> Models.MessageTemplate:
    """定型文を登録する（user_pkはusers.idの数値PK）

    同じ本文が既に登録されている場合はTemplateAlreadyExistsErrorを送出する。
    """
    db_template = Models.MessageTemplate(
        user_id=user_pk,
        content=template.content,
    )
    db.add(db_template)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise TemplateAlreadyExistsError(template.content) from e
    db.refresh(db_template)
    return db_template


def get_templates(db: Session, user_pk: int) -> list[Models.MessageTemplate]:
    """指定ユーザーの定型文を登録順で取得する"""
    return list(
        db.scalars(
            select(Models.MessageTemplate)
            .where(Models.MessageTemplate.user_id == user_pk)
            .order_by(Models.MessageTemplate.id)
        ).all()
    )


def get_template(
    db: Session, template_id: int, user_pk: int
) -> Models.MessageTemplate | None:
    
    return db.scalars(
        select(Models.MessageTemplate).where(
            Models.MessageTemplate.id == template_id,
            Models.MessageTemplate.user_id == user_pk,
        )
    ).first()


def update_template(
    db: Session, template_id: int, user_pk: int, template: Schemas.TemplateCreate
) -> Models.MessageTemplate | None:
    """定型文を更新する

    対象が存在しない、または他人のものだった場合はNoneを返す。
    """
    db_template = get_template(db, template_id, user_pk)
    if db_template is None:
        return None

    db_template.content = template.content
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise TemplateAlreadyExistsError(template.content) from e
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int, user_pk: int) -> bool:
    """定型文を削除する

    削除できた場合はTrue、対象が存在しない場合はFalseを返す。
    """
    db_template = get_template(db, template_id, user_pk)
    if db_template is None:
        return False

    db.delete(db_template)
    db.commit()
    return True
