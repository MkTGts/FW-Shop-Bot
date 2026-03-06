from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import async_session_factory
from keyboards.cart_keyboards import cart_inline_kb
from services.cart_service import (
    get_cart_with_products,
    change_quantity,
    remove_item,
    clear_cart,
    calculate_cart_total,
)
from services.user_service import get_user_by_telegram_id

router = Router(name="user_cart")


async def _render_cart_text(user_id: int) -> tuple[str, list]:
    async with async_session_factory() as session:
        cart_items = await get_cart_with_products(session, user_id)
        total = await calculate_cart_total(session, user_id)

    if not cart_items:
        return "Ваша корзина пуста 🛒", []

    lines = ["Ваша корзина:"]
    for cart_item, product in cart_items:
        desc = (
            product.description[:60] + "..."
            if len(product.description) > 60
            else product.description
        )
        line = (
            f"№{product.number}\n"
            f"{desc}\n"
            f"Цена: {product.price} ₽\n"
            f"Количество: {cart_item.quantity}\n"
            f"Сумма: {cart_item.quantity * product.price} ₽\n"
        )
        lines.append(line)

    lines.append(f"\nИтого по корзине: {total} ₽")
    text = "\n".join(lines)
    return text, cart_items


@router.message(F.text == "Корзина")
async def show_cart(message: Message):
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start.")
            return

    text, cart_items = await _render_cart_text(user.id)
    kb = cart_inline_kb(cart_items).as_markup()
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("cart_inc:"))
async def cart_inc(callback: CallbackQuery):
    await callback.answer()
    _, product_id_str = callback.data.split(":", 1)
    product_id = int(product_id_str)
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer(
                "Пожалуйста, сначала зарегистрируйтесь через /start."
            )
            return
        await change_quantity(session, user.id, product_id, delta=1)

    text, cart_items = await _render_cart_text(user.id)
    kb = cart_inline_kb(cart_items).as_markup()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("cart_dec:"))
async def cart_dec(callback: CallbackQuery):
    await callback.answer()
    _, product_id_str = callback.data.split(":", 1)
    product_id = int(product_id_str)
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer(
                "Пожалуйста, сначала зарегистрируйтесь через /start."
            )
            return
        await change_quantity(session, user.id, product_id, delta=-1)

    text, cart_items = await _render_cart_text(user.id)
    kb = cart_inline_kb(cart_items).as_markup()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("cart_remove:"))
async def cart_remove_cb(callback: CallbackQuery):
    await callback.answer()
    _, product_id_str = callback.data.split(":", 1)
    product_id = int(product_id_str)
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer(
                "Пожалуйста, сначала зарегистрируйтесь через /start."
            )
            return
        await remove_item(session, user.id, product_id)

    text, cart_items = await _render_cart_text(user.id)
    kb = cart_inline_kb(cart_items).as_markup()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "cart_clear")
async def cart_clear_cb(callback: CallbackQuery):
    await callback.answer()
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer(
                "Пожалуйста, сначала зарегистрируйтесь через /start."
            )
            return
        await clear_cart(session, user.id)

    text, cart_items = await _render_cart_text(user.id)
    kb = cart_inline_kb(cart_items).as_markup()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "cart_ignore")
async def cart_ignore_cb(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "cart_back_to_catalog")
async def cart_back_to_catalog_cb(callback: CallbackQuery):
    await callback.answer()
    from handlers.user.catalog import show_catalog

    fake_message = callback.message
    fake_message.from_user = callback.from_user
    await show_catalog(fake_message)
