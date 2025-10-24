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
from config import bot

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
    if tg_id in work_with_bd.database.keys() and sum(1 for v in work_with_bd.database[tg_id].values() if v or v == False) in [3, 4]:
        if work_with_bd.database[int(tg_id)]['admin']:
            await message.answer(
                f'Привет, администратор {work_with_bd.database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                reply_markup=keyboards.admin_keyboard)
            logger.info(f'Администратор {tg_id} отправил /start')
            await state.set_state(state_user.work)
        else:
            await message.answer(f'Привет, {work_with_bd.database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                                 reply_markup=keyboards.main_keyboard)
            logger.info(f'Пользователь {tg_id} отправил /start')
            await state.set_state(state_user.work)
    elif tg_id not in work_with_bd.database.keys():
        await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
        await state.set_state(state_user.name)
    elif tg_id in work_with_bd.database.keys() and sum(1 for v in work_with_bd.database[tg_id].values() if v or v == False) not in [3, 4]:
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
    work_with_bd.temp_data[tg_id]["admin"] = 'False'
    await work_with_bd.AddUser(work_with_bd.temp_data)
    del work_with_bd.temp_data[tg_id]
    await state.set_state(state_user.work)
    await message.answer(
        f"Супер регистрация завершена!\nИмя: {work_with_bd.database[tg_id]['name']}\nФамилия: {work_with_bd.database[tg_id]['lastname']}\nОтправьте ваш Telegram <code>{tg_id}</code> для верификации.",
        reply_markup=keyboards.main_keyboard, parse_mode='HTML'
    )
    logger.info(f'Пользователь {tg_id} завершил регистрацию')

# Обработка кнопки инструкция
async def instructions(message: types.Message):
    await message.answer('GPT в помощь =)')
    tg_id = message.from_user.id
    logger.info(f'Пользователь {tg_id} отправил "Инструкция"')

# Обработка кнопки инструкция администратора
async def admin_instructions(message: types.Message):
    await message.answer(
    "<b>📘 Инструкция администратора</b>\n\n"
    "<b>✅ Верификация пользователя:</b>\n"
    "1. Пользователь отправляет вам свой <b>Telegram ID (tgid)</b> в личные сообщения.\n"
    "2. Если всё корректно, введите команду:\n"
    "<code>/v tgid</code>\n"
    "После этого пользователь будет верифицирован и получит сообщение со свою ссылкой.\n\n"
    "<b>🗑️ Удаление пользователя:</b>\n"
    "Чтобы удалить пользователя из системы, используйте команду:\n"
    "<code>/dv tgid</code>\n"
    "После удаления пользователь утратит доступ к своим данным и получит оповещение об этом.\n\n"
    "<b>ℹ️ Примечание:</b>\n"
    "Все команды выполняются только пользователями, имеющими права администратора.",
    parse_mode='HTML')
    tg_id = message.from_user.id
    logger.info(f'Пользователь {tg_id} отправил "Инструкция администратора"')

# Обработка пользователя при перезапуске бота
async def start_state(message: types.Message, state: FSMContext):
    if message.text == '/start':
        await send_welcome()
    else:
        tg_id = message.from_user.id
        if tg_id in work_with_bd.database.keys() and sum(1 for v in work_with_bd.database[tg_id].values() if v or v == False) in [3, 4]:
            if work_with_bd.database[int(tg_id)]['admin']:
                await message.answer(f'Привет, администратор {work_with_bd.database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                                     reply_markup=keyboards.admin_keyboard)
                logger.info(f'Администратор {tg_id} отправил /start')
                await state.set_state(state_user.work)
            else:
                await message.answer(f'Привет, {work_with_bd.database[tg_id]['name']}! Что ты хочешь, выбери действие?',
                                     reply_markup=keyboards.main_keyboard)
                logger.info(f'Пользователь {tg_id} отправил /start')
                await state.set_state(state_user.work)
        elif tg_id not in work_with_bd.database.keys():
            await message.answer('Ты ещё не зарегистрирован, введи своё имя для регистрации.')
            await state.set_state(state_user.name)
        elif tg_id in work_with_bd.database.keys() and sum(1 for v in work_with_bd.database[tg_id].values() if v or v == False) not in [3, 4]:
            await message.answer('Ты ещё не завершил регистрацию, введи своё имя для регистрации.')
            await state.set_state(state_user.name)
        else:
            await  message.answer('Какие-то проблемы...')

# Создание профиля 3x-ui
async def create_profile(message: types.Message):
    tg_id = message.from_user.id
    user_uuid = work_with_bd.database[tg_id]['uuid']
    logger.info(f'Пользователь {tg_id} отправил "Получить ссылку"')
    username = work_with_bd.database[tg_id]['name']
    async with work_with_3xui.XUI() as xui:
        if work_with_bd.database[tg_id]['admin']:
            if user_uuid != '':
                try:
                    # Обновление ссылки пользователя из 3x-ui
                    link = await xui.get_link(user_uuid, tg_id, username)
                    # Отправляем обновление в БД uuid
                    await work_with_bd.AddUser({tg_id: work_with_bd.database[tg_id]})
                    await message.answer(f'Профиль обновлён!\nСсылка: <code>{link}</code>', parse_mode='HTML')
                    logger.info(f'Пользователь {tg_id} обновил ссылку')
                except Exception as error:
                    await message.answer(f'Ошибка при обновлении профиля.')
                    logger.exception(f'Ошибка при обновлении профиля: {error}')
            else:
                try:
                    # Обновление ссылки пользователя из 3x-ui
                    link, user_uuid = await xui.add_user(tg_id, username)
                    # Отправляем обновление в БД uuid
                    work_with_bd.database[tg_id]['uuid'] = user_uuid
                    await work_with_bd.AddUser({tg_id: work_with_bd.database[tg_id]})
                    await message.answer(f'Профиль обновлён!\nСсылка:\n<code>{link}</code>', parse_mode='HTML')
                    logger.info(f'Пользователь {tg_id} обновил ссылку')
                except Exception as error:
                    await message.answer(f'Ошибка при обновлении профиля.')
                    logger.exception(f'Ошибка при обновлении профиля: {error}')
        else:
            try:
                if user_uuid != '':
                    # Обновление ссылки пользователя из 3x-ui
                    link = await xui.get_link(user_uuid, tg_id, username)
                    # Отправляем обновление в БД uuid
                    await work_with_bd.AddUser({tg_id: work_with_bd.database[tg_id]})
                    await message.answer(f'Профиль обновлён!\nСсылка:\n<code>{link}</code>', parse_mode='HTML')
                    logger.info(f'Пользователь {tg_id} обновил ссылку')
                else:
                    await message.answer(f'Пройдите верификацию у админа, вот ваш Telegram ID <code>{tg_id}</code>.', parse_mode='HTML')
                    logger.info(f'Пользователю {tg_id} требуется верификация')
            except Exception as error:
                await message.answer(f'Ошибка при обновлении профиля.')
                logger.exception(f'Ошибка при обновлении профиля: {error}')

# Верификация пользователей админом через /v tg_id
async def verify_user(message: types.Message):
    tg_id = message.from_user.id
    is_admin = work_with_bd.database[tg_id]['admin']
    args = message.text.split()
    async with work_with_3xui.XUI() as xui:
        if is_admin:
            if len(args) == 2 and args[0] == '/v' and args[1].isdigit():
                client_id = args[1]
                client_name = work_with_bd.database[int(client_id)]['name']
                link, user_uuid = await xui.add_user(client_id, client_name)
                work_with_bd.database[int(client_id)]['uuid'] = user_uuid
                await work_with_bd.AddUser({int(client_id): work_with_bd.database[int(client_id)]})
                await message.answer(f'Пользователь {client_id} успешно верифицирован, ему отправлена ссылка')
                logger.info(f'Пользователь {client_id} успешно верифицирован, ему отправлена ссылка')
                await bot.send_message(client_id, f'Ты успешно верифицирован! Вот твой ссылка:\n<code>{link}</code>', parse_mode='HTML')
            else:
                await message.answer('Ошибка верификации пользователя, проверь формат ввода: /v client_tg_id')
                logger.info(f'Ошибка верификации пользователя {args[1]}')
        else:
            await message.answer('У тебя нет прав для верификации пользователей')
            logger.info(f'Сторонний пользователь({tg_id}) пытался верифицировать клиента({args[1]})')

# Удаление верификации юзера админом через /dv tg_id
async def del_verify_user(message: types.Message):
    tg_id = message.from_user.id
    is_admin = work_with_bd.database[tg_id]['admin']
    args = message.text.split()
    async with work_with_3xui.XUI() as xui:
        if is_admin:
            if len(args) == 2 and args[0] == '/dv' and args[1].isdigit():
                client_id = args[1]
                client_uuid = work_with_bd.database[int(client_id)]['uuid']
                result = await xui.del_user(client_uuid)
                if result == True:
                    work_with_bd.database[int(client_id)]['uuid'] = ''
                    await work_with_bd.AddUser({int(client_id): work_with_bd.database[int(client_id)]})
                    await message.answer(f'Пользователь {client_id} успешно удалён')
                    logger.info(f'Пользователь {client_id} успешно удалён')
                    await bot.send_message(client_id, f'Администратор удалил вашу ссылку, за подробностями обращайтесь к администратору')
                else:
                    await message.answer(f'Ошибка удаления {client_id}')
                    logger.info(f'Ошибка удаления пользователя {client_id}')
            else:
                await message.answer('Ошибка удаления пользователя, проверь формат ввода: /v client_tg_id')
                logger.info(f'Ошибка верификации пользователя {args[1]}')
        else:
            await message.answer('У тебя нет прав для удаления пользователей')
            logger.info(f'Сторонний пользователь({tg_id}) пытался удалить клиента({args[1]})')

def register_handlers(dp: Dispatcher):
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(reg_name, state_user.name)
    dp.message.register(reg_lastname, state_user.lastname)
    dp.message.register(instructions, state_user.work, F.text == "Инструкция")
    dp.message.register(create_profile, state_user.work, F.text == "Получить ссылку")
    dp.message.register(admin_instructions, state_user.work, F.text == "Команды администратора")
    dp.message.register(verify_user, state_user.work, Command("v"))
    dp.message.register(del_verify_user, state_user.work, Command("dv"))
    dp.message.register(start_state)