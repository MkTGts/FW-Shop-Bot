from aiogram import Router, F
from aiogram.types import Message

from database.db import async_session_factory
from services.user_service import get_all_users

from handlers.admin.admin_menu import is_admin

router = Router(name="admin_users")


async def show_all_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return

    async with async_session_factory() as session:
        users = await get_all_users(session)

    if not users:
        await message.answer("Пользователей пока нет.")
        return

    lines = []
    for user in users:
        lines.append(
            f"ID: {user.id}\n"
            f"TG ID: {user.telegram_id}\n"
            f"Имя: {user.name}\n"
            f"Телефон: {user.phone}\n"
            f"Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )

    text = "Список пользователей:\n\n" + "\n".join(lines)
    await message.answer(text)
