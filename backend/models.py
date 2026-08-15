from sqlalchemy import String, ForeignKey, Integer, Float
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

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200))
    platform: Mapped[str] = mapped_column(String(50), default='other')
    category: Mapped[str] = mapped_column(String(120), default='')
    price: Mapped[float] = mapped_column(Float, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default='draft')

class ProductSku(Base):
    __tablename__ = 'product_skus'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    sku_code: Mapped[str] = mapped_column(String(100), index=True)
    sku_name: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default='active')

class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey('product_skus.id'), unique=True)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    locked_qty: Mapped[int] = mapped_column(Integer, default=0)
    warning_threshold: Mapped[int] = mapped_column(Integer, default=10)

class GenerationJob(Base):
    __tablename__ = 'generation_jobs'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    job_kind: Mapped[str] = mapped_column(String(40))
    job_status: Mapped[str] = mapped_column(String(30), default='pending')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

class GenerationJobEvent(Base):
    __tablename__ = 'generation_job_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('generation_jobs.id'), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    event_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
