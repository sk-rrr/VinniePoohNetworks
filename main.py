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
bd = dict()
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
# Блок кнопок для не зарегистрированных
reg_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Зарегистрироваться")]
    ],
    resize_keyboard=True
)

# Приветствие на команду /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Всем привет! Я Винни-пух — ваш помощник по безопасному соединению.")

    # Проверка регистрации и дальнейшая регистрация
    tg_id = str(message.from_user.id)
    bd = await load_bd()
    if tg_id in bd.keys():
        await message.answer(f'Привет, {bd[tg_id]['name']}! Что ты хочешь, выбери действие?',
                             reply_markup = main_keyboard)

    elif tg_id not in bd.keys():
        await message.answer('Ты ещё не зарегистрирован, чтобы пройти регистрацию, нажми кнопку "Зарегистрироваться".',
                             reply_markup = reg_keyboard)
    else: await  message.answer('Какие-то проблемы...')

# Начало регистрации
@dp.message(lambda msg: msg.text == 'Зарегистрироваться')
async def start_reg(message: types.Message):
    tg_id = str(message.from_user.id)
    # Защита от дурака
    if tg_id not in bd.keys():
        bd[tg_id] = {"step": "wait_name"}  # step только, имени нет
        await message.answer('Введи своё имя')
    else:
        del bd[tg_id]
        bd[tg_id] = {"step": "wait_name"}  # step только, имени нет
        await message.answer('Введи своё имя')
        await save_bd(bd)

# Продолжение регистрации, сохраняем имя и фамилию для TG ID
@dp.message()
async def continue_reg(message: types.Message):
    # bd = await load_bd()
    tg_id = str(message.from_user.id)

    # Пользователь не начал регистрацию
    if tg_id not in bd or "step" not in bd[tg_id]:
        await message.answer("Напиши /start чтобы зарегистрироваться", reply_markup=reg_keyboard)
        return

    step = bd[tg_id]["step"]

    if step == "wait_name":
        bd[tg_id]["name"] = message.text
        bd[tg_id]["step"] = "wait_lastname"
        await save_bd(bd) # сохраняем после изменения
        await message.answer("Отлично, теперь введи фамилию")
        return

    elif step == "wait_lastname":
        bd[tg_id]["lastname"] = message.text
        del bd[tg_id]["step"]  # регистрация завершена
        await save_bd(bd)  # сохраняем после изменения
        await message.answer(
            f"Супер регистрация завершена!\nИмя: {bd[tg_id]['name']}\nФамилия: {bd[tg_id]['lastname']}",
            reply_markup=main_keyboard
        )
        return  # регистрация закончена

    else:
        await message.answer("Что-то пошло не так, напиши /start", reply_markup=reg_keyboard)


# Обработка всех остальных сообщений
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(message.text)


# Точка входа
async def main():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())