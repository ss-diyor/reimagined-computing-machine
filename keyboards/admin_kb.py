from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📚 Imtihon turlari"),
                KeyboardButton(text="📅 Imtihon sanalari"))
    builder.row(KeyboardButton(text="👥 Ro'yxatlar"),
                KeyboardButton(text="📊 Statistika"))
    builder.row(KeyboardButton(text="📢 Xabar yuborish"))
    builder.row(KeyboardButton(text="🔙 Asosiy menyu"))
    return builder.as_markup(resize_keyboard=True)


def exam_types_manage_kb(exam_types) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for et in exam_types:
        icon = "✅" if et['is_active'] else "❌"
        builder.row(InlineKeyboardButton(
            text=f"{icon} {et['name']}",
            callback_data=f"admin_type:{et['id']}"
        ))
    builder.row(InlineKeyboardButton(text="➕ Yangi tur qo'shish", callback_data="admin_add_type"))
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_back"))
    return builder.as_markup()


def exam_type_actions_kb(type_id: int, is_active: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "❌ O'chirish (deaktiv)" if is_active else "✅ Yoqish (aktiv)"
    builder.row(
        InlineKeyboardButton(text=toggle_text,     callback_data=f"admin_toggle_type:{type_id}"),
        InlineKeyboardButton(text="🗑 Butunlay o'chirish", callback_data=f"admin_delete_type:{type_id}"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_types_list"))
    return builder.as_markup()


def exam_dates_manage_kb(exam_dates) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ed in exam_dates:
        seats_left = ed['available_seats'] - ed['registered_count']
        status = "🟢" if seats_left > 0 else "🔴"
        builder.row(InlineKeyboardButton(
            text=f"{status} {ed['type_name']} | {ed['exam_date']} | 👤{seats_left}/{ed['available_seats']}",
            callback_data=f"admin_date:{ed['id']}"
        ))
    builder.row(InlineKeyboardButton(text="➕ Yangi sana qo'shish", callback_data="admin_add_date"))
    builder.row(InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin_back"))
    return builder.as_markup()


def exam_date_actions_kb(date_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🗑 Sanani o'chirish",
        callback_data=f"admin_delete_date:{date_id}"
    ))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_dates_list"))
    return builder.as_markup()


def select_type_for_date_kb(exam_types) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for et in exam_types:
        builder.row(InlineKeyboardButton(
            text=f"📚 {et['name']}",
            callback_data=f"admin_date_type:{et['id']}"
        ))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_dates_list"))
    return builder.as_markup()


def registrations_filter_kb(exam_types) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Barcha ro'yxatlar", callback_data="admin_regs_all"))
    for et in exam_types:
        builder.row(InlineKeyboardButton(
            text=f"📚 {et['name']}",
            callback_data=f"admin_regs_type:{et['id']}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back"))
    return builder.as_markup()


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, yuborish",      callback_data="admin_broadcast_confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_broadcast_cancel"),
    )
    return builder.as_markup()
