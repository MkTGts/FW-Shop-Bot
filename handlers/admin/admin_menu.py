from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from keyboards.admin_keyboards import admin_main_menu_kb

router = Router(name="admin_menu")


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
@router.message(F.text == "Админ")
async def cmd_admin(message: Message):
    if not message.from_user:
        return
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    await message.answer("Админ-меню:", reply_markup=admin_main_menu_kb())


@router.message(F.text == "Админ: Товары")
async def admin_products_menu_entry(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    from keyboards.admin_keyboards import admin_products_menu_kb

    await message.answer(
        "Управление товарами:",
        reply_markup=admin_products_menu_kb().as_markup(),
    )


@router.message(F.text == "Админ: Заказы")
async def admin_orders_menu_entry(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    from keyboards.admin_keyboards import admin_orders_menu_kb

    await message.answer(
        "Управление заказами:",
        reply_markup=admin_orders_menu_kb().as_markup(),
    )


@router.message(F.text == "Админ: Пользователи")
async def admin_users_menu_entry(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    from handlers.admin.users import show_all_users

    await show_all_users(message)
