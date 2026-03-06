from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import async_session_factory
from database.models.order import Order as OrderModel, OrderStatus
from database.models.user import User
from keyboards.admin_keyboards import admin_orders_menu_kb, admin_order_item_kb
from services.order_service import get_orders, get_order_with_items, set_order_status
from utils.notifications import format_order_items, format_order_short

from handlers.admin.admin_menu import is_admin

router = Router(name="admin_orders")


async def _refresh_order_detail_message(callback: CallbackQuery, order_id: int) -> bool:
    """Обновляет сообщение с деталями заказа после смены статуса."""
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await get_order_with_items(session, order_id)
        if not result:
            return False
        order, items = result
        res = await session.execute(select(User).where(User.id == order.user_id))
        user = res.scalar_one()

    text = format_order_short(order, user) + "\n\n" + format_order_items(items)
    kb = admin_order_item_kb(order.id, order.status.value).as_markup()
    try:
        await callback.message.edit_text(text, reply_markup=kb)
        return True
    except Exception:
        return False


STATUS_LABELS = {
    OrderStatus.UNPAID: "НЕ ОПЛАЧЕН",
    OrderStatus.PAID: "ОПЛАЧЕН",
    OrderStatus.SENT: "ОТПРАВЛЕН",
    OrderStatus.COMPLETED: "ВЫПОЛНЕН",
}


def _format_order_line(order) -> str:
    status = STATUS_LABELS.get(order.status, order.status.value)
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


@router.callback_query(F.data == "admin_orders_sent")
async def admin_orders_sent(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    async with async_session_factory() as session:
        orders = await get_orders(session, status=OrderStatus.SENT)
    if not orders:
        await callback.message.answer("Отправленных заказов пока нет.")
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
    text = "Отправленные заказы:\n\n" + "\n\n".join(text_parts)
    await callback.message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "admin_orders_completed")
async def admin_orders_completed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    async with async_session_factory() as session:
        orders = await get_orders(session, status=OrderStatus.COMPLETED)
    if not orders:
        await callback.message.answer("Выполненных заказов пока нет.")
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
    text = "Выполненные заказы:\n\n" + "\n\n".join(text_parts)
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
    kb = admin_order_item_kb(order.id, order.status.value).as_markup()
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("admin_confirm_payment:"))
async def admin_confirm_payment(callback: CallbackQuery):
    """Подтверждение оплаты по скриншоту от пользователя."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        order = await set_order_status(session, order_id, OrderStatus.PAID)
    if order:
        await callback.answer("Оплата подтверждена ✅", show_alert=True)
        suffix = "\n\n✅ ОПЛАТА ПОДТВЕРЖДЕНА"
        try:
            caption = callback.message.caption or ""
            await callback.message.edit_caption(
                caption=caption + suffix,
                reply_markup=None,
            )
        except Exception:
            try:
                text = callback.message.text or ""
                await callback.message.edit_text(
                    text=text + suffix,
                    reply_markup=None,
                )
            except Exception:
                pass
    else:
        await callback.answer("Заказ не найден", show_alert=True)


@router.callback_query(F.data.startswith("admin_order_mark_paid:"))
async def admin_order_mark_paid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        await set_order_status(session, order_id, OrderStatus.PAID)
    await callback.answer("Статус изменён")
    await _refresh_order_detail_message(callback, order_id)


@router.callback_query(F.data.startswith("admin_order_mark_unpaid:"))
async def admin_order_mark_unpaid(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        await set_order_status(session, order_id, OrderStatus.UNPAID)
    await callback.answer("Статус изменён")
    await _refresh_order_detail_message(callback, order_id)


@router.callback_query(F.data.startswith("admin_order_mark_sent:"))
async def admin_order_mark_sent(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        await set_order_status(session, order_id, OrderStatus.SENT)
    await callback.answer("Заказ отмечен как отправленный 📦")
    await _refresh_order_detail_message(callback, order_id)


@router.callback_query(F.data.startswith("admin_order_mark_completed:"))
async def admin_order_mark_completed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    _, oid_str = callback.data.split(":", 1)
    order_id = int(oid_str)
    async with async_session_factory() as session:
        await set_order_status(session, order_id, OrderStatus.COMPLETED)
    await callback.answer("Заказ выполнен ✅")
    await _refresh_order_detail_message(callback, order_id)


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
