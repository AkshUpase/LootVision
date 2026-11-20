"""
Relational storage for product metadata, scan history, and settings.
SQLite for local dev; swap DATABASE_URL to a Postgres DSN for production
(SQLAlchemy makes this a one-line change).
"""
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./lootvision.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    product_id = Column(String, nullable=True)
    product_name = Column(String)
    category = Column(String)
    similarity = Column(Float)
    condition_score = Column(Integer)
    estimated_resale_price = Column(Float)
    estimated_profit = Column(Float)
    roi_percent = Column(Float)
    price_source = Column(String)


class UserSettingsRow(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, default=1)
    currency = Column(String, default="INR")
    marketplace = Column(String, default="mock_catalog")
    default_purchase_price = Column(Float, default=0.0)
    confidence_threshold = Column(Float, default=0.65)
    marketplace_fee_percent = Column(Float, default=0.10)
    shipping_estimate = Column(Float, default=100.0)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()
