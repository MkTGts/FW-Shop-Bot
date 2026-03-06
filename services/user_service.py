from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession, telegram_id: int, name: str, phone: str
) -> User:
    user = User(telegram_id=telegram_id, name=name, phone=phone)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
    name: str | None = None,
    phone: str | None = None,
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        return user
    if name is None or phone is None:
        raise ValueError("Нельзя создать пользователя без имени и телефона")
    return await create_user(session, telegram_id, name, phone)


async def get_all_users(session: AsyncSession) -> List[User]:
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())
