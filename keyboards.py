from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Mashqlar Rejasi"),
        KeyboardButton(text="Natijalarim")
    )
    builder.row(
        KeyboardButton(text="Kkal Hisoblagich"),
        KeyboardButton(text="BMI Hisoblash")
    )
    builder.row(
        KeyboardButton(text="Suv Balansi"),
        KeyboardButton(text="AI Yordamchi")
    )
    builder.row(
        KeyboardButton(text="Eslatmalar"),
        KeyboardButton(text="Yordam")
    )
    return builder.as_markup(resize_keyboard=True)
