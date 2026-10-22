from aiogram.fsm.state import State, StatesGroup


class CreateShopStates(StatesGroup):
    waiting_name = State()


class CreateProductStates(StatesGroup):
    waiting_photo = State()
    choosing_shop = State()
