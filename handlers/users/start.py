import asyncio
import os
import sqlite3
import pandas as pd
import datetime
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from data.config import ADMIN_ID, GROUP_ID
from aiogram.dispatcher import FSMContext
from loader import dp, bot
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.default.button import birinchi_button
from states.state import Xonachalar
from database_saver import save_request_sorov_table, update_status, save_request_to_history, get_user_data
from keyboards.inline.inline_buttons import filial_buttons



DB_PATH = "user_data.db"
EXPORT_DIR = "exports"




@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    await message.answer("Assalomu Aleykum <b>MARS IT SCHOOL</b> ning botiga xush kelibsiz",
                         reply_markup=birinchi_button)

@dp.message_handler(text="🤝 Ruxsat so`rash")
async def ruxsat_sorash(message: types.Message):
    await message.reply(""""Ism va familyangizni kiriting ⬇️

✅ <i>Bekbayev Sirojiddin</i>
❌ <i>Siroj</i>""", reply_markup=ReplyKeyboardRemove())
    await Xonachalar.ism_xonacha.set()

@dp.message_handler(content_types=types.ContentType.TEXT, state=Xonachalar.ism_xonacha)
async def vaqt(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(""""Javob so’rash sanasini to’liq kiriting ⬇️

✅ <i>1.02.2025-8.02.2025</i>
❌ <i>1 fev dan 8 fev gacha</i>""", parse_mode="HTML")
    await Xonachalar.vaqt_xonacha.set()

@dp.message_handler(content_types=types.ContentType.TEXT, state=Xonachalar.vaqt_xonacha)
async def guruxlar(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.reply("""Guruhingizni kiriting ⬇️

✅ BG-1375
❌ bg1375""")
    await Xonachalar.guruxlar_xonacha.set()


@dp.message_handler(content_types=types.ContentType.TEXT, state=Xonachalar.guruxlar_xonacha)
async def filial(message: types.Message, state: FSMContext):
    await state.update_data(guruxlar=message.text)
    await message.reply("<b>Filialdan birini tanlang</b>", reply_markup=filial_buttons, parse_mode="HTML")
    await Xonachalar.filial_xonacha.set()


@dp.callback_query_handler(state=Xonachalar.filial_xonacha)
async def sabab(callback_query: types.CallbackQuery, state: FSMContext):
    filial = callback_query.data  # callback data orqali filialni olish
    await state.update_data(filial=filial)

    # Javobni callback query orqali yuborish
    await callback_query.answer()  # Bu javobni yuboradi
    await bot.send_message(callback_query.from_user.id, "Javob so’rash sababini to’liq kiriting ⬇️")
    await Xonachalar.sabab_xonacha.set()


@dp.message_handler(content_types=types.ContentType.TEXT, state=Xonachalar.sabab_xonacha)
async def submit_request(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name")
    time = user_data.get("time")
    guruxlar = user_data.get("guruxlar")
    filial = user_data.get("filial")
    sabab = message.text
    user_id = message.from_user.id

    # Ma'lumotlarni bazaga saqlash
    save_request_sorov_table(user_id, name, time, guruxlar, filial, sabab)
    await message.answer("☑️ Sizning arizangiz qabul qilindi")

    # Ruxsat so'rovini adminlarga yuborish
    await send_request_to_admin(user_id, name, time, guruxlar, filial, sabab)

    await state.finish()

async def send_request_to_admin(user_id, name, time, guruxlar, filial, sabab):
    user_data = get_user_data(user_id)
    message_for_admin = f"""
🆔 Telegram ID: {user_id}
👤 Ism: {user_data['name']}
⏳ Vaqt: {user_data['time']}
👥 Guruhlar: {user_data['guruxlar']}
📍 Filial: {user_data['filial']}
❓ Sabab: {user_data['sabab']}
📅 Ariza Sanasi: {user_data['data']}
    """

    # Inline tugmalarni yaratish
    tasdiqlash_buttons = InlineKeyboardMarkup()
    tasdiqlash_buttons.add(InlineKeyboardButton("✔️ Tasdiqlash", callback_data=f"approve_{user_id}"))
    tasdiqlash_buttons.add(InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}"))

    # Xabarni adminlarga yuborish
    await dp.bot.send_message(ADMIN_ID, message_for_admin, reply_markup=tasdiqlash_buttons)

@dp.callback_query_handler(lambda c: c.data.startswith('approve_') or c.data.startswith('reject_'))
async def process_callback_approval(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[1])
    status_text = ""


    if callback_query.data.startswith('approve_'):
        status_text = "Ruxsat berildi"

        # Foydalanuvchi ma'lumotlarini bazadan olish
        user_data = get_user_data(user_id)  # Bazadan foydalanuvchi ma'lumotlarini olish
        if user_data:
            message_for_group = f"""
<b>{status_text}</b>
Ruxsat so'rov holati:
🆔 Telegram ID: {user_id}
👤 Ism: {user_data['name']}
⏳ Vaqt: {user_data['time']}
👥 Guruhlar: {user_data['guruxlar']}
📍 Filial: {user_data['filial']}
❓ Sabab: {user_data['sabab']}
📅 Ariza Sanasi: {user_data['data']}
"""
            await bot.send_message(GROUP_ID, message_for_group, parse_mode="HTML")
    else:
        status_text = "Ruxsat rad etildi"

    # Foydalanuvchiga javob yuborish
    await callback_query.answer(status_text)
    await dp.bot.send_message(user_id, status_text)

    # Holatni sorov_table da yangilash
    update_status(user_id, status_text)

    # Ariza ma'lumotlarini history_sorov ga ko'chirish va sorov_table dan o'chirish
    save_request_to_history(user_id)


# ------ Send xlsx file to admin

def is_first_day_of_month():
    return datetime.datetime.now().day == 1

# SQLite3 ma'lumotlarini Excelga o'tkazish
def export_db_to_excel():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # faqat history_sorov jadvalidan ma'lumot olish
    table_name = "history_sorov"
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

    file_name = f"{EXPORT_DIR}/history_sorov_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"

    # Excel faylga yozish
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=table_name, index=False)

    conn.close()
    return file_name

# Adminga faylni yuborish
async def send_file_to_admin():
    if is_first_day_of_month():
        file_path = export_db_to_excel()
        with open(file_path, "rb") as file:
            await bot.send_document(chat_id=ADMIN_ID, document=file, caption="Oylik SQLite backup")
        print("Backup yaratildi va adminga yuborildi.")
    else:
        print("Bugun birinchi kun emas.")

# Bot buyruqlari
@dp.message_handler(commands=["backup"])
async def manual_backup(message: types.Message):
    """Qo'lda /backup buyrug'ini yuborgan adminga xabar yuboradi."""
    if str(message.chat.id) == ADMIN_ID:
        file_path = export_db_to_excel()
        with open(file_path, "rb") as file:
            await bot.send_document(chat_id=ADMIN_ID, document=file, caption="Manually requested SQLite backup")
        await message.reply("✅ Backup yaratildi va yuborildi!")
    else:
        await message.reply("❌ Sizda ruxsat yo'q!")

# Har oy avtomatik yuborish uchun task
async def scheduler():
    while True:
        now = datetime.datetime.now()
        if now.hour == 0 and now.minute == 0:  # 00:00 da ishga tushadi
            await send_file_to_admin()
        await asyncio.sleep(60)  # Har daqiqa tekshiradi

# Botni ishga tushirish
async def on_startup(dp):
    asyncio.create_task(scheduler())

