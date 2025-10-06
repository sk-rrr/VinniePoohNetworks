# Импорт библиотек
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import work_with_bd

# Загружаем данные из .env
load_dotenv('data.env')
API_TOKEN = os.getenv('TOKEN')

# Создаём бота и диспетчер
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
# Импортируем обработку сообщений, работает только после объявления диспетчера
import handlers
# Регистрируем обработчики
handlers.register_handlers(dp)

# Точка входа с восстановлением состояния
async def main():
    # Создаём пул
    await work_with_bd.init_db_pool()
    global database
    database = await work_with_bd.GetDB()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())