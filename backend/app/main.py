import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # Schemas.pyで実装待ち
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app import Schemas, Crud, Auth
from app.Crud import UsernameAlreadyExistsError
from app.Auth import create_access_token


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
    login_user = Crud.get_user_by_username(db, user.username)

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
    post: Schemas.PostCreate, user_id: str, db: Session = Depends(get_db)
):
    new_post = Crud.create_post(db, post, user_id)
    return new_post


# メッセージ受信
@app.get("/messages/timeline", response_model=list[Schemas.PostResponse])
def get_messages(user_id: str, db: Session = Depends(get_db)):
    return Crud.get_timeline(db, user_id)
