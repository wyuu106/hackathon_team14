from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import cruds, schemas
from app.Auth import create_access_token
from app.db import get_db

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return cruds.create_user(db, payload)
    except cruds.UserIdAlreadyExistsError:
        raise HTTPException(status_code=400, detail="このIDは既に使用されています")


@router.post("/login")
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = cruds.get_user_by_user_id(db, payload.user_id)
    if user is None or not cruds.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="IDまたはパスワードが間違っています")
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}
