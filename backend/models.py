from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(30), default='viewer')
    status: Mapped[str] = mapped_column(String(30), default='active')
