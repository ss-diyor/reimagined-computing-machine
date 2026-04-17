from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📝 Imtihonga ro'yxatdan o'tish"))
    builder.row(KeyboardButton(text="📋 Mening ro'yxatlarim"))
    builder.row(KeyboardButton(text="ℹ️ Ma'lumot"))
    return builder.as_markup(resize_keyboard=True)


def phone_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📱 Raqamimni yuborish", request_contact=True))
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def exam_types_kb(exam_types) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for et in exam_types:
        builder.row(InlineKeyboardButton(
            text=f"📚 {et['name']}",
            callback_data=f"exam_type:{et['id']}"
        ))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="user_cancel"))
    return builder.as_markup()


def exam_dates_kb(exam_dates) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ed in exam_dates:
        seats_left = ed['available_seats'] - ed['registered_count']
        builder.row(InlineKeyboardButton(
            text=f"📅 {ed['exam_date']}  |  📍 {ed['location']}  |  👤 {seats_left} joy",
            callback_data=f"exam_date:{ed['id']}"
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_types"))
    return builder.as_markup()


def confirm_kb(date_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm:{date_id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="user_cancel"),
    )
    return builder.as_markup()


def registrations_kb(registrations) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for reg in registrations:
        builder.row(InlineKeyboardButton(
            text=f"🗑 {reg['type_name']} – {reg['exam_date']} (bekor qilish)",
            callback_data=f"cancel_reg:{reg['id']}"
        ))
    return builder.as_markup()
