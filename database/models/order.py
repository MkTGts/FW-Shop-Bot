from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class OrderStatus(str, PyEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class DeliveryType(str, PyEnum):
    PICKUP = "pickup"
    DELIVERY = "delivery"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    delivery_type: Mapped[DeliveryType] = mapped_column(
        Enum(DeliveryType, name="delivery_type_enum"), nullable=False
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.UNPAID,
        nullable=False,
    )
    payment_screenshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
