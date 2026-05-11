"""
SQLAlchemy ORM models for users and calculations.

The cascade="all, delete" on the calculations relationship ensures that
deleting a User automatically removes all their calculations, enforced
at both the ORM level and the DB level via ondelete="CASCADE".
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """Represents an authenticated application user."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt digest, never plain-text
    bio = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    calculations = relationship("Calculation", back_populates="user", cascade="all, delete")


class Calculation(Base):
    """Stores a single arithmetic calculation performed by a user."""
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)   # matches OperationType enum value
    result = Column(Float, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="calculations")
