from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    delivery_type = State()
    address = State()
    confirm = State()
    wait_payment = State()
