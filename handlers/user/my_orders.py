from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database.db import async_session_factory
from database.models.order import OrderStatus
from services.order_service import get_user_orders, get_order_with_items
from services.user_service import get_user_by_telegram_id
from states.order_states import OrderStates
from utils.notifications import format_order_items, format_order_short

router = Router(name="user_my_orders")


def _format_order_line(order) -> str:
    status = "✅ Оплачен" if order.status == OrderStatus.PAID else "⏳ Неоплачен"
    delivery = "Самовывоз" if order.delivery_type.value == "pickup" else "Доставка"
    return (
        f"Заказ #{order.id} | {status}\n"
        f"Тип: {delivery} | Сумма: {order.total_price} ₽\n"
        f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@router.message(F.text == "Мои заказы")
async def show_my_orders(message: Message):
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь через /start.")
            return
        orders = await get_user_orders(session, user.id)

    if not orders:
        await message.answer("У вас пока нет заказов.")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    text_parts = []
    for order in orders[:20]:
        text_parts.append(_format_order_line(order))
        kb.button(
            text=f"Подробнее #{order.id}",
            callback_data=f"user_order_detail:{order.id}",
        )
    kb.adjust(1)
    text = "Ваши заказы:\n\n" + "\n\n".join(text_parts)
    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("user_order_detail:"))
async def user_order_detail(callback: CallbackQuery):
    await callback.answer()
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)

    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer("Пожалуйста, сначала зарегистрируйтесь через /start.")
            return
        result = await get_order_with_items(session, order_id)
        if not result:
            await callback.message.answer("Заказ не найден.")
            return
        order, items = result
        if order.user_id != user.id:
            await callback.message.answer("Это не ваш заказ.")
            return
        from sqlalchemy import select
        from database.models.user import User

        res = await session.execute(select(User).where(User.id == order.user_id))
        order_user = res.scalar_one()

    text = format_order_short(order, order_user) + "\n\n" + format_order_items(items)

    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    if order.status == OrderStatus.UNPAID:
        kb.button(
            text="💳 Оплатить",
            callback_data=f"user_pay_order:{order.id}",
        )
    kb.button(text="🔙 К списку заказов", callback_data="user_back_to_orders")
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "user_back_to_orders")
async def user_back_to_orders(callback: CallbackQuery):
    await callback.answer()
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.edit_text("Пожалуйста, сначала зарегистрируйтесь через /start.")
            return
        orders = await get_user_orders(session, user.id)

    if not orders:
        await callback.message.edit_text("У вас пока нет заказов.")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    text_parts = []
    for order in orders[:20]:
        text_parts.append(_format_order_line(order))
        kb.button(
            text=f"Подробнее #{order.id}",
            callback_data=f"user_order_detail:{order.id}",
        )
    kb.adjust(1)
    text = "Ваши заказы:\n\n" + "\n\n".join(text_parts)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("user_pay_order:"))
async def user_pay_order_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)

    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer("Пожалуйста, сначала зарегистрируйтесь через /start.")
            return
        result = await get_order_with_items(session, order_id)
        if not result:
            await callback.message.answer("Заказ не найден.")
            return
        order, _ = result
        if order.user_id != user.id:
            await callback.message.answer("Это не ваш заказ.")
            return
        if order.status == OrderStatus.PAID:
            await callback.message.answer("Этот заказ уже оплачен.")
            return

    await state.set_state(OrderStates.wait_payment)
    await state.update_data(order_id=order_id)

    payment_text = (
        f"Оплата заказа #{order.id}\n"
        f"Сумма к оплате: {order.total_price} ₽\n\n"
        f"Переведите деньги на номер: {settings.payment_phone}\n\n"
        "После оплаты отправьте сюда скриншот подтверждения перевода."
    )
    await callback.message.answer(payment_text)
