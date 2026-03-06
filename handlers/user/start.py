from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import settings
from database.db import async_session_factory
from services.user_service import get_user_by_telegram_id, create_user
from states.registration_states import RegistrationStates
from keyboards.user_keyboards import main_menu_kb

router = Router(name="user_start")


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    if user:
        await state.clear()
        is_admin = _is_admin(message.from_user.id)
        await message.answer(
            f"Рады снова вас видеть, {user.name}!\n"
            "Добро пожаловать в онлайн-магазин цветов 🌸",
            reply_markup=main_menu_kb(is_admin=is_admin),
        )
        return

    await state.set_state(RegistrationStates.name)
    await message.answer(
        "Здравствуйте! Добро пожаловать в наш онлайн-магазин цветов 🌸\n\n"
        "Давайте познакомимся.\n"
        "Как вас зовут?",
    )


@router.message(RegistrationStates.name)
async def registration_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.phone)
    await message.answer(
        "Отлично, спасибо!\nТеперь, пожалуйста, отправьте ваш номер телефона "
        "в формате +79991234567."
    )


@router.message(RegistrationStates.phone)
async def registration_phone(message: Message, state: FSMContext):
    phone = message.text.strip() if message.text else ""
    if not phone.startswith("+") or len(phone) < 10:
        await message.answer("Пожалуйста, введите телефон в формате +79991234567.")
        return

    data = await state.get_data()
    name = data.get("name", "Гость")

    async with async_session_factory() as session:
        await create_user(
            session=session,
            telegram_id=message.from_user.id,
            name=name,
            phone=phone,
        )

    await state.clear()
    is_admin = _is_admin(message.from_user.id)
    await message.answer(
        f"{name}, регистрация завершена! 🎉\n\n"
        "Теперь вы можете просмотреть каталог букетов и оформить заказ.",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )
