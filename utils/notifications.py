from typing import List, Tuple

from aiogram import Bot

from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.product import Product
from database.models.user import User


def format_order_short(
    order: Order,
    user: User,
    completed_orders_count: int | None = None,
    completed_orders_total: int | None = None,
) -> str:
    status_map = {
        "UNPAID": "НЕ ОПЛАЧЕН",
        "PAID": "ОПЛАЧЕН",
        "SENT": "ОТПРАВЛЕН",
        "COMPLETED": "ВЫПОЛНЕН",
    }
    status = status_map.get(order.status.value, order.status.value)
    delivery = "Самовывоз" if order.delivery_type.value == "pickup" else "Доставка"
    text = (
        f"Заказ #{order.id}\n"
        f"Статус: {status}\n"
        f"Пользователь: {user.name}\n"
        f"ID: {user.id} | TG: {user.telegram_id}\n"
        f"Телефон: {user.phone}\n"
    )
    if completed_orders_count is not None and completed_orders_total is not None:
        text += (
            f"Выполнено заказов: {completed_orders_count} "
            f"на сумму {completed_orders_total} ₽\n"
        )
    text += f"Тип доставки: {delivery}\n" f"Сумма: {order.total_price} ₽\n"
    if order.address:
        text += f"Адрес: {order.address}\n"
    return text


def format_order_items(items: List[Tuple[OrderItem, Product]]) -> str:
    lines = []
    for item, product in items:
        desc = product.description[:40] + "..." if len(product.description) > 40 else product.description
        line = (
            f"№{product.number}: {desc}\n"
            f"  {item.quantity} шт. × {item.price} ₽ = {item.quantity * item.price} ₽"
        )
        lines.append(line)
    return "\n".join(lines)


async def notify_new_order(
    bot: Bot,
    admin_ids: List[int],
    order: Order,
    user: User,
    items: List[Tuple[OrderItem, Product]],
    delivery_cost: int,
    products_total: int,
    completed_orders_count: int | None = None,
    completed_orders_total: int | None = None,
) -> None:
    base = format_order_short(
        order, user,
        completed_orders_count=completed_orders_count,
        completed_orders_total=completed_orders_total,
    )
    items_text = format_order_items(items)
    text = (
        "🆕 НОВЫЙ ЗАКАЗ\n\n"
        f"{base}\n"
        f"Товары:\n{items_text}\n\n"
        f"Сумма товаров: {products_total} ₽\n"
        f"Доставка: {delivery_cost} ₽\n"
        f"Итого: {order.total_price} ₽"
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=text)
        except Exception:
            continue


def payment_confirm_kb(order_id: int):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Подтвердить оплату",
        callback_data=f"admin_confirm_payment:{order_id}",
    )
    return kb.as_markup()


async def notify_payment(
    bot: Bot,
    admin_ids: List[int],
    order: Order,
    user: User,
    items: List[Tuple[OrderItem, Product]],
    completed_orders_count: int | None = None,
    completed_orders_total: int | None = None,
) -> None:
    base = format_order_short(
        order, user,
        completed_orders_count=completed_orders_count,
        completed_orders_total=completed_orders_total,
    )
    items_text = format_order_items(items)
    text = (
        "💸 ПОЛУЧЕН СКРИНШОТ ОПЛАТЫ\n\n"
        f"{base}\n"
        f"Товары:\n{items_text}\n"
    )
    kb = payment_confirm_kb(order.id)
    for admin_id in admin_ids:
        try:
            if order.payment_screenshot:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=order.payment_screenshot,
                    caption=text,
                    reply_markup=kb,
                )
            else:
                await bot.send_message(
                    chat_id=admin_id, text=text, reply_markup=kb
                )
        except Exception:
            continue
