from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.models import Item, ItemCreate, ItemOut, ItemUpdate
from app.web.api.deps import CurrentUser, SessionDep

router = APIRouter()


@router.get("/", response_model=list[ItemOut])
def read_items(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items.
    """
    statement = select(Item).offset(skip).limit(limit)
    return session.exec(statement).all()


@router.get("/{id}", response_model=ItemOut)
def read_item(session: SessionDep, id: int) -> Any:
    """
    Get item by ID.
    """
    item = Item.one_by_id(session, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/fuzzy/{title}", response_model=list[ItemOut])
def read_item_fuzzy(session: SessionDep, title: str) -> Any:
    """
    Get item by fuzzy title.
    """
    pass


@router.post("/", response_model=ItemOut)
def create_item(*, session: SessionDep, item_in: ItemCreate) -> Any:
    """
    Create new item.
    """
    item = Item.create(session, source=item_in)
    if not item:
        raise HTTPException(status_code=400, detail="Item not created")
    return item


@router.post("/bulk", response_model=list[ItemOut])
def create_items(*, session: SessionDep, items_in: list[ItemCreate]) -> Any:
    """
    Create new items.
    """
    pass


@router.put("/{id}", response_model=ItemOut)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
    item_in: ItemUpdate
) -> Any:
    """
    Update an item.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item: Item = Item.one_by_id(session, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.update(session, item_in)
    return item


@router.delete("/{id}", response_model=ItemOut)
def delete_item(
    session: SessionDep,
    current_user: CurrentUser,
    id: int,
) -> Any:
    """
    Delete an item.
    """
    item: Item = Item.one_by_id(session, id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    item.delete(session)
    return item
