# Импорт библиотек
import os
import json
import aiofiles
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup



# Загружаем данные из .env (не забудь добавить в .gitignore)
load_dotenv('data.env')
API_TOKEN = os.getenv('TOKEN')

# Создаём бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Пока вместо БД будет json, для проверки регистрации, реализуются функции чтения и сохранения
bd_file = os.getenv('USERS')
with open(bd_file) as f:
    database = json.loads(f.read())

# Сохранение в бд
async def save_bd():
    async with aiofiles.open(bd_file, mode='w', encoding='utf-8') as file:
        await file.write(json.dumps(database, ensure_ascii=False, indent=2))

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

# Приветствие на команду /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer("Всем привет! Я Винни-пух — ваш помощник по безопасному соединению.")

    # Проверка регистрации и дальнейшая регистрация
    tg_id = str(message.from_user.id)
    if tg_id in database.keys() and database[tg_id] != {}:
        await message.answer(f'Привет, {database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                             reply_markup = main_keyboard)
        await state.set_state(state_user.work)

    elif tg_id not in database.keys():
        await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
    else: await  message.answer('Какие-то проблемы...')


# Продолжение регистрации, сохраняем имя и фамилию для TG ID
@dp.message(state_user.name)
async def reg_name(message: types.Message, state: FSMContext):
    tg_id = str(message.from_user.id)
    database[tg_id]["name"] = message.text
    await state.set_state(state_user.lastname)
    await message.answer("Отлично, теперь введи фамилию")

@dp.message(state_user.lastname)
async def reg_lastname(message: types.Message, state: FSMContext):
    tg_id = str(message.from_user.id)
    database[tg_id]["lastname"] = message.text
    await state.set_state(state_user.work)
    await message.answer(
        f"Супер регистрация завершена!\nИмя: {database[tg_id]['name']}\nФамилия: {database[tg_id]['lastname']}",
        reply_markup=main_keyboard
    )
    await save_bd()

# Обработка кнопки инструкция
@dp.message(state_user.work, F.text == "Инструкция")
async def instructions(message: types.Message):
    await message.answer('GPT в помощь =)')

# Обработка всех остальных сообщений
@dp.message(state_user.work)
async def echo_message(message: types.Message):
    await message.answer(message.text)

@dp.message()
async def echo_message(message: types.Message, state: FSMContext):
    if message.text == '/start':
        await send_welcome()
    else:
        tg_id = str(message.from_user.id)
        if tg_id in database.keys() and database[tg_id] != {}:
            await message.answer(f'Привет, {database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                                 reply_markup=main_keyboard)
            await state.set_state(state_user.work)

# Точка входа с восстановлением состояния
async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())