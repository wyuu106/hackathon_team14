from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import cruds, models, schemas
from app.Auth import get_current_user
from app.db import get_db

router = APIRouter(tags=["account"])


@router.get("/account", response_model=schemas.AccountResponse)
def account(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"user_id": current.user_id, "username": current.username,
            "friend_count": len(cruds.list_friends(db, current.id))}
