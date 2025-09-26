# Импорт библиотек
import os
import json
import aiofiles
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Загружаем данные из .env (не забудь добавить в .gitignore)
load_dotenv('data.env')
API_TOKEN = os.getenv('TOKEN')
users = os.getenv('USERS')

# Создаём бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Пока вместо БД будет json, для проверки регистрации, реализуются функции чтения и сохранения
bd_file = os.getenv('USERS')

async def load_bd():
    try:
        async with aiofiles.open(bd_file, mode='r', encoding='utf-8') as f:
            data = await f.read()
            return json.loads(data) if data else {}
    except FileNotFoundError:
        return {}

# Сохранение в бд
async def save_bd(data):
    async with aiofiles.open(bd_file, mode='w', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))

# Создаём блоки кнопок
# Основной блок кнопок для зарегистрированных
main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text='Тарифы')],
        [types.KeyboardButton(text='Инструкция')]
    ],
    resize_keyboard=True
)

class state_user(StatesGroup):
    name = State()
    lastname = State()
    work = State()

# Приветствие на команду /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer("Всем привет! Я Винни-пух — ваш помощник по безопасному соединению.")

    # Проверка регистрации и дальнейшая регистрация
    tg_id = str(message.from_user.id)
    bd = await load_bd()
    if tg_id in bd.keys() and bd[tg_id] != {}:
        await message.answer(f'Привет, {bd[tg_id]['name']}! Что ты хочешь, выбери действие?',
                             reply_markup = main_keyboard)
        await state.set_state(state_user.work)

    elif tg_id not in bd.keys() or tg_id in bd.keys() and bd[tg_id] == {}:
        await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
        bd[tg_id] = {}
        await save_bd(bd)
    else: await  message.answer('Какие-то проблемы...')


# Продолжение регистрации, сохраняем имя и фамилию для TG ID
@dp.message(state_user.name)
async def reg_name(message: types.Message, state: FSMContext):
    tg_id = str(message.from_user.id)
    bd = await load_bd()
    bd[tg_id]["name"] = message.text
    await save_bd(bd) # сохраняем после изменения
    await state.set_state(state_user.lastname)
    await message.answer("Отлично, теперь введи фамилию")

@dp.message(state_user.lastname)
async def reg_lastname(message: types.Message, state: FSMContext):
    tg_id = str(message.from_user.id)
    bd = await load_bd()
    bd[tg_id]["lastname"] = message.text
    await save_bd(bd)  # сохраняем после изменения
    await state.set_state(state_user.work)
    await message.answer(
        f"Супер регистрация завершена!\nИмя: {bd[tg_id]['name']}\nФамилия: {bd[tg_id]['lastname']}",
        reply_markup=main_keyboard
    )

# Обработка всех остальных сообщений
@dp.message(state_user.work)
async def echo_message(message: types.Message):
    await message.answer(message.text)


# Точка входа
async def main():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())