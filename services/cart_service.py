from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.cart import Cart
from database.models.product import Product


async def get_cart_with_products(
    session: AsyncSession, user_id: int
) -> List[Tuple[Cart, Product]]:
    stmt = (
        select(Cart, Product)
        .join(Product, Cart.product_id == Product.id)
        .where(Cart.user_id == user_id)
        .order_by(Product.number.asc())
    )
    result = await session.execute(stmt)
    return list(result.all())


async def add_to_cart(
    session: AsyncSession, user_id: int, product_id: int, quantity: int = 1
) -> None:
    stmt = select(Cart).where(
        Cart.user_id == user_id, Cart.product_id == product_id
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        session.add(cart_item)
    await session.commit()


async def change_quantity(
    session: AsyncSession, user_id: int, product_id: int, delta: int
) -> None:
    stmt = select(Cart).where(
        Cart.user_id == user_id, Cart.product_id == product_id
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        return
    cart_item.quantity += delta
    if cart_item.quantity <= 0:
        await session.delete(cart_item)
    await session.commit()


async def remove_item(
    session: AsyncSession, user_id: int, product_id: int
) -> None:
    stmt = select(Cart).where(
        Cart.user_id == user_id, Cart.product_id == product_id
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        return
    await session.delete(cart_item)
    await session.commit()


async def clear_cart(session: AsyncSession, user_id: int) -> None:
    stmt = select(Cart).where(Cart.user_id == user_id)
    result = await session.execute(stmt)
    for item in result.scalars().all():
        await session.delete(item)
    await session.commit()


async def calculate_cart_total(session: AsyncSession, user_id: int) -> int:
    items = await get_cart_with_products(session, user_id)
    total = 0
    for cart_item, product in items:
        total += cart_item.quantity * product.price
    return total
