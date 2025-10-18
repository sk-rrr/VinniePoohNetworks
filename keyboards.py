# Импорт библиотек
from aiogram import types
# Создаём блоки кнопок
# Основной блок кнопок для зарегистрированных
main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text='Получить ссылку')],
        [types.KeyboardButton(text='Инструкция')]
    ],
    resize_keyboard=True
)
# Основной блок кнопок для администраторов
admin_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text='Получить ссылку')],
        [types.KeyboardButton(text='Инструкция')],
        [types.KeyboardButton(text='Команды администратора')]
    ],
    resize_keyboard=True
)