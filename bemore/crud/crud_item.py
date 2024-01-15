from sqlalchemy.orm import Session
from sqlmodel import col

from bemore.crud.base import CRUDBase
from bemore.models import Item
from bemore.schemas.item import ItemCreate, ItemUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    def create(self, db: Session, *, obj_in: ItemCreate) -> Item:
        db_obj = Item(
            title=obj_in.title,
            description=obj_in.description,
            keywords=obj_in.keywords,
            raw_url=obj_in.raw_url,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Item, obj_in: ItemUpdate) -> Item:
        if obj_in.title:
            db_obj.title = obj_in.title
        if obj_in.description:
            db_obj.description = obj_in.description
        if obj_in.keywords:
            db_obj.keywords = obj_in.keywords
        if obj_in.raw_url:
            db_obj.raw_url = obj_in.raw_url
        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    def get_by_id(self, db: Session, *, id: int) -> Item:
        return db.query(Item).filter(Item.id == id).first()

    def get_by_fuzzy_title(self, db: Session, *, title: str) -> list[Item]:
        return db.query(Item).filter(col("title").ilike(f"%{title}%")).all()

    def create_bulk(self, db: Session, *, objs_in: list[ItemCreate]) -> list[Item]:
        objs = [Item(**obj_in.model_dump()) for obj_in in objs_in]
        db.add_all(objs)
        db.commit()
        db.refresh(objs)
        return objs


item = CRUDItem(Item)
