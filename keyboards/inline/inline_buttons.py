from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

tasdiqlash_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✔️ Tasdiqlash", callback_data="tasdiqlash"),
            InlineKeyboardButton(text="✖️ Rad etish", callback_data="rad_etish")
        ]
    ], resize_keyboard=True
)




filial_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Yunusobod ⭕️", callback_data="Yunusobod"),
            InlineKeyboardButton(text="Tinchlik ⭕️", callback_data="Tinchlik"),
            InlineKeyboardButton(text="Chilonzor ️⭕️", callback_data="Chilonzor")
        ],
        [
            InlineKeyboardButton(text="Sergeli ⭕️", callback_data="Sergeli"),
            InlineKeyboardButton(text="Maksim Gorki ⭕️", callback_data="Maksim_Gorki"),
            InlineKeyboardButton(text="Oybek ⭕️", callback_data="Oybek")
        ],
        [
            InlineKeyboardButton(text="Minor ⭕️", callback_data="Minor")
        ]
    ], resize_keyboard=True
)

