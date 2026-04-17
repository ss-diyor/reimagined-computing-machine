import re
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

import database as db
from states.states import Registration, ExamBooking
from keyboards.user_kb import (
    main_menu_kb, phone_kb, remove_kb,
    exam_types_kb, exam_dates_kb, confirm_kb, registrations_kb,
)

router = Router()
logger = logging.getLogger(__name__)


# ─── /start ─────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)

    if user:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{user['full_name']}</b>!\n\n"
            "Quyidagi menyu orqali imtihonga ro'yxatdan o'tishingiz mumkin.",
            reply_markup=main_menu_kb()
        )
    else:
        await message.answer(
            "👋 Botga xush kelibsiz!\n\n"
            "Davom etish uchun avval ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 <b>To'liq ismingizni kiriting:</b>\n"
            "<i>Masalan: Karimov Ali Valiyevich</i>",
            reply_markup=remove_kb()
        )
        await state.set_state(Registration.full_name)


# ─── Registration ────────────────────────────────────────────────────────────────

@router.message(Registration.full_name)
async def reg_full_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 5:
        await message.answer("❌ Ism juda qisqa. Iltimos, <b>to'liq</b> ismingizni kiriting:")
        return

    await state.update_data(full_name=name)
    await message.answer(
        "📱 <b>Telefon raqamingizni yuboring:</b>\n\n"
        "Quyidagi tugmani bosib avtomatik yuborishingiz yoki\n"
        "qo'lda kiritishingiz mumkin.\n"
        "<i>Format: +998901234567</i>",
        reply_markup=phone_kb()
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone, F.text == "❌ Bekor qilish")
async def reg_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=remove_kb())


@router.message(Registration.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await _finish_registration(message, state, phone)


@router.message(Registration.phone)
async def reg_phone_manual(message: Message, state: FSMContext):
    phone = message.text.strip().replace(" ", "").replace("-", "")
    if not re.match(r"^\+?[0-9]{9,13}$", phone):
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, raqamni to'g'ri kiriting:\n"
            "<i>+998901234567</i>"
        )
        return
    if not phone.startswith("+"):
        phone = "+" + phone
    await _finish_registration(message, state, phone)


async def _finish_registration(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    await db.create_user(message.from_user.id, data['full_name'], phone)
    await state.clear()
    await message.answer(
        "✅ <b>Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!</b>\n\n"
        f"👤 Ism: <b>{data['full_name']}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n\n"
        "Endi imtihonga ro'yxatdan o'tishingiz mumkin. 👇",
        reply_markup=main_menu_kb()
    )


# ─── Main menu buttons ────────────────────────────────────────────────────────────

@router.message(F.text == "📝 Imtihonga ro'yxatdan o'tish")
async def start_booking(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return

    exam_types = await db.get_exam_types(active_only=True)
    if not exam_types:
        await message.answer("😔 Hozircha faol imtihon turlari mavjud emas.")
        return

    await message.answer(
        "📚 <b>Imtihon turini tanlang:</b>",
        reply_markup=exam_types_kb(exam_types)
    )
    await state.set_state(ExamBooking.selecting_type)


@router.message(F.text == "📋 Mening ro'yxatlarim")
async def my_registrations(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return

    regs = await db.get_user_registrations(user['id'])
    if not regs:
        await message.answer(
            "📋 Siz hali hech qanday imtihonga ro'yxatdan o'tmagansiz.\n\n"
            "Ro'yxatdan o'tish uchun <b>📝 Imtihonga ro'yxatdan o'tish</b> tugmasini bosing."
        )
        return

    text = "📋 <b>Sizning faol ro'yxatlaringiz:</b>\n\n"
    for i, reg in enumerate(regs, 1):
        text += (
            f"{i}. 📚 <b>{reg['type_name']}</b>\n"
            f"   📅 Sana: {reg['exam_date']}\n"
            f"   📍 Joy: {reg['location']}\n\n"
        )
    text += "<i>Bekor qilish uchun tugmani bosing 👇</i>"

    await message.answer(text, reply_markup=registrations_kb(regs))


@router.message(F.text == "ℹ️ Ma'lumot")
async def info_handler(message: Message):
    await message.answer(
        "ℹ️ <b>Bot haqida ma'lumot</b>\n\n"
        "Bu bot orqali turli imtihonlarga (SAT, Milliy sertifikat va boshqalar) "
        "ro'yxatdan o'tishingiz mumkin.\n\n"
        "🔹 Ro'yxatdan o'tish — imtihon turi va sanasini tanlang\n"
        "🔹 Mening ro'yxatlarim — ro'yxatlaringizni ko'ring yoki bekor qiling\n\n"
        "📞 Muammo yuzaga kelsa, administratorga murojaat qiling."
    )


# ─── Exam Booking Flow ────────────────────────────────────────────────────────────

@router.callback_query(ExamBooking.selecting_type, F.data.startswith("exam_type:"))
async def cb_select_type(callback: CallbackQuery, state: FSMContext):
    type_id = int(callback.data.split(":")[1])
    exam_type = await db.get_exam_type(type_id)
    if not exam_type:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    exam_dates = await db.get_exam_dates(type_id, active_only=True)
    if not exam_dates:
        await callback.answer(
            "😔 Bu imtihon uchun hozircha mavjud sanalar yo'q.", show_alert=True
        )
        return

    await state.update_data(selected_type_id=type_id, selected_type_name=exam_type['name'])
    await callback.message.edit_text(
        f"📚 <b>{exam_type['name']}</b>\n\n"
        "📅 <b>Imtihon sanasini tanlang:</b>",
        reply_markup=exam_dates_kb(exam_dates)
    )
    await state.set_state(ExamBooking.selecting_date)
    await callback.answer()


@router.callback_query(ExamBooking.selecting_date, F.data.startswith("exam_date:"))
async def cb_select_date(callback: CallbackQuery, state: FSMContext):
    date_id = int(callback.data.split(":")[1])
    exam_date = await db.get_exam_date(date_id)
    if not exam_date:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    seats_left = exam_date['available_seats'] - exam_date['registered_count']
    if seats_left <= 0:
        await callback.answer("😔 Bu sanadagi barcha joylar band.", show_alert=True)
        return

    await state.update_data(selected_date_id=date_id)
    await callback.message.edit_text(
        "✅ <b>Ro'yxatdan o'tishni tasdiqlang:</b>\n\n"
        f"📚 Imtihon:    <b>{exam_date['type_name']}</b>\n"
        f"📅 Sana:       <b>{exam_date['exam_date']}</b>\n"
        f"📍 Joy:        <b>{exam_date['location']}</b>\n"
        f"👥 Bo'sh joylar: <b>{seats_left}</b>",
        reply_markup=confirm_kb(date_id)
    )
    await state.set_state(ExamBooking.confirming)
    await callback.answer()


@router.callback_query(ExamBooking.confirming, F.data.startswith("confirm:"))
async def cb_confirm_booking(callback: CallbackQuery, state: FSMContext):
    date_id = int(callback.data.split(":")[1])
    user = await db.get_user(callback.from_user.id)
    exam_date = await db.get_exam_date(date_id)

    if not exam_date:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)
        await state.clear()
        return

    # Check duplicate
    already = await db.check_already_registered(user['id'], date_id)
    if already:
        await callback.answer(
            "❌ Siz allaqachon bu imtihonga ro'yxatdan o'tgansiz!", show_alert=True
        )
        await state.clear()
        return

    success = await db.register_for_exam(user['id'], exam_date['exam_type_id'], date_id)

    if success:
        await callback.message.edit_text(
            "🎉 <b>Muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
            f"📚 Imtihon: <b>{exam_date['type_name']}</b>\n"
            f"📅 Sana:   <b>{exam_date['exam_date']}</b>\n"
            f"📍 Joy:    <b>{exam_date['location']}</b>\n\n"
            "Omad tilaymiz! 🍀"
        )
    else:
        await callback.message.edit_text(
            "❌ Ro'yxatdan o'tishda xatolik yuz berdi. Qayta urinib ko'ring."
        )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "back_to_types")
async def cb_back_to_types(callback: CallbackQuery, state: FSMContext):
    exam_types = await db.get_exam_types(active_only=True)
    await callback.message.edit_text(
        "📚 <b>Imtihon turini tanlang:</b>",
        reply_markup=exam_types_kb(exam_types)
    )
    await state.set_state(ExamBooking.selecting_type)
    await callback.answer()


@router.callback_query(F.data == "user_cancel")
async def cb_user_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("❌ Bekor qilindi.")


# ─── Cancel registration ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cancel_reg:"))
async def cb_cancel_registration(callback: CallbackQuery):
    reg_id = int(callback.data.split(":")[1])
    user = await db.get_user(callback.from_user.id)

    success = await db.cancel_registration(reg_id, user['id'])
    if not success:
        await callback.answer("❌ Bekor qilishda xatolik.", show_alert=True)
        return

    await callback.answer("✅ Ro'yxatdan o'chirildi!", show_alert=True)

    regs = await db.get_user_registrations(user['id'])
    if not regs:
        await callback.message.edit_text("📋 Sizda faol ro'yxatlar yo'q.")
    else:
        text = "📋 <b>Sizning faol ro'yxatlaringiz:</b>\n\n"
        for i, reg in enumerate(regs, 1):
            text += (
                f"{i}. 📚 <b>{reg['type_name']}</b>\n"
                f"   📅 Sana: {reg['exam_date']}\n"
                f"   📍 Joy: {reg['location']}\n\n"
            )
        text += "<i>Bekor qilish uchun tugmani bosing 👇</i>"
        await callback.message.edit_text(text, reply_markup=registrations_kb(regs))


# ─── /cancel command ──────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=main_menu_kb())
