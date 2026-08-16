import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException, Response, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.Auth import decode_access_token, get_current_user
from app.cruds import chat_crud, user_crud
from app.db import get_db
from app.models import user_model
from app.schemas import chat_schema, user_schema
from app.websocket_manager import websocket_manager

router = APIRouter(tags=["chats"])
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.getenv("ALLOW_ORIGINS", "").split(",")
    if origin.strip()
}


@router.websocket("/ws")
async def websocket_updates(websocket: WebSocket, db: Session = Depends(get_db)):
    origin = websocket.headers.get("origin")
    await websocket.accept()
    if origin and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008, reason="許可されていない接続です")
        return

    user_id = None
    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        if auth_message.get("type") != "authenticate":
            await websocket.close(code=1008, reason="認証が必要です")
            return
        try:
            user_id = decode_access_token(auth_message.get("token", ""))
        except HTTPException:
            await websocket.close(code=1008, reason="認証情報が無効です")
            return
        if user_crud.get_user(db, user_id) is None:
            await websocket.close(code=1008, reason="ユーザーが見つかりません")
            return

        websocket_manager.connect(user_id, websocket)
        await websocket.send_json({"type": "authenticated"})

        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except (TimeoutError, WebSocketDisconnect):
        pass
    finally:
        if user_id is not None:
            websocket_manager.disconnect(user_id, websocket)


@router.post("/messages", response_model=chat_schema.ChatResponse, status_code=201)
async def create_message(payload: chat_schema.ChatCreate, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = chat_crud.create_chat(db, payload, current.id)
    recipient_ids = {current.id, *(friend.id for friend in user_crud.list_friends(db, current.id))}
    await websocket_manager.send_to_users(recipient_ids, {
        "type": "message.created",
        "message": {
            "message_id": chat.id,
            "content": chat.content,
            "created_at": chat.created_at.isoformat(),
            "author": {
                "user_id": current.user_id,
                "username": current.username,
            },
        },
    })
    return chat


@router.get("/messages/timeline", response_model=list[chat_schema.ChatResponse])
def timeline(current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = [current, *user_crud.list_friends(db, current.id)]
    chats = []
    for user in users:
        chats.extend(chat_crud.message_history(db, current, user))
    return sorted(chats, key=lambda chat: (chat.created_at, chat.id), reverse=True)


@router.get("/messages/{user_id}", response_model=chat_schema.MessageHistoryResponse)
def history(user_id: str, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = user_crud.get_user_by_user_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    try:
        chats = chat_crud.message_history(db, current, target)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="友だちのメッセージのみ閲覧できます") from exc
    return {"user_id": target.user_id, "username": target.username, "is_own": target.id == current.id,
            "messages": [{"message_id": chat.id, "content": chat.content, "created_at": chat.created_at} for chat in chats]}


@router.get("/messages/{message_id}/viewers", response_model=list[chat_schema.MessageViewerResponse])
def viewers(message_id: int, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = chat_crud.message_viewers(db, message_id, current.id)
    if result is None:
        raise HTTPException(status_code=404, detail="メッセージが見つかりません")
    return result


@router.get("/inbox", response_model=list[user_schema.FriendResponse])
@router.get("/follows", response_model=list[user_schema.FriendResponse], include_in_schema=False)
def inbox(current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return chat_crud.inbox(db, current)


@router.get("/templates", response_model=list[chat_schema.TemplateResponse])
def templates(current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return chat_crud.get_templates(db, current.id)


@router.post("/templates", response_model=chat_schema.TemplateResponse, status_code=201)
def add_template(payload: chat_schema.TemplateCreate, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return chat_crud.create_template(db, payload, current.id)
    except user_crud.ConflictError as exc:
        raise HTTPException(status_code=400, detail="同じ定型文が登録されています") from exc


@router.delete("/templates/{template_id}", status_code=204)
def remove_template(template_id: int, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not chat_crud.delete_template(db, template_id, current.id):
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません")
    return Response(status_code=204)


@router.put("/templates/order", status_code=204)
def reorder_templates(payload: chat_schema.TemplateReorder, current: user_model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not chat_crud.reorder_templates(db, payload.template_ids, current.id):
        raise HTTPException(status_code=400, detail="テンプレートの並び順が不正です")
    return Response(status_code=204)
