import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from states.states import AdminStates
from keyboards.admin_kb import (
    admin_menu_kb, exam_types_manage_kb, exam_type_actions_kb,
    exam_dates_manage_kb, exam_date_actions_kb, select_type_for_date_kb,
    registrations_filter_kb, confirm_broadcast_kb,
)
from keyboards.user_kb import main_menu_kb

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── /admin ──────────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqlari yo'q.")
        return

    await state.clear()
    stats = await db.get_stats()
    await message.answer(
        "🔧 <b>Admin panel</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"📝 Faol ro'yxatlar:  <b>{stats['registrations']}</b>\n"
        f"📚 Imtihon turlari:  <b>{stats['exam_types']}</b>\n"
        f"📅 Imtihon sanalari: <b>{stats['exam_dates']}</b>",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.delete()
    await callback.answer()


# ─── Exam Types ───────────────────────────────────────────────────────────────────

@router.message(F.text == "📚 Imtihon turlari")
async def manage_exam_types(message: Message):
    if not is_admin(message.from_user.id):
        return
    exam_types = await db.get_exam_types(active_only=False)
    await message.answer(
        "📚 <b>Imtihon turlari boshqaruvi:</b>",
        reply_markup=exam_types_manage_kb(exam_types)
    )


@router.callback_query(F.data == "admin_types_list")
async def cb_admin_types_list(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    exam_types = await db.get_exam_types(active_only=False)
    await callback.message.edit_text(
        "📚 <b>Imtihon turlari boshqaruvi:</b>",
        reply_markup=exam_types_manage_kb(exam_types)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_type")
async def cb_admin_add_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "📝 Yangi imtihon turining nomini kiriting:\n"
        "<i>Masalan: SAT, Milliy sertifikat, IELTS, TOEFL...</i>\n\n"
        "/cancel — bekor qilish"
    )
    await state.set_state(AdminStates.adding_type_name)
    await callback.answer()


@router.message(AdminStates.adding_type_name)
async def admin_add_type_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Nom juda qisqa. Iltimos, qayta kiriting:")
        return

    success = await db.add_exam_type(name)
    await state.clear()
    if success:
        await message.answer(
            f"✅ <b>{name}</b> imtihon turi muvaffaqiyatli qo'shildi!",
            reply_markup=admin_menu_kb()
        )
    else:
        await message.answer(
            "❌ Bu nom allaqachon mavjud yoki xatolik yuz berdi.",
            reply_markup=admin_menu_kb()
        )


@router.callback_query(F.data.startswith("admin_type:"))
async def cb_admin_type_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    type_id = int(callback.data.split(":")[1])
    exam_type = await db.get_exam_type(type_id)
    if not exam_type:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    status = "✅ Faol" if exam_type['is_active'] else "❌ Nofaol"
    await callback.message.edit_text(
        f"📚 <b>{exam_type['name']}</b>\n"
        f"Holat: {status}",
        reply_markup=exam_type_actions_kb(type_id, exam_type['is_active'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_type:"))
async def cb_admin_toggle_type(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    type_id = int(callback.data.split(":")[1])
    await db.toggle_exam_type(type_id)
    exam_type = await db.get_exam_type(type_id)
    status = "✅ Faol" if exam_type['is_active'] else "❌ Nofaol"
    await callback.answer(f"Holat o'zgartirildi: {status}", show_alert=True)
    await callback.message.edit_text(
        f"📚 <b>{exam_type['name']}</b>\n"
        f"Holat: {status}",
        reply_markup=exam_type_actions_kb(type_id, exam_type['is_active'])
    )


@router.callback_query(F.data.startswith("admin_delete_type:"))
async def cb_admin_delete_type(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    type_id = int(callback.data.split(":")[1])
    await db.delete_exam_type(type_id)
    await callback.answer("🗑 O'chirildi!", show_alert=True)
    exam_types = await db.get_exam_types(active_only=False)
    await callback.message.edit_text(
        "📚 <b>Imtihon turlari boshqaruvi:</b>",
        reply_markup=exam_types_manage_kb(exam_types)
    )


# ─── Exam Dates ───────────────────────────────────────────────────────────────────

@router.message(F.text == "📅 Imtihon sanalari")
async def manage_exam_dates(message: Message):
    if not is_admin(message.from_user.id):
        return
    exam_dates = await db.get_all_exam_dates()
    await message.answer(
        "📅 <b>Imtihon sanalari boshqaruvi:</b>",
        reply_markup=exam_dates_manage_kb(exam_dates)
    )


@router.callback_query(F.data == "admin_dates_list")
async def cb_admin_dates_list(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    exam_dates = await db.get_all_exam_dates()
    await callback.message.edit_text(
        "📅 <b>Imtihon sanalari boshqaruvi:</b>",
        reply_markup=exam_dates_manage_kb(exam_dates)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_date")
async def cb_admin_add_date(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    exam_types = await db.get_exam_types(active_only=True)
    if not exam_types:
        await callback.answer("❌ Avval kamida bitta imtihon turi qo'shing!", show_alert=True)
        return
    await callback.message.edit_text(
        "📚 <b>Qaysi imtihon uchun sana qo'shmoqchisiz?</b>",
        reply_markup=select_type_for_date_kb(exam_types)
    )
    await state.set_state(AdminStates.adding_date_type)
    await callback.answer()


@router.callback_query(AdminStates.adding_date_type, F.data.startswith("admin_date_type:"))
async def cb_admin_date_type_selected(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    type_id = int(callback.data.split(":")[1])
    await state.update_data(date_type_id=type_id)
    await callback.message.edit_text(
        "📅 <b>Imtihon sanasini kiriting:</b>\n\n"
        "<i>Format: 25.12.2024 yoki 2024-12-25</i>\n\n"
        "/cancel — bekor qilish"
    )
    await state.set_state(AdminStates.adding_date_value)
    await callback.answer()


@router.message(AdminStates.adding_date_value)
async def admin_add_date_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    import re
    date_text = message.text.strip()
    if not re.match(r'^\d{4}-\d{2}-\d{2}$|^\d{2}\.\d{2}\.\d{4}$', date_text):
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, sanani to'g'ri kiriting:\n"
            "<i>25.12.2024  yoki  2024-12-25</i>"
        )
        return
    await state.update_data(date_value=date_text)
    await message.answer(
        "📍 <b>Imtihon o'tkaziladigan joyni kiriting:</b>\n"
        "<i>Masalan: Toshkent sh., Chilonzor tumani, 1-maktab</i>"
    )
    await state.set_state(AdminStates.adding_date_location)


@router.message(AdminStates.adding_date_location)
async def admin_add_date_location(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(date_location=message.text.strip())
    await message.answer(
        "👥 <b>Maksimal o'rinlar sonini kiriting:</b>\n"
        "<i>Masalan: 100</i>"
    )
    await state.set_state(AdminStates.adding_date_seats)


@router.message(AdminStates.adding_date_seats)
async def admin_add_date_seats(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        seats = int(message.text.strip())
        if seats <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, musbat butun son kiriting!")
        return

    data = await state.get_data()
    await db.add_exam_date(data['date_type_id'], data['date_value'], data['date_location'], seats)
    await state.clear()

    exam_type = await db.get_exam_type(data['date_type_id'])
    await message.answer(
        "✅ <b>Imtihon sanasi muvaffaqiyatli qo'shildi!</b>\n\n"
        f"📚 Imtihon:   <b>{exam_type['name']}</b>\n"
        f"📅 Sana:      <b>{data['date_value']}</b>\n"
        f"📍 Joy:       <b>{data['date_location']}</b>\n"
        f"👥 O'rinlar:  <b>{seats}</b>",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data.startswith("admin_date:"))
async def cb_admin_date_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    date_id = int(callback.data.split(":")[1])
    ed = await db.get_exam_date(date_id)
    if not ed:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    seats_left = ed['available_seats'] - ed['registered_count']
    await callback.message.edit_text(
        f"📅 <b>Imtihon sanasi:</b>\n\n"
        f"📚 Tur:           <b>{ed['type_name']}</b>\n"
        f"📅 Sana:          <b>{ed['exam_date']}</b>\n"
        f"📍 Joy:           <b>{ed['location']}</b>\n"
        f"👥 Jami o'rinlar: <b>{ed['available_seats']}</b>\n"
        f"✅ Ro'yxatdagilar: <b>{ed['registered_count']}</b>\n"
        f"🔓 Bo'sh joylar:  <b>{seats_left}</b>",
        reply_markup=exam_date_actions_kb(date_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_date:"))
async def cb_admin_delete_date(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    date_id = int(callback.data.split(":")[1])
    await db.delete_exam_date(date_id)
    await callback.answer("🗑 O'chirildi!", show_alert=True)
    exam_dates = await db.get_all_exam_dates()
    await callback.message.edit_text(
        "📅 <b>Imtihon sanalari boshqaruvi:</b>",
        reply_markup=exam_dates_manage_kb(exam_dates)
    )


# ─── Registrations ────────────────────────────────────────────────────────────────

@router.message(F.text == "👥 Ro'yxatlar")
async def view_registrations(message: Message):
    if not is_admin(message.from_user.id):
        return
    exam_types = await db.get_exam_types(active_only=False)
    await message.answer(
        "👥 <b>Ro'yxatlarni ko'rish:</b>",
        reply_markup=registrations_filter_kb(exam_types)
    )


@router.callback_query(F.data == "admin_regs_all")
async def cb_admin_regs_all(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    regs = await db.get_all_registrations()
    if not regs:
        await callback.answer("📋 Hozircha ro'yxatlar yo'q.", show_alert=True)
        return

    text = f"👥 <b>Barcha faol ro'yxatlar ({len(regs)} ta):</b>\n\n"
    for i, r in enumerate(regs[:30], 1):
        text += (
            f"{i}. <b>{r['full_name']}</b>\n"
            f"   📱 {r['phone']}\n"
            f"   📚 {r['type_name']}  |  📅 {r['exam_date']}\n\n"
        )
    if len(regs) > 30:
        text += f"<i>... va yana {len(regs) - 30} ta ro'yxat</i>"

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_regs_type:"))
async def cb_admin_regs_by_type(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    type_id = int(callback.data.split(":")[1])
    regs = await db.get_registrations_by_type(type_id)
    exam_type = await db.get_exam_type(type_id)

    if not regs:
        await callback.answer(f"📋 Bu imtihon uchun ro'yxat yo'q.", show_alert=True)
        return

    text = f"👥 <b>{exam_type['name']} ro'yxatlari ({len(regs)} ta):</b>\n\n"
    for i, r in enumerate(regs, 1):
        text += (
            f"{i}. <b>{r['full_name']}</b>\n"
            f"   📱 {r['phone']}\n"
            f"   📅 {r['exam_date']}  |  📍 {r['location']}\n\n"
        )

    await callback.message.edit_text(text)
    await callback.answer()


# ─── Statistics ───────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await db.get_stats()
    await message.answer(
        "📊 <b>Statistika:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"📝 Faol ro'yxatlar:       <b>{stats['registrations']}</b>\n"
        f"📚 Faol imtihon turlari:  <b>{stats['exam_types']}</b>\n"
        f"📅 Faol imtihon sanalari: <b>{stats['exam_dates']}</b>"
    )


# ─── Broadcast ────────────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:\n\n"
        "<i>/cancel — bekor qilish</i>"
    )
    await state.set_state(AdminStates.broadcast_text)


@router.message(AdminStates.broadcast_text)
async def broadcast_text_received(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(broadcast_text=message.text)

    users_count = len(await db.get_all_users())
    await message.answer(
        f"📢 <b>Xabar ko'rinishi:</b>\n\n"
        f"{message.text}\n\n"
        f"<b>{users_count} ta foydalanuvchiga yuborilsin?</b>",
        reply_markup=confirm_broadcast_kb()
    )
    await state.set_state(AdminStates.broadcast_confirm)


@router.callback_query(AdminStates.broadcast_confirm, F.data == "admin_broadcast_confirm")
async def cb_broadcast_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    users = await db.get_all_users()

    await callback.message.edit_text("📤 Xabar yuborilmoqda...")

    sent, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(
                user['telegram_id'],
                f"📢 <b>E'lon:</b>\n\n{data['broadcast_text']}"
            )
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"✅ Muvaffaqiyatli: <b>{sent}</b>\n"
        f"❌ Xatolik:        <b>{failed}</b>"
    )


@router.callback_query(F.data == "admin_broadcast_cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.")
    await callback.answer()


# ─── Back to main menu ────────────────────────────────────────────────────────────

@router.message(F.text == "🔙 Asosiy menyu")
async def admin_back_to_main(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_kb())


# ─── /cancel in admin FSM states ─────────────────────────────────────────────────

@router.message(Command("cancel"))
async def admin_cmd_cancel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Amal bekor qilindi.", reply_markup=admin_menu_kb())
