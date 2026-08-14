from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import cruds, models, schemas
from app.Auth import get_current_user
from app.db import get_db

router = APIRouter(tags=["messages"])


@router.post("/messages", response_model=schemas.PostResponse, status_code=201)
def create_message(payload: schemas.PostCreate, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cruds.create_post(db, payload, current.id)


@router.get("/messages/timeline", response_model=list[schemas.PostResponse])
def timeline(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = [current, *cruds.list_friends(db, current.id)]
    posts = []
    for user in users:
        posts.extend(cruds.message_history(db, current, user))
    return sorted(posts, key=lambda post: (post.created_at, post.id), reverse=True)


@router.get("/messages/{user_id}", response_model=schemas.MessageHistoryResponse)
def history(user_id: str, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = cruds.get_user_by_user_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    try:
        posts = cruds.message_history(db, current, target)
    except PermissionError:
        raise HTTPException(status_code=403, detail="友だちのメッセージのみ閲覧できます")
    return {"user_id": target.user_id, "username": target.username, "is_own": target.id == current.id,
            "messages": [{"message_id": p.id, "content": p.content, "created_at": p.created_at} for p in posts]}


@router.get("/messages/{message_id}/viewers", response_model=list[schemas.MessageViewerResponse])
def viewers(message_id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = cruds.message_viewers(db, message_id, current.id)
    if result is None:
        raise HTTPException(status_code=404, detail="メッセージが見つかりません")
    return result


@router.get("/inbox", response_model=list[schemas.FriendResponse])
@router.get("/follows", response_model=list[schemas.FriendResponse], include_in_schema=False)
def inbox(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cruds.inbox(db, current)


@router.get("/templates", response_model=list[schemas.TemplateResponse])
def templates(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cruds.get_templates(db, current.id)


@router.post("/templates", response_model=schemas.TemplateResponse, status_code=201)
def add_template(payload: schemas.TemplateCreate, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return cruds.create_template(db, payload, current.id)
    except cruds.ConflictError as exc:
        raise HTTPException(status_code=400, detail="同じ定型文が登録されています") from exc


@router.delete("/templates/{template_id}", status_code=204)
def remove_template(template_id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not cruds.delete_template(db, template_id, current.id):
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません")
    return Response(status_code=204)


@router.put("/templates/order", status_code=204)
def reorder_templates(payload: schemas.TemplateReorder, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not cruds.reorder_templates(db, payload.template_ids, current.id):
        raise HTTPException(status_code=400, detail="テンプレートの並び順が不正です")
    return Response(status_code=204)
