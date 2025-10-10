# Импорт библиотек
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
import sys
import keyboards
from logger import logger
import work_with_bd
import work_with_3xui

# Обработка состояния пользователя
class state_user(StatesGroup):
    name = State()
    lastname = State()
    work = State()

# Функция сохраняет БД в json при возникновении критической ошибки перед завершением программы
def save_on_error(exc_type, exc_value, tb):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(work_with_bd.database, f, ensure_ascii=False, indent=2)
        logger.info('Успешное резервное копирование БД в json')
sys.excepthook = save_on_error

# Приветствие на команду /start
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer("Всем привет! Я Винни-Пух — ваш помощник по безопасному соединению.")

    # Проверка регистрации и дальнейшая регистрация
    tg_id = message.from_user.id
    if tg_id in work_with_bd.database.keys() and len(work_with_bd.database[tg_id].values())  in [2, 3]:
        await message.answer(f'Привет, {work_with_bd.database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                             reply_markup = keyboards.main_keyboard)
        logger.info(f'Пользователь {tg_id} отправил /start')
        await state.set_state(state_user.work)

    elif tg_id not in work_with_bd.database.keys():
        await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
    elif tg_id in work_with_bd.database.keys() and len(work_with_bd.database[tg_id].values()) not  in [2, 3]:
        await message.answer('Ты ещё не завершил регистрацию, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
    else: await  message.answer('Какие-то проблемы...')

# Продолжение регистрации, сохраняем имя и фамилию для TG ID
async def reg_name(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    work_with_bd.database[tg_id] = {}
    work_with_bd.temp_data[tg_id] = {}
    work_with_bd.database[tg_id]["name"] = message.text
    work_with_bd.temp_data[tg_id]["name"] = message.text
    await state.set_state(state_user.lastname)
    await message.answer("Отлично, теперь введи фамилию")

async def reg_lastname(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    work_with_bd.database[tg_id]["lastname"] = message.text
    work_with_bd.temp_data[tg_id]["lastname"] = message.text
    work_with_bd.temp_data[tg_id]["uuid"] = ''
    await work_with_bd.AddUser(work_with_bd.temp_data)
    del work_with_bd.temp_data[tg_id]
    await state.set_state(state_user.work)
    await message.answer(
        f"Супер регистрация завершена!\nИмя: {work_with_bd.database[tg_id]['name']}\nФамилия: {work_with_bd.database[tg_id]['lastname']}",
        reply_markup=keyboards.main_keyboard
    )
    logger.info(f'Пользователь {tg_id} завершил регистрацию')

# Обработка кнопки инструкция
async def instructions(message: types.Message):
    await message.answer('GPT в помощь =)')
    tg_id = message.from_user.id
    logger.info(f'Пользователь {tg_id} отправил "Инструкция"')

# Обработка всех остальных сообщений
async def echo_message(message: types.Message):
    await message.answer(message.text)

# Обработка пользователя при перезапуске бота
async def start_state(message: types.Message, state: FSMContext):
    if message.text == '/start':
        await send_welcome()
    else:
        tg_id = message.from_user.id
        if tg_id in work_with_bd.database.keys() and len(work_with_bd.database[tg_id].values()) in [2, 3]:
            await message.answer(f'Привет, {work_with_bd.database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                                 reply_markup=keyboards.main_keyboard)
            logger.info(f'Пользователь {tg_id} отправил /start')
            await state.set_state(state_user.work)

        elif tg_id not in work_with_bd.database.keys():
            await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
            await state.set_state(state_user.name)
        elif tg_id in work_with_bd.database.keys() and len(work_with_bd.database[tg_id].values()) not in [2, 3]:
            await message.answer('Ты ещё не завершил регистрацию, введи своё имя для регистрации.')
            await state.set_state(state_user.name)
        else:
            await  message.answer('Какие-то проблемы...')

# Создание профиля 3x-ui
async def create_profile(message: types.Message):
    tg_id = message.from_user.id
    logger.info(f'Пользователь {tg_id} отправил "Получить ссылку"')
    username = work_with_bd.database[tg_id]['name']
    async with work_with_3xui.XUI() as xui:
        try:
            # Создаём профиль 3x-ui
            link, user_uuid = await xui.add_user(str(tg_id), username)
            # Отправляем обновление в БД uuid
            work_with_bd.database[tg_id]['uuid'] = user_uuid
            await work_with_bd.AddUser({tg_id: work_with_bd.database[tg_id]})
            await message.answer(f'Профиль создан!\nСсылка: {link}')
        except Exception as error:
            await message.answer(f'Ошибка при создании профиля: {error}')

def register_handlers(dp: Dispatcher):
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(reg_name, state_user.name)
    dp.message.register(reg_lastname, state_user.lastname)
    dp.message.register(instructions, state_user.work, F.text == "Инструкция")
    dp.message.register(create_profile, state_user.work, F.text == "Получить ссылку")
    dp.message.register(echo_message, state_user.work)
    dp.message.register(start_state)