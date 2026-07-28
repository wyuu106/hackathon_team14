import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import Schemas, Crud
from Crud import EmailAlreadyExistsError
from pydantic import BaseModel  # Schemas.pyで実装待ち
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db


# 消したい部分
class UserLogin(BaseModel):  # フロント側とは乖離しているemailがid
    email: EmailStr
    password: str


# ここまで

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
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=400, detail="このメールアドレスは既に登録されています"
        )

    return new_user


# ユーザーログイン
@app.post("/login", response_model=Schemas.UserResponse)
def login(
    user: Schemas.UserLogin, db: Session = Depends(get_db)
):  # IDかEmailかで話が変わってくる。
    login_user = Crud.get_user_by_email(db, user.email)

    if login_user is None:
        raise HTTPException(
            status_code=400, detail="emailまたはpasswordが間違っています"
        )

    if not Crud.verify_password(user.password, login_user.password_hash):
        raise HTTPException(
            status_code=400, detail="emailまたはpasswordが間違っています"
        )

    return login_user
