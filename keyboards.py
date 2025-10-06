# Импорт библиотек
from aiogram import types
# Создаём блоки кнопок
# Основной блок кнопок для зарегистрированных
main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text='Тарифы')],
        [types.KeyboardButton(text='Инструкция')]
    ],
    resize_keyboard=True
)