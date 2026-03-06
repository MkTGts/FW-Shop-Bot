from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    add_product_photo = State()
    add_product_price = State()
    add_product_description = State()
    add_product_composition = State()
