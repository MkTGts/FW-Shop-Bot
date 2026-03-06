from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import async_session_factory
from database.models.order import Order as OrderModel, OrderStatus
from keyboards.admin_keyboards import admin_orders_menu_kb, admin_order_item_kb
from services.order_service import get_orders, get_order_with_items, set_order_status
from utils.notifications import format_order_items, format_order_short

from handlers.admin.admin_menu import is_admin

router = Router(name="admin_orders")


def _format_order_line(order) -> str:
    status = "ОПЛАЧЕН" if order.status == OrderStatus.PAID else "НЕ ОПЛАЧЕН"
    delivery = "Самовывоз" if order.delivery_type.value == "pickup" else "Доставка"
    return (
        f"Заказ #{order.id} | {status}\n"
        f"Тип доставки: {delivery}\n"
        f"Сумма: {order.total_price} ₽\n"
        f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@router.callback_query(F.data == "admin_orders_all")
async def admin_orders_all(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    async with async_session_factory() as session:
        orders = await get_orders(session)
    if not orders:
        await callback.message.answer("Заказов пока нет.")
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    text_parts = []
    for order in orders[:30]:
        text_parts.append(_format_order_line(order))
        kb.button(
            text=f"Подробнее #{order.id}",
            callback_data=f"admin_order_detail:{order.id}",
        )
    kb.button(text="🔙 В админ-меню", callback_data="admin_back_main")
    kb.adjust(1)
    text = "Список заказов:\n\n" + "\n\n".join(text_parts)
    await callback.message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "admin_orders_paid")
async def admin_orders_paid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    async with async_session_factory() as session:
        orders = await get_orders(session, status=OrderStatus.PAID)
    if not orders:
        await callback.message.answer("Оплаченных заказов пока нет.")
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    text_parts = []
    for order in orders[:30]:
        text_parts.append(_format_order_line(order))
        kb.button(
            text=f"Подробнее #{order.id}",
            callback_data=f"admin_order_detail:{order.id}",
        )
    kb.button(text="🔙 В админ-меню", callback_data="admin_back_main")
    kb.adjust(1)
    text = "Оплаченные заказы:\n\n" + "\n\n".join(text_parts)
    await callback.message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "admin_orders_unpaid")
async def admin_orders_unpaid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    async with async_session_factory() as session:
        orders = await get_orders(session, status=OrderStatus.UNPAID)
    if not orders:
        await callback.message.answer("Неоплаченных заказов пока нет.")
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    text_parts = []
    for order in orders[:30]:
        text_parts.append(_format_order_line(order))
        kb.button(
            text=f"Подробнее #{order.id}",
            callback_data=f"admin_order_detail:{order.id}",
        )
    kb.button(text="🔙 В админ-меню", callback_data="admin_back_main")
    kb.adjust(1)
    text = "Неоплаченные заказы:\n\n" + "\n\n".join(text_parts)
    await callback.message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("admin_order_detail:"))
async def admin_order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)

    async with async_session_factory() as session:
        result = await get_order_with_items(session, order_id)
        if not result:
            await callback.message.answer("Заказ не найден.")
            return
        order, items = result
        from sqlalchemy import select
        from database.models.user import User

        res = await session.execute(select(User).where(User.id == order.user_id))
        user = res.scalar_one()

    text = format_order_short(order, user) + "\n\n" + format_order_items(items)
    kb = admin_order_item_kb(
        order.id, is_paid=(order.status == OrderStatus.PAID)
    ).as_markup()
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("admin_order_mark_paid:"))
async def admin_order_mark_paid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer("Статус изменён")
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        await set_order_status(session, order_id, OrderStatus.PAID)


@router.callback_query(F.data.startswith("admin_order_mark_unpaid:"))
async def admin_order_mark_unpaid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer("Статус изменён")
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        await set_order_status(session, order_id, OrderStatus.UNPAID)


@router.callback_query(F.data.startswith("admin_order_delete:"))
async def admin_order_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer("Удалено")
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)

    async with async_session_factory() as session:
        from sqlalchemy import select

        res = await session.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        order = res.scalar_one_or_none()
        if order:
            await session.delete(order)
            await session.commit()
    await callback.message.answer(f"Заказ #{order_id} удалён.")
