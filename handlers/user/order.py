from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database.db import async_session_factory
from database.models.order import DeliveryType, OrderStatus
from database.models.user import User
from keyboards.user_keyboards import delivery_type_kb, order_summary_kb
from services.cart_service import get_cart_with_products, calculate_cart_total
from services.order_service import (
    create_order_from_cart,
    get_order_with_items,
    set_payment_screenshot,
)
from services.user_service import get_user_by_telegram_id
from states.order_states import OrderStates
from utils.notifications import notify_new_order, notify_payment

router = Router(name="user_order")
DELIVERY_COST = 400


async def _build_order_preview_text(
    user_id: int,
    delivery_type: DeliveryType,
    address: str | None,
) -> tuple[str, int, int]:
    async with async_session_factory() as session:
        cart_items = await get_cart_with_products(session, user_id)
        products_total = await calculate_cart_total(session, user_id)

    if not cart_items:
        return "Корзина пуста. Невозможно оформить заказ.", 0, 0

    lines = ["Предварительный заказ:"]
    for cart_item, product in cart_items:
        desc = (
            product.description[:60] + "..."
            if len(product.description) > 60
            else product.description
        )
        line = (
            f"№{product.number}\n"
            f"{desc}\n"
            f"{cart_item.quantity} шт. × {product.price} ₽ = "
            f"{cart_item.quantity * product.price} ₽\n"
        )
        lines.append(line)

    delivery_cost = 0
    if delivery_type == DeliveryType.DELIVERY:
        delivery_cost = DELIVERY_COST
        lines.append(f"Доставка: {delivery_cost} ₽")
    else:
        lines.append("Самовывоз: 0 ₽")

    total = products_total + delivery_cost
    lines.append(f"\nСумма товаров: {products_total} ₽")
    lines.append(f"Итого к оплате: {total} ₽")

    if delivery_type == DeliveryType.DELIVERY and address:
        lines.append(f"\nАдрес доставки: {address}")

    return "\n".join(lines), products_total, delivery_cost


@router.callback_query(F.data == "cart_checkout")
async def start_order_from_cart(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer(
                "Пожалуйста, сначала зарегистрируйтесь через /start."
            )
            return
        total = await calculate_cart_total(session, user.id)
    if total == 0:
        await callback.message.answer("Ваша корзина пуста, нечего оформлять 🛒")
        return

    await state.set_state(OrderStates.delivery_type)
    await callback.message.answer(
        "Выберите тип доставки:",
        reply_markup=delivery_type_kb().as_markup(),
    )


@router.callback_query(OrderStates.delivery_type, F.data == "delivery_pickup")
async def delivery_pickup(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(delivery_type=DeliveryType.PICKUP.value)
    data = await state.get_data()
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
    text, _, _ = await _build_order_preview_text(
        user.id, DeliveryType.PICKUP, data.get("address")
    )
    await state.set_state(OrderStates.confirm)
    await callback.message.answer(text, reply_markup=order_summary_kb().as_markup())


@router.callback_query(OrderStates.delivery_type, F.data == "delivery_delivery")
async def delivery_delivery(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(delivery_type=DeliveryType.DELIVERY.value)
    await state.set_state(OrderStates.address)
    await callback.message.answer(
        "Пожалуйста, введите адрес доставки текстом."
    )


@router.message(OrderStates.address)
async def order_address(message: Message, state: FSMContext):
    address = message.text.strip() if message.text else ""
    if not address:
        await message.answer("Пожалуйста, введите корректный адрес.")
        return
    await state.update_data(address=address)
    data = await state.get_data()
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    text, _, _ = await _build_order_preview_text(
        user.id, DeliveryType.DELIVERY, address
    )
    await state.set_state(OrderStates.confirm)
    await message.answer(text, reply_markup=order_summary_kb().as_markup())


@router.callback_query(OrderStates.confirm, F.data == "order_back_to_cart")
async def order_back_to_cart(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    from handlers.user.cart import show_cart

    fake_message = callback.message
    fake_message.from_user = callback.from_user
    await show_cart(fake_message)


@router.callback_query(OrderStates.confirm, F.data == "order_confirm")
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    delivery_type_val = data.get("delivery_type")
    address = data.get("address")

    if not delivery_type_val:
        await callback.message.answer(
            "Произошла ошибка, попробуйте оформить заказ заново."
        )
        await state.clear()
        return

    delivery_type = DeliveryType(delivery_type_val)

    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer(
                "Пожалуйста, сначала зарегистрируйтесь через /start."
            )
            await state.clear()
            return

        order = await create_order_from_cart(
            session=session,
            user_id=user.id,
            delivery_type=delivery_type,
            address=address,
            delivery_cost=DELIVERY_COST,
        )
        if not order:
            await callback.message.answer(
                "Ваша корзина пуста, нечего оформлять."
            )
            await state.clear()
            return

        order_with_items = await get_order_with_items(session, order.id)
        if order_with_items:
            order_obj, items = order_with_items
            products_total = 0
            for item, product in items:
                products_total += item.quantity * item.price
            delivery_cost = (
                DELIVERY_COST
                if order_obj.delivery_type == DeliveryType.DELIVERY
                else 0
            )
            await notify_new_order(
                bot=callback.bot,
                admin_ids=settings.admin_ids,
                order=order_obj,
                user=user,
                items=items,
                delivery_cost=delivery_cost,
                products_total=products_total,
            )

    await state.set_state(OrderStates.wait_payment)
    await state.update_data(order_id=order.id)

    payment_text = (
        f"Ваш заказ #{order.id} успешно создан!\n"
        f"Сумма к оплате: {order.total_price} ₽\n\n"
        "Пожалуйста, выполните перевод на следующий номер телефона:\n"
        "<вставьте номер телефона для оплаты здесь>\n\n"
        "После оплаты отправьте сюда скриншот подтверждения перевода."
    )
    await callback.message.answer(payment_text)


@router.message(OrderStates.wait_payment, F.photo)
async def order_payment_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await message.answer(
            "Не удалось найти заказ. Попробуйте оформить заказ заново."
        )
        await state.clear()
        return

    file_id = message.photo[-1].file_id

    async with async_session_factory() as session:
        order_with_items = await get_order_with_items(session, order_id)
        if not order_with_items:
            await message.answer("Заказ не найден.")
            await state.clear()
            return
        order, items = order_with_items

        updated_order = await set_payment_screenshot(session, order.id, file_id)

        from sqlalchemy import select

        res = await session.execute(select(User).where(User.id == order.user_id))
        user = res.scalar_one()

        order_for_notify = updated_order or order
        await notify_payment(
            bot=message.bot,
            admin_ids=settings.admin_ids,
            order=order_for_notify,
            user=user,
            items=items,
        )

    await state.clear()
    await message.answer(
        "Спасибо! Мы получили ваш скриншот оплаты 💸\n"
        "Ваш заказ передан в обработку. "
        "В ближайшее время с вами свяжется оператор."
    )


@router.message(OrderStates.wait_payment)
async def order_wait_payment_non_photo(message: Message):
    await message.answer(
        "Пожалуйста, отправьте скриншот оплаты в виде фото.\n"
        "Если вы передумали, вы можете начать новый заказ позже."
    )
