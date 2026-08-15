import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.Auth import create_access_token, get_current_user
from app.cruds import auth_crud, user_crud
from app.db import get_db
from app.models import user_model
from app.schemas import user_schema

router = APIRouter(tags=["users"])

REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", 60))
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.getenv("ALLOW_ORIGINS", "").split(",")
    if origin.strip()
}


def validate_request_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="許可されていないリクエストです")


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/auth",
    )


def invalid_session_response(detail: str) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
    )
    clear_refresh_cookie(response)
    return response


def auth_response(user: user_model.User) -> dict:
    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": user,
    }


@router.post("/register", response_model=user_schema.UserResponse, status_code=201)
def register(payload: user_schema.UserCreate, db: Session = Depends(get_db)):
    try:
        return user_crud.create_user(db, payload)
    except user_crud.UserIdAlreadyExistsError as exc:
        raise HTTPException(status_code=400, detail="このIDは既に使用されています") from exc


@router.post("/login", response_model=user_schema.AuthResponse)
def login(
    payload: user_schema.UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    validate_request_origin(request)
    user = user_crud.get_user_by_user_id(db, payload.user_id)
    if user is None or not user_crud.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="IDまたはパスワードが間違っています")
    refresh_token, _ = auth_crud.create_refresh_session(
        db, user.id, REFRESH_TOKEN_DAYS
    )
    set_refresh_cookie(response, refresh_token)
    return auth_response(user)


@router.post("/auth/refresh", response_model=user_schema.AuthResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    validate_request_origin(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ログインが必要です")
    try:
        new_token, refresh_session = auth_crud.rotate_refresh_session(
            db, refresh_token, REFRESH_TOKEN_DAYS
        )
    except auth_crud.InvalidRefreshTokenError:
        return invalid_session_response("ログインの有効期限が切れています")
    user = user_crud.get_user(db, refresh_session.user_id)
    if user is None:
        return invalid_session_response("ログインが必要です")
    set_refresh_cookie(response, new_token)
    return auth_response(user)


@router.post("/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    validate_request_origin(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        auth_crud.revoke_refresh_token(db, refresh_token)
    clear_refresh_cookie(response)
    response.status_code = 204
    return response


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
