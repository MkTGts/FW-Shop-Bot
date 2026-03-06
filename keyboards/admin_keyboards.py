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
    kb.button(text="Оплаченные", callback_data="admin_orders_paid")
    kb.button(text="Неоплаченные", callback_data="admin_orders_unpaid")
    kb.button(text="🔙 В админ-меню", callback_data="admin_back_main")
    kb.adjust(1)
    return kb


def admin_order_item_kb(order_id: int, is_paid: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if is_paid:
        kb.button(
            text="Отметить неоплаченным",
            callback_data=f"admin_order_mark_unpaid:{order_id}",
        )
    else:
        kb.button(
            text="Отметить оплаченным",
            callback_data=f"admin_order_mark_paid:{order_id}",
        )
    kb.button(text="🗑 Удалить заказ", callback_data=f"admin_order_delete:{order_id}")
    kb.adjust(1)
    return kb
