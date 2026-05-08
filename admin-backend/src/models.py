"""SQLAlchemy models for admin management."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from src.database import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # "admin" or "user"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class VectorDatabase(Base):
    """Managed vector database profile for the admin console."""

    __tablename__ = "vector_databases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    store_type = Column(String(20), nullable=False)  # chroma / faiss / milvus
    description = Column(String(500), default="", nullable=False)

    # Path-based stores
    persist_path = Column(String(255), nullable=True)

    # Network-based stores
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)

    # Optional logical grouping
    collection_prefix = Column(String(100), nullable=True)

    is_default = Column(Boolean, default=False, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    last_status = Column(String(20), default="unknown", nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    last_error = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VectorDatabase(id={self.id}, name='{self.name}', type='{self.store_type}')>"
