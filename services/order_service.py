from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.cart import Cart
from database.models.order import DeliveryType, Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.product import Product


async def create_order_from_cart(
    session: AsyncSession,
    user_id: int,
    delivery_type: DeliveryType,
    address: str | None,
    delivery_cost: int = 400,
) -> Optional[Order]:
    stmt = (
        select(Cart, Product)
        .join(Product, Cart.product_id == Product.id)
        .where(Cart.user_id == user_id)
    )
    result = await session.execute(stmt)
    items: List[Tuple[Cart, Product]] = list(result.all())

    if not items:
        return None

    products_total = 0
    for cart_item, product in items:
        products_total += cart_item.quantity * product.price

    total_price = products_total
    if delivery_type == DeliveryType.DELIVERY:
        total_price += delivery_cost

    order = Order(
        user_id=user_id,
        delivery_type=delivery_type,
        address=address,
        total_price=total_price,
        status=OrderStatus.UNPAID,
    )
    session.add(order)
    await session.flush()

    for cart_item, product in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price=product.price,
        )
        session.add(order_item)

    for cart_item, _ in items:
        await session.delete(cart_item)

    await session.commit()
    await session.refresh(order)
    return order


async def set_order_status(
    session: AsyncSession, order_id: int, status: OrderStatus
) -> Optional[Order]:
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return None
    order.status = status
    await session.commit()
    await session.refresh(order)
    return order


async def set_payment_screenshot(
    session: AsyncSession, order_id: int, file_id: str
) -> Optional[Order]:
    """Сохраняет скриншот оплаты. Статус меняет только админ через «Подтвердить оплату»."""
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return None
    order.payment_screenshot = file_id
    await session.commit()
    await session.refresh(order)
    return order


async def get_orders(
    session: AsyncSession, status: OrderStatus | None = None
) -> List[Order]:
    stmt = select(Order).order_by(Order.created_at.desc())
    if status is not None:
        stmt = stmt.where(Order.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_order_with_items(
    session: AsyncSession, order_id: int
) -> Optional[Tuple[Order, List[Tuple[OrderItem, Product]]]]:
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return None

    items_stmt = (
        select(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id == order_id)
    )
    items_res = await session.execute(items_stmt)
    items = list(items_res.all())
    return order, items


async def get_user_orders(session: AsyncSession, user_id: int) -> List[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_completed_stats(
    session: AsyncSession, user_id: int
) -> Tuple[int, int]:
    """Возвращает (количество выполненных заказов, общая сумма выполненных заказов)."""
    from sqlalchemy import func

    stmt = (
        select(func.count(Order.id).label("count"), func.sum(Order.total_price).label("total"))
        .where(Order.user_id == user_id)
        .where(Order.status == OrderStatus.COMPLETED)
    )
    result = await session.execute(stmt)
    row = result.one()
    count = row.count or 0
    total = row.total or 0
    return count, int(total)
