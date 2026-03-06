from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина")],
        [KeyboardButton(text="Мои заказы")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="Админ")])
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def catalog_inline_kb(products: list) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for product in products:
        text = f"№{product.number} — {product.price} ₽"
        kb.button(text=text, callback_data=f"product:{product.id}")
    kb.adjust(1)
    return kb


def order_summary_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить заказ", callback_data="order_confirm")
    kb.button(text="🔙 Вернуться в корзину", callback_data="order_back_to_cart")
    kb.adjust(1)
    return kb


def delivery_type_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚶 Самовывоз", callback_data="delivery_pickup")
    kb.button(text="🚚 Доставка", callback_data="delivery_delivery")
    kb.adjust(1)
    return kb
