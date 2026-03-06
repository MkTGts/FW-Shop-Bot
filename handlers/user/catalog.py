from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import async_session_factory
from keyboards.cart_keyboards import product_card_kb
from keyboards.user_keyboards import catalog_inline_kb
from services.product_service import get_all_products, get_product_by_id
from services.cart_service import add_to_cart
from services.user_service import get_user_by_telegram_id

router = Router(name="user_catalog")


@router.message(F.text == "Каталог")
async def show_catalog(message: Message):
    async with async_session_factory() as session:
        products = await get_all_products(session)
    if not products:
        await message.answer("Каталог пока пуст. Загляните позже 💐")
        return
    kb = catalog_inline_kb(products).as_markup()
    await message.answer("Выберите букет из каталога:", reply_markup=kb)


@router.callback_query(F.data == "back_to_catalog")
@router.callback_query(F.data == "cart_back_to_catalog")
async def back_to_catalog_cb(callback: CallbackQuery):
    await callback.answer()
    async with async_session_factory() as session:
        products = await get_all_products(session)
    if not products:
        await callback.message.edit_text("Каталог пока пуст. Загляните позже 💐")
        return
    kb = catalog_inline_kb(products).as_markup()
    await callback.message.edit_text("Выберите букет из каталога:", reply_markup=kb)


@router.callback_query(F.data.startswith("product:"))
async def product_card(callback: CallbackQuery):
    await callback.answer()
    _, product_id_str = callback.data.split(":", 1)
    product_id = int(product_id_str)

    async with async_session_factory() as session:
        product = await get_product_by_id(session, product_id)

    if not product:
        await callback.message.answer("Товар не найден или был удалён.")
        return

    caption = (
        f"Букет №{product.number}\n\n"
        f"{product.description}\n\n"
        f"Цена: {product.price} ₽"
    )
    if product.composition:
        caption += f"\n\nСостав: {product.composition}"

    kb = product_card_kb(product.id).as_markup()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer_photo(
        photo=product.photo,
        caption=caption,
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart_cb(callback: CallbackQuery):
    await callback.answer()
    _, product_id_str = callback.data.split(":", 1)
    product_id = int(product_id_str)
    user_id = callback.from_user.id

    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if not user:
            await callback.message.answer(
                "Похоже, вы ещё не зарегистрированы. Нажмите /start."
            )
            return
        await add_to_cart(session, user.id, product_id, quantity=1)

    await callback.message.answer(
        "Товар добавлен в корзину 🛒\n\n"
        "Откройте «Корзина», чтобы оформить заказ."
    )
