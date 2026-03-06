from aiogram.utils.keyboard import InlineKeyboardBuilder


def cart_inline_kb(cart_items) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for cart_item, product in cart_items:
        kb.button(
            text=f"➖ №{product.number}",
            callback_data=f"cart_dec:{product.id}",
        )
        kb.button(
            text=f"{cart_item.quantity} шт.",
            callback_data="cart_ignore",
        )
        kb.button(
            text=f"➕ №{product.number}",
            callback_data=f"cart_inc:{product.id}",
        )
        kb.button(
            text=f"❌ Удалить №{product.number}",
            callback_data=f"cart_remove:{product.id}",
        )
    if cart_items:
        kb.button(text="🧹 Очистить корзину", callback_data="cart_clear")
        kb.button(text="🧾 Оформить заказ", callback_data="cart_checkout")
    kb.button(text="🔙 В каталог", callback_data="cart_back_to_catalog")
    kb.adjust(3)
    return kb


def product_card_kb(product_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🛒 В корзину",
        callback_data=f"add_to_cart:{product_id}",
    )
    kb.button(
        text="🔙 Назад к каталогу",
        callback_data="back_to_catalog",
    )
    kb.adjust(1)
    return kb
