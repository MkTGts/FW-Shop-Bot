from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_menu_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Админ: Товары")],
        [KeyboardButton(text="Админ: Заказы")],
        [KeyboardButton(text="Админ: Пользователи")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Админ-меню",
    )


def admin_products_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить товар", callback_data="admin_add_product")
    kb.button(text="🗑 Удалить товар", callback_data="admin_delete_product_menu")
    kb.button(text="🔙 В админ-меню", callback_data="admin_back_main")
    kb.adjust(1)
    return kb


def admin_orders_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="Все заказы", callback_data="admin_orders_all")
    kb.button(text="Неоплаченные", callback_data="admin_orders_unpaid")
    kb.button(text="Оплаченные", callback_data="admin_orders_paid")
    kb.button(text="Отправленные", callback_data="admin_orders_sent")
    kb.button(text="Выполненные", callback_data="admin_orders_completed")
    kb.button(text="🔙 В админ-меню", callback_data="admin_back_main")
    kb.adjust(1)
    return kb


def admin_order_item_kb(order_id: int, status: str) -> InlineKeyboardBuilder:
    """Клавиатура для деталей заказа в зависимости от статуса."""
    from database.models.order import OrderStatus

    kb = InlineKeyboardBuilder()
    if status == OrderStatus.UNPAID.value:
        kb.button(
            text="✅ Отметить оплаченным",
            callback_data=f"admin_order_mark_paid:{order_id}",
        )
    elif status == OrderStatus.PAID.value:
        kb.button(
            text="↩ Отметить неоплаченным",
            callback_data=f"admin_order_mark_unpaid:{order_id}",
        )
        kb.button(
            text="📦 Отправить",
            callback_data=f"admin_order_mark_sent:{order_id}",
        )
    elif status == OrderStatus.SENT.value:
        kb.button(
            text="✅ Выполнен",
            callback_data=f"admin_order_mark_completed:{order_id}",
        )
    kb.button(text="🗑 Удалить заказ", callback_data=f"admin_order_delete:{order_id}")
    kb.adjust(1)
    return kb
