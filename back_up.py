import logging
import sqlite3
import pandas as pd
import os
import datetime
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_polling

logging.basicConfig(level=logging.INFO)

# Telegram ma'lumotlari
TOKEN = "YOUR_TOKEN_HERE"
ADMIN_CHAT_ID = "YOUR_ADMIN_ID"  # Adminga yuborish uchun chat ID

# SQLite fayl manzili
DB_PATH = "user_data.db"
EXPORT_DIR = "exports"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Har oy 1-sanada ishga tushirish uchun tekshirish
def is_first_day_of_month():
    return datetime.datetime.now().day == 1

def export_db_to_excel():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    file_name = f"{EXPORT_DIR}/database_backup_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"

    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        for table in tables:
            table_name = table[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            df.to_excel(writer, sheet_name=table_name, index=False)

    conn.close()
    return file_name

# Adminga faylni yuborish
async def send_file_to_admin():
    if is_first_day_of_month():
        file_path = export_db_to_excel()
        with open(file_path, "rb") as file:
            await bot.send_document(chat_id=ADMIN_CHAT_ID, document=file, caption="Oylik SQLite backup")
        print("Backup yaratildi va adminga yuborildi.")
    else:
        print("Bugun birinchi kun emas.")

# Bot buyruqlari
@dp.message_handler(commands=["backup"])
async def manual_backup(message: types.Message):
    """Qo'lda /backup buyrug'ini yuborgan adminga xabar yuboradi."""
    if str(message.chat.id) == ADMIN_CHAT_ID:
        file_path = export_db_to_excel()
        with open(file_path, "rb") as file:
            await bot.send_document(chat_id=ADMIN_CHAT_ID, document=file, caption="Manually requested SQLite backup")
        await message.reply("✅ Backup yaratildi va yuborildi!")
    else:
        await message.reply("❌ Sizda ruxsat yo'q!")

# Har oy avtomatik yuborish uchun task
async def scheduler():
    while True:
        now = datetime.datetime.now()
        if now.hour == 0 and now.minute == 0:
            await send_file_to_admin()
        await asyncio.sleep(60)

async def on_startup(dp):
    asyncio.create_task(scheduler())

if __name__ == "__main__":
    start_polling(dp, on_startup=on_startup)
