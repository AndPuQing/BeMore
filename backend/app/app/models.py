# Contents of JWT token
from typing import List, Optional, Union

from pydantic import BaseModel, EmailStr, HttpUrl
from sqlmodel import JSON, AutoString, Column, Field, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Union[str, None] = None
    subscription: Union[list[str], None] = Field(default=None, sa_column=Column(JSON))


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


class UserUpdateMe(BaseModel):
    password: Union[str, None] = None
    full_name: Union[str, None] = None
    email: Union[EmailStr, None] = None
    subscription: Union[List[str], None] = None


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    hashed_password: str


# Properties to return via API, id is always required
class UserOut(UserBase):
    id: int


# Shared properties
class ItemBase(SQLModel):
    title: str
    description: str
    keywords: Union[list[str], None] = Field(default=None, sa_column=Column(JSON))


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str
    raw_url: Optional[HttpUrl] = None


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    raw_url: Optional[HttpUrl] = None
    is_hidden: Optional[bool] = None


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    is_hidden: bool = False
    raw_url: Optional[str]


# Properties to return via API, id is always required
class ItemOut(ItemBase):
    id: int


class TokenPayload(BaseModel):
    sub: Union[int, None] = None


# Generic message
class Message(BaseModel):
    message: str


class NewPassword(BaseModel):
    token: str
    new_password: str


# JSON payload containing access token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
