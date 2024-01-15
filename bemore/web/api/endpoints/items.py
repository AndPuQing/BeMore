from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from bemore.crud.crud_item import item as crud
from bemore.web.api.deps import CurrentUser, SessionDep
from bemore.models import Item, ItemCreate, ItemOut, ItemUpdate

router = APIRouter()


@router.get("/", response_model=list[ItemOut])
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> list[ItemOut]:
    """
    Retrieve items.
    """
    if current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    statement = select(Item).offset(skip).limit(limit)
    return session.exec(statement).all()


@router.get("/{id}", response_model=ItemOut)
def read_item(session: SessionDep, id: int) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/fuzzy/{title}", response_model=list[ItemOut])
def read_item_fuzzy(session: SessionDep, title: str) -> Any:
    """
    Get item by fuzzy title.
    """
    statement = crud.get_by_fuzzy_title(session, title=title)
    return statement


@router.post("/", response_model=ItemOut)
def create_item(*, session: SessionDep, item_in: ItemCreate) -> Any:
    """
    Create new item.
    """
    item = crud.create(session, obj_in=item_in)
    return item


@router.post("/bulk", response_model=list[ItemOut])
def create_items(*, session: SessionDep, items_in: list[ItemCreate]) -> Any:
    """
    Create new items.
    """
    items = crud.create_bulk(session, objs_in=items_in)
    return items


@router.put("/{id}", response_model=ItemOut)
def update_item(
    *, session: SessionDep, current_user: CurrentUser, id: int, item_in: ItemUpdate
) -> Any:
    """
    Update an item.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = crud.get(session, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = crud.update(session, db_obj=item, obj_in=item_in)
    return item


@router.delete("/{id}", response_model=ItemOut)
def delete_item(session: SessionDep, current_user: CurrentUser, id: int) -> ItemOut:
    """
    Delete an item.
    """
    item = crud.get(session, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item = crud.remove(session, id=id)
    return item
