# Импорт библиотек
import os
import sys
import json
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import work_with_bd

# Загружаем данные из .env
load_dotenv('data.env')
API_TOKEN = os.getenv('TOKEN')

# Создаём бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Пока вместо БД будет json, для проверки регистрации, реализуются функции чтения и сохранения
database = work_with_bd.GetDB()
print(database)

# Создаём блоки кнопок
# Основной блок кнопок для зарегистрированных
main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text='Тарифы')],
        [types.KeyboardButton(text='Инструкция')]
    ],
    resize_keyboard=True
)

# Обработка состояния пользователя
class state_user(StatesGroup):
    name = State()
    lastname = State()
    work = State()

# Функция сохраняет БД при возникновении критической ошибки перед завершением программы
def save_on_error(exc_type, exc_value, tb):
    work_with_bd.UpdateBD(database)
sys.excepthook = save_on_error

# Приветствие на команду /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer("Всем привет! Я Винни-пух — ваш помощник по безопасному соединению.")

    # Проверка регистрации и дальнейшая регистрация
    tg_id = message.from_user.id
    if tg_id in database.keys() and len(database[tg_id]) == 2:
        await message.answer(f'Привет, {database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                             reply_markup = main_keyboard)
        await state.set_state(state_user.work)

    elif tg_id not in database.keys():
        await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
    elif tg_id in database.keys() and len(database[tg_id]) != 2:
        await message.answer('Ты ещё не завершил регистрацию, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
    else: await  message.answer('Какие-то проблемы...')

# Продолжение регистрации, сохраняем имя и фамилию для TG ID
@dp.message(state_user.name)
async def reg_name(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    database[tg_id] = {}
    database[tg_id]["name"] = message.text
    await state.set_state(state_user.lastname)
    await message.answer("Отлично, теперь введи фамилию")

@dp.message(state_user.lastname)
async def reg_lastname(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    database[tg_id]["lastname"] = message.text
    await state.set_state(state_user.work)
    await message.answer(
        f"Супер регистрация завершена!\nИмя: {database[tg_id]['name']}\nФамилия: {database[tg_id]['lastname']}",
        reply_markup=main_keyboard
    )

# Обработка кнопки инструкция
@dp.message(state_user.work, F.text == "Инструкция")
async def instructions(message: types.Message):
    await message.answer('GPT в помощь =)')

# Обработка всех остальных сообщений
@dp.message(state_user.work)
async def echo_message(message: types.Message):
    await message.answer(message.text)

# Обработка пользователя при перезапуске бота
@dp.message()
async def echo_message(message: types.Message, state: FSMContext):
    if message.text == '/start':
        await send_welcome()
    else:
        tg_id = str(message.from_user.id)
        if tg_id in database.keys() and len(database[tg_id]) == 2:
            await message.answer(f'Привет, {database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                                 reply_markup=main_keyboard)
            await state.set_state(state_user.work)
        elif tg_id not in database.keys():
            await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
            await state.set_state(state_user.name)
        elif tg_id in database.keys() and len(database[tg_id]) != 2:
            await message.answer('Ты ещё не завершил регистрацию, введи своё имя для регистрации.')
            await state.set_state(state_user.name)
        else:
            await  message.answer('Какие-то проблемы...')

# Точка входа с восстановлением состояния
async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())