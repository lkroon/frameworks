from sqlalchemy import Column, Integer, String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    display_name = Column(String)
    # Null for SSO-only accounts
    password_hash = Column(String)
    provider = Column(String, nullable=False, default="local")
    google_sub = Column(String, unique=True)
