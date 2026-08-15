from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.Auth import create_access_token, get_current_user
from app.cruds import user_crud
from app.db import get_db
from app.models import user_model
from app.schemas import user_schema

router = APIRouter(tags=["users"])


@router.post("/register", response_model=user_schema.UserResponse, status_code=201)
def register(payload: user_schema.UserCreate, db: Session = Depends(get_db)):
    try:
        return user_crud.create_user(db, payload)
    except user_crud.UserIdAlreadyExistsError as exc:
        raise HTTPException(status_code=400, detail="このIDは既に使用されています") from exc


@router.post("/login")
def login(payload: user_schema.UserLogin, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_user_id(db, payload.user_id)
    if user is None or not user_crud.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="IDまたはパスワードが間違っています")
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}


@router.get("/users/{user_id}", response_model=user_schema.UserSearchResponse)
def search(user_id: str, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = user_crud.get_user_by_user_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    return {"user_id": target.user_id, "username": target.username,
            "follow_status": user_crud.request_status(db, current.id, target.id)}


@router.post("/friend-requests/{user_id}", status_code=201)
@router.post("/follow/{user_id}", status_code=201, include_in_schema=False)
def request_friend(user_id: str, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = user_crud.get_user_by_user_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    try:
        user_crud.create_friend_request(db, current.id, target.id)
    except user_crud.ConflictError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "フォローリクエストを送信しました"}


@router.get("/friend-requests", response_model=list[user_schema.FriendRequestResponse])
def requests(current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_crud.list_friend_requests(db, current.id)


@router.post("/friend-requests/{request_id}/accept")
def accept(request_id: int, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = user_crud.get_received_request(db, request_id, current.id)
    if request is None:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")
    user_crud.accept_friend_request(db, request, current.id)
    return {"message": "友だちになりました"}


@router.delete("/friend-requests/{request_id}", status_code=204)
def reject(request_id: int, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = user_crud.get_received_request(db, request_id, current.id)
    if request is None:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")
    user_crud.reject_friend_request(db, request)
    return Response(status_code=204)


@router.delete("/friend-requests/to/{user_id}", status_code=204)
def cancel(user_id: str, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = user_crud.get_user_by_user_id(db, user_id)
    if target is None or not user_crud.cancel_friend_request(db, current.id, target.id):
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")
    return Response(status_code=204)


@router.get("/friends", response_model=list[user_schema.UserResponse])
def friends(current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_crud.list_friends(db, current.id)


@router.delete("/friends/{user_id}", status_code=204)
@router.delete("/follow/{user_id}", status_code=204, include_in_schema=False)
def unfriend(user_id: str, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = user_crud.get_user_by_user_id(db, user_id)
    if target is None or not user_crud.remove_friend(db, current.id, target.id):
        raise HTTPException(status_code=404, detail="友だちではありません")
    return Response(status_code=204)


@router.get("/account", response_model=user_schema.AccountResponse)
def account(current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"user_id": current.user_id, "username": current.username,
            "friend_count": len(user_crud.list_friends(db, current.id))}
