import asyncio
import os
import sqlite3
import pandas as pd
import datetime
from aiogram import types
from data.config import ADMIN_ID, GROUP_ID
from aiogram.dispatcher import FSMContext
from loader import dp, bot
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.default.button import birinchi_button
from states.state import Xonachalar
from database_saver import save_request_sorov_table, update_status, save_request_to_history, get_user_data, get_all_pending_requests
from keyboards.inline.inline_buttons import filial_buttons


DB_PATH = "user_data.db"
EXPORT_DIR = "exports"


async def check_group():
    chat = await bot.get_chat(GROUP_ID)
    print(chat)

# check_group()

@dp.message_handler(commands='start', state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    # Reset any ongoing form entry state
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
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
    await message.answer(""""Javob so'rash sanasini to'liq kiriting ⬇️

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

    await callback_query.answer()  # Bu javobni yuboradi
    await bot.send_message(callback_query.from_user.id, "Javob so'rash sababini to'liq kiriting ⬇️")
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
    request_id = save_request_sorov_table(user_id, name, time, guruxlar, filial, sabab)
    await message.answer("☑️ Sizning arizangiz qabul qilindi")

    # Ruxsat so'rovini adminlarga yuborish
    await send_request_to_admin(user_id, name, time, guruxlar, filial, sabab, request_id)

    await state.finish()

async def send_request_to_admin(user_id, name, time, guruxlar, filial, sabab, request_id):
    data = datetime.datetime.now().strftime("%Y-%m-%d")
    message_for_admin = f"""
🆔 Telegram ID: {user_id}
👤 Ism: {name}
⏳ Vaqt: {time}
👥 Guruhlar: {guruxlar}
📍 Filial: {filial}
❓ Sabab: {sabab}
📅 Ariza Sanasi: {data}
📌 So'rov ID: {request_id}
    """

    # Inline tugmalarni yaratish
    tasdiqlash_buttons = InlineKeyboardMarkup()
    tasdiqlash_buttons.add(InlineKeyboardButton("✔️ Tasdiqlash", callback_data=f"approve_{request_id}"))
    tasdiqlash_buttons.add(InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{request_id}"))

    # Xabarni adminlarga yuborish
    await dp.bot.send_message(ADMIN_ID, message_for_admin, reply_markup=tasdiqlash_buttons)

@dp.callback_query_handler(lambda c: c.data.startswith('approve_') or c.data.startswith('reject_'))
async def process_callback_approval(callback_query: types.CallbackQuery):
    request_id = int(callback_query.data.split('_')[1])
    status_text = ""

    if callback_query.data.startswith('approve_'):
        status_text = "Ruxsat berildi"
    else:
        status_text = "Ruxsat rad etildi"

    # Foydalanuvchi ma'lumotlarini bazadan olish
    user_data = get_user_data(request_id)  
    if user_data:
        message_for_group = f"""
<b>{status_text}</b>
Ruxsat so'rov holati:
🆔 Telegram ID: {user_data['id']}
👤 Ism: {user_data['name']}
⏳ Vaqt: {user_data['time']}
👥 Guruhlar: {user_data['guruxlar']}
📍 Filial: {user_data['filial']}
❓ Sabab: {user_data['sabab']}
📅 Ariza Sanasi: {user_data['data']}
Status: {status_text}
"""
        await bot.send_message(GROUP_ID, message_for_group, parse_mode="HTML")
        
        # Holatni sorov_table da yangilash
        update_status(request_id, status_text)
        
        # Extract user_id from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sorov_table WHERE id = ?", (request_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id = result[0]
            await dp.bot.send_message(user_id, status_text)
        
        # Save to history
        save_request_to_history(request_id)
        
        # Edit the original message to remove the buttons
        try:
            # Get the original message text
            original_message_text = callback_query.message.text
            # Edit the message to remove buttons, and add status
            await callback_query.message.edit_text(f"{original_message_text}\n\n<b>Status:</b> {status_text}", parse_mode="HTML")
        except Exception as e:
            print(f"Error editing message: {e}")
        
        # Inform the admin about the action
        await callback_query.answer(f"So'rov {status_text}")

# Add command to show all pending requests
@dp.message_handler(commands=["sorovs"])
async def show_pending_requests(message: types.Message):
    """Show all pending requests to admin"""
    if message.chat.id == int(ADMIN_ID):
        pending_requests = get_all_pending_requests()
        if not pending_requests:
            await message.reply("Javob kutilayotgan so'rovlar mavjud emas.")
            return
            
        for request in pending_requests:
            request_message = f"""
🆔 Telegram ID: {request['user_id']}
👤 Ism: {request['name']}
⏳ Vaqt: {request['time']}
👥 Guruhlar: {request['guruxlar']}
📍 Filial: {request['filial']}
❓ Sabab: {request['sabab']}
📅 Ariza Sanasi: {request['data']}
📌 So'rov ID: {request['id']}
            """
            # Create inline buttons for each request
            tasdiqlash_buttons = InlineKeyboardMarkup()
            tasdiqlash_buttons.add(InlineKeyboardButton("✔️ Tasdiqlash", callback_data=f"approve_{request['id']}"))
            tasdiqlash_buttons.add(InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{request['id']}"))
            
            await message.answer(request_message, reply_markup=tasdiqlash_buttons)
    else:
        await message.reply("❌ Sizda ruxsat yo'q!")

def is_first_day_of_month():
    return datetime.datetime.now().day == 1

def export_db_to_excel():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
    await check_group()