import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # DBができれば削除
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db

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


class RegisterInput(BaseModel):
    id: int | str  # コレが何か分からない
    username: str
    password: str


class LoginInput(BaseModel):
    id: int | str  # RegisterInputと同様
    password: str


@app.get("/")
def root():
    return {"message": "Hello Hackathon"}


@app.post("/register")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    # ユーザーをDBに保存する
    pass


@app.post("/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    # idとpasswordが一致するユーザーがいるか確認する
    # 一致すれば {"message": "ログイン成功"} のような簡易的な返答がいいかも
    pass
