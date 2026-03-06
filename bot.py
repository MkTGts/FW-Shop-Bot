import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.db import init_db
from handlers.user import start as user_start
from handlers.user import catalog as user_catalog
from handlers.user import cart as user_cart
from handlers.user import order as user_order
from handlers.user import my_orders as user_my_orders
from handlers.admin import (
    admin_menu,
    products as admin_products,
    orders as admin_orders,
    users as admin_users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


async def main():
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Админ-роутеры первыми — приоритет для /admin и кнопок админа
    dp.include_router(admin_menu.router)
    dp.include_router(admin_products.router)
    dp.include_router(admin_orders.router)
    dp.include_router(admin_users.router)

    dp.include_router(user_start.router)
    dp.include_router(user_catalog.router)
    dp.include_router(user_cart.router)
    dp.include_router(user_order.router)
    dp.include_router(user_my_orders.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
