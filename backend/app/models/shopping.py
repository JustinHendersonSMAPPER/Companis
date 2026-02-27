from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShoppingCart(Base):
    __tablename__ = "shopping_carts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    household_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), default="My Shopping List")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list[ShoppingCartItem]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class ShoppingCartItem(Base):
    __tablename__ = "shopping_cart_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("shopping_carts.id", ondelete="CASCADE"), nullable=False
    )
    ingredient_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ingredients.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_purchased: Mapped[bool] = mapped_column(default=False, index=True)
    added_from_recipe_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    cart: Mapped[ShoppingCart] = relationship(back_populates="items")
