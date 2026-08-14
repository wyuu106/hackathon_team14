from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import cruds, models, schemas
from app.Auth import get_current_user
from app.db import get_db

router = APIRouter(tags=["friends"])


@router.get("/users/{user_id}", response_model=schemas.UserSearchResponse)
def search(user_id: str, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = cruds.get_user_by_user_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    return {"user_id": target.user_id, "username": target.username,
            "follow_status": cruds.request_status(db, current.id, target.id)}


@router.post("/friend-requests/{user_id}", status_code=201)
@router.post("/follow/{user_id}", status_code=201, include_in_schema=False)
def request_friend(user_id: str, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = cruds.get_user_by_user_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    try:
        cruds.create_friend_request(db, current.id, target.id)
    except cruds.ConflictError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "フォローリクエストを送信しました"}


@router.get("/friend-requests", response_model=list[schemas.FriendRequestResponse])
def requests(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cruds.list_friend_requests(db, current.id)


@router.post("/friend-requests/{request_id}/accept")
def accept(request_id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = cruds.get_received_request(db, request_id, current.id)
    if request is None:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")
    cruds.accept_friend_request(db, request, current.id)
    return {"message": "友だちになりました"}


@router.delete("/friend-requests/{request_id}", status_code=204)
def reject(request_id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = cruds.get_received_request(db, request_id, current.id)
    if request is None:
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")
    cruds.reject_friend_request(db, request)
    return Response(status_code=204)


@router.delete("/friend-requests/to/{user_id}", status_code=204)
def cancel(user_id: str, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = cruds.get_user_by_user_id(db, user_id)
    if target is None or not cruds.cancel_friend_request(db, current.id, target.id):
        raise HTTPException(status_code=404, detail="リクエストが見つかりません")
    return Response(status_code=204)


@router.get("/friends", response_model=list[schemas.UserResponse])
def friends(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cruds.list_friends(db, current.id)


@router.delete("/friends/{user_id}", status_code=204)
@router.delete("/follow/{user_id}", status_code=204, include_in_schema=False)
def unfriend(user_id: str, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = cruds.get_user_by_user_id(db, user_id)
    if target is None or not cruds.remove_friend(db, current.id, target.id):
        raise HTTPException(status_code=404, detail="友だちではありません")
    return Response(status_code=204)
