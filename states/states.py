from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    full_name = State()
    phone     = State()


class ExamBooking(StatesGroup):
    selecting_type = State()
    selecting_date = State()
    confirming     = State()


class AdminStates(StatesGroup):
    # Exam type
    adding_type_name = State()

    # Exam date
    adding_date_type     = State()
    adding_date_value    = State()
    adding_date_location = State()
    adding_date_seats    = State()

    # Broadcast
    broadcast_text    = State()
    broadcast_confirm = State()
