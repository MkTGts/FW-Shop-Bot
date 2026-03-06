from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.db import async_session_factory
from keyboards.admin_keyboards import admin_products_menu_kb
from services.product_service import get_all_products, create_product, delete_product
from states.admin_states import AdminStates

from handlers.admin.admin_menu import is_admin

router = Router(name="admin_products")


@router.callback_query(F.data == "admin_back_main")
async def admin_back_main_cb(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_text("Админ-меню")


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    await state.set_state(AdminStates.add_product_photo)
    await callback.message.answer("Отправьте фото букета.")


@router.message(AdminStates.add_product_photo, F.photo)
async def admin_add_product_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await state.set_state(AdminStates.add_product_price)
    await message.answer(
        "Введите цену букета в рублях (целое число)."
    )


@router.message(AdminStates.add_product_photo)
async def admin_add_product_photo_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте фото букета.")


@router.message(AdminStates.add_product_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer(
            "Введите, пожалуйста, целое число (например, 2500)."
        )
        return
    price = int(text)
    await state.update_data(price=price)
    await state.set_state(AdminStates.add_product_description)
    await message.answer("Введите описание букета.")


@router.message(AdminStates.add_product_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    description = message.text.strip() if message.text else ""
    if not description:
        await message.answer("Введите, пожалуйста, не пустое описание.")
        return
    await state.update_data(description=description)
    await state.set_state(AdminStates.add_product_composition)
    await message.answer(
        "Введите состав букета (можно оставить пустым, отправив «-»)."
    )


@router.message(AdminStates.add_product_composition)
async def admin_add_product_composition(message: Message, state: FSMContext):
    composition = message.text.strip() if message.text else ""
    if composition == "-":
        composition = ""

    data = await state.get_data()
    photo = data["photo"]
    price = data["price"]
    description = data["description"]

    async with async_session_factory() as session:
        product = await create_product(
            session=session,
            photo_file_id=photo,
            price=price,
            description=description,
            composition=composition,
        )

    await state.clear()
    await message.answer(
        f"Товар успешно создан!\n"
        f"Букет №{product.number}\n"
        f"Цена: {product.price} ₽\n"
        f"Описание: {product.description}\n"
        f"Состав: {product.composition or 'не указан'}",
        reply_markup=admin_products_menu_kb().as_markup(),
    )


@router.callback_query(F.data == "admin_delete_product_menu")
async def admin_delete_product_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    async with async_session_factory() as session:
        products = await get_all_products(session)
    if not products:
        await callback.message.answer("В каталоге нет товаров.")
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(
            text=f"Удалить букет №{product.number}",
            callback_data=f"admin_delete_product:{product.id}",
        )
    kb.button(text="Отмена", callback_data="admin_products_cancel")
    kb.adjust(1)
    await callback.message.answer(
        "Выберите товар для удаления:",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "admin_products_cancel")
async def admin_products_cancel(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()


@router.callback_query(F.data.startswith("admin_delete_product:"))
async def admin_delete_product_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.answer()
    _, pid_str = callback.data.split(":", 1)
    product_id = int(pid_str)
    async with async_session_factory() as session:
        success = await delete_product(session, product_id)
    if success:
        await callback.message.answer("Товар удалён.")
    else:
        await callback.message.answer("Не удалось найти товар.")
