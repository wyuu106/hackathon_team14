import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # Schemas.pyで実装待ち
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import Base, engine, get_db
from app import Schemas, Crud, Auth, Models
from app.Crud import UsernameAlreadyExistsError
from app.Auth import create_access_token, get_current_user


# Schemas.pyに追記して欲しい？Discord見て判断
# class UserLogin(BaseModel):
#     user_id: str  # ユーザー識別子
#     password: str
# あと、DB系のファイルインポートにて、相対パスのfrom app入れる。

# Crud.pyに追記(変更)
# from app import Models, Schemas

# Models.pyに追記(変更)
# from app.db import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = os.getenv("ALLOW_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello Hackathon"}


# ユーザー登録
@app.post("/register", response_model=Schemas.UserResponse)
def register(user: Schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = Crud.create_user(db, user)
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=400, detail="このユーザーIDは既に使われています"
        )

    return new_user


# ユーザーログイン
@app.post("/login")
def login(
    user: Schemas.UserLogin, db: Session = Depends(get_db)
):  # ID(文字列) ログイン
    login_user = Crud.get_user_by_user_id(db, user.user_id)

    if login_user is None:
        raise HTTPException(
            status_code=400, detail="usernameまたはpasswordが間違っています"
        )

    if not Crud.verify_password(user.password, login_user.password_hash):
        raise HTTPException(
            status_code=400, detail="usernameまたはpasswordが間違っています"
        )

    access_token = create_access_token(data={"sub": str(login_user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


# メッセージ作成
@app.post("/messages", response_model=Schemas.PostResponse)
def post_messages(
    post: Schemas.PostCreate,
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_post = Crud.create_post(db, post, current_user.id)
    return new_post


# メッセージ受信
# TODO:現行のフロントでは呼び出されない可能性高
@app.get("/messages/timeline", response_model=list[Schemas.PostResponse])
def get_messages(
    current_user: Models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return Crud.get_timeline(db, current_user.id)


# メッセージ受信(一個人)
@app.get("/message/{user_id}")
def get_user_messages(
    user_id: str,
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user = Crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # TODO:フォロー中の相手かどうかのチェックが本来は必要
    # 現状は、ログインさえしていればURLの書き換えで誰でも見れる
    # if user_id != current_user.id and not Crud.is_following(db, current_user.id, user_id):
    #   raise HTTPException(status_code=403, detail="このユーザーの投稿を閲覧する権限がありません")

    posts = db.scalars(
        select(Models.Post)
        .where(Models.Post.user_id == user_id)
        .order_by(Models.Post.created_at.desc())
    ).all()

    return {
        "user_id": target_user.user_id,
        "username": target_user.username,
        "messages": [
            {
                "message_id": p.id,
                "content": p.content,
                "created_at": p.created_at,
            }
            for p in posts
        ],
    }


# フォロー中のユーザー取得
@app.get("/follows")
def get_following_users(
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    followed_ids = db.scalars(
        select(Models.follows_table.c.followed_id).where(
            Models.follows_table.c.follower_id == current_user.id
        )
    ).all()

    result = []
    for followed_id in followed_ids:
        user = Crud.get_user(db, followed_id)
        if user is None:
            continue

        latest_post = db.scalars(
            select(Models.Post)
            .where(Models.Post.user_id == followed_id)
            .order_by(Models.Post.created_at.desc())
        ).first()

        result.append(
            {
                "user_id": user.user_id,
                "username": user.username,
                "read_status": True,
                # TODO: 既読機能は未実装のため仮でTrue固定
                "latest_message": latest_post.content if latest_post else None,
            }
        )

    return result


# フォロー関係


# ユーザー検索
@app.get("/users/{user_id}")
def search_user(
    user_id: str,
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user = Crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    if Crud.is_following(db, current_user.id, user_id):
        follow_status = "following"
    else:
        follow_status = "not_following"

    return {
        "user_id": target_user.user_id,
        "username": target_user.username,
        "follow_status": follow_status,
    }


# フォロー
@app.post("/follow/{user_id}")
def follow(
    user_id: str,
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user = Crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    try:
        Crud.follow_user(db, follower_id=current_user.id, followed_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "フォローしました"}


# フォロー削除


@app.delete("/follow/{user_id}")
def unfollow(
    user_id: str,
    current_user: Models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    target_user = Crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    follow_row = db.execute(
        select(Models.follows_table).where(
            Models.follows_table.c.follower_id == current_user.id,
            Models.follows_table.c.followed_id == user_id,
        )
    ).first()

    if follow_row is None:
        raise HTTPException(status_code=404, detail="フォローしていません")

    db.execute(
        Models.follows_table.delete().where(
            Models.follows_table.c.follower_id == current_user.id,
            Models.follows_table.c.followed_id == user_id,
        )
    )
    db.commit()
    return {"message": "フォローを解除しました"}
