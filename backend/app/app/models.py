import logging
from datetime import datetime
from typing import Any, Optional, Union

from app.core.security import get_password_hash, verify_password
from pydantic import EmailStr, HttpUrl
from sqlalchemy.exc import IntegrityError, NoResultFound, OperationalError
from sqlalchemy.orm.exc import FlushError
from sqlmodel import JSON, AutoString, Column, Field, SQLModel, select


class ActiveRecordMixin:
    __config__ = None

    @property
    def primary_key(self):
        return self.__mapper__.primary_key_from_instance(self)  # type: ignore

    @classmethod
    def first(cls, session):
        statement = select(cls)
        return session.exec(statement).first()

    @classmethod
    def one_by_id(cls, session, id: int):
        obj = session.get(cls, id)
        return obj

    @classmethod
    def first_by_field(cls, session, field: str, value: Any):
        return cls.first_by_fields(session, {field: value})

    @classmethod
    def one_by_field(cls, session, field: str, value: Any):
        return cls.one_by_fields(session, {field: value})

    @classmethod
    def first_by_fields(cls, session, fields: dict):
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)
        try:
            return session.exec(statement).first()
        except NoResultFound:
            logging.error(f"{cls}: first_by_fields failed, NoResultFound")
            return None

    @classmethod
    def one_by_fields(cls, session, fields: dict):
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)
        try:
            return session.exec(statement).one()
        except NoResultFound:
            logging.error(f"{cls}: one_by_fields failed, NoResultFound")
            return None

    @classmethod
    def all_by_field(cls, session, field: str, value: Any):
        statement = select(cls).where(getattr(cls, field) == value)
        return session.exec(statement).all()

    @classmethod
    def all_by_fields(cls, session, fields: dict):
        statement = select(cls)
        for key, value in fields.items():
            statement = statement.where(getattr(cls, key) == value)
        return session.exec(statement).all()

    @classmethod
    def convert_without_saving(
        cls,
        source: Union[dict, SQLModel],
        update: Optional[dict] = None,
    ) -> SQLModel:
        if isinstance(source, SQLModel):
            obj = cls.from_orm(source, update=update)  # type: ignore
        elif isinstance(source, dict):
            obj = cls.parse_obj(source, update=update)  # type: ignore
        return obj

    @classmethod
    def create(
        cls,
        session,
        source: Union[dict, SQLModel],
        update: Optional[dict] = None,
    ) -> Optional[SQLModel]:
        obj = cls.convert_without_saving(source, update)
        if obj.save(session):
            return obj
        else:
            return None

    @classmethod
    def create_or_update(
        cls,
        session,
        source: Union[dict, SQLModel],
        update: Optional[dict] = None,
    ) -> Optional[SQLModel]:
        obj = cls.convert_without_saving(source, update)
        if obj is None:
            return None
        pk = cls.__mapper__.primary_key_from_instance(obj)  # type: ignore
        if pk[0] is not None:
            existing = session.get(cls, pk)
            if existing is None:
                return None  # Error
            else:
                existing.update(session, obj)  # Update
                return existing
        else:
            return cls.create(session, obj)  # Create

    @classmethod
    def count(cls, session) -> int:
        return len(cls.all(session))

    def refresh(self, session):
        session.refresh(self)

    def save(self, session) -> bool:
        session.add(self)
        try:
            session.commit()
            session.refresh(self)
            return True
        except (IntegrityError, OperationalError, FlushError) as e:
            logging.error(e)
            session.rollback()
            return False

    def update(self, session, source: Union[dict, SQLModel]):
        if isinstance(source, SQLModel):
            source = source.model_dump(exclude_unset=True)

        for key, value in source.items():
            setattr(self, key, value)
        self.save(session)

    def delete(self, session):
        session.delete(self)
        session.commit()

    @classmethod
    def all(cls, session):
        return session.exec(select(cls)).all()

    @classmethod
    def delete_all(cls, session):
        for obj in cls.all(session):
            obj.delete(session)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Union[str, None] = None
    subscription: Union[list[str], None] = Field(
        default=None,
        sa_column=Column(JSON),
    )


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


class UserCreateOpen(SQLModel):
    email: EmailStr
    password: str
    full_name: Union[str, None] = None


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: Union[EmailStr, None] = None
    password: Union[str, None] = None


class UserUpdateMe(SQLModel):
    password: Union[str, None] = None
    full_name: Union[str, None] = None
    email: Union[EmailStr, None] = None
    subscription: Union[list[str], None] = None


# Database model, database table inferred from class name
class User(ActiveRecordMixin, UserBase, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    hashed_password: str

    @classmethod
    def authenticate(
        cls, session, *, email: str, password: str
    ) -> Optional["User"]:
        user = User.one_by_field(session, "email", email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def create(
        cls,
        session,
        source: Union[UserCreate, UserCreateOpen],
    ) -> Optional[SQLModel]:
        obj = User(
            **source.model_dump(exclude={"password"}, exclude_unset=True),
            hashed_password=get_password_hash(source.password),
        )
        if obj.save(session):
            return obj
        else:
            return None

    def update(self, session, source: Union[dict, SQLModel]):
        if isinstance(source, SQLModel):
            source = source.model_dump(exclude_unset=True)

        if "password" in source:
            source["hashed_password"] = get_password_hash(source["password"])
            del source["password"]
        for key, value in source.items():
            setattr(self, key, value)
        self.save(session)


# Properties to return via API, id is always required
class UserOut(UserBase):
    id: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(nullable=False, unique=True)
    abstract: str = Field(nullable=False)
    keywords: Union[list[str], None] = Field(
        default=None,
        sa_column=Column(JSON),
    )
    authors: Union[list[str], None] = Field(
        default=None,
        sa_column=Column(JSON),
    )
    url: Optional[str]


# Properties to receive on item creation
class ItemCreate(ItemBase):
    url: Optional[HttpUrl] = None


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[list[str]] = None
    url: Optional[HttpUrl] = None
    is_hidden: Optional[bool] = None


# Database model, database table inferred from class name
class Item(ActiveRecordMixin, ItemBase, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    is_hidden: bool = False

    from_source: str = Field(nullable=False)
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )
    category: Union[list[str], None] = Field(
        default=None,
        sa_column=Column(JSON),
    )


# Properties to return via API, id is always required
class ItemOut(ItemBase):
    id: int


class CrawledItem(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    raw_url: str = Field(nullable=False)
    last_crawled: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )


class TokenPayload(SQLModel):
    sub: Union[int, None] = None


# Generic message
class Message(SQLModel):
    message: str


class NewPassword(SQLModel):
    token: str
    new_password: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
