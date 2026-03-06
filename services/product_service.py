from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.product import Product


async def get_all_products(session: AsyncSession) -> List[Product]:
    result = await session.execute(select(Product).order_by(Product.number.asc()))
    return list(result.scalars().all())


async def get_product_by_id(
    session: AsyncSession, product_id: int
) -> Optional[Product]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def _get_first_free_number(session: AsyncSession) -> int:
    result = await session.execute(
        select(Product.number).order_by(Product.number.asc())
    )
    numbers = [row[0] for row in result.all()]
    expected = 1
    for n in numbers:
        if n == expected:
            expected += 1
        elif n > expected:
            break
    return expected


async def create_product(
    session: AsyncSession,
    photo_file_id: str,
    price: int,
    description: str,
    composition: str | None,
) -> Product:
    free_number = await _get_first_free_number(session)
    product = Product(
        number=free_number,
        photo=photo_file_id,
        price=price,
        description=description,
        composition=composition or None,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product_id: int) -> bool:
    product = await get_product_by_id(session, product_id)
    if not product:
        return False
    await session.delete(product)
    await session.commit()
    return True
