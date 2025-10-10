# Импорт библиотек
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from logger import logger
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

# Логирование запуска
async def on_startup(_):
    logger.info("✅ Бот успешно запущен и готов к работе!")
async def on_shutdown(_):
    logger.info("🛑 Бот остановлен.")

# Точка входа с восстановлением состояния
async def main():
    # Создаём пул
    await work_with_bd.init_db_pool()
    global database
    database = await work_with_bd.GetDB()
    '''# Подключение логирования на запуск
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)'''
    # Функция запуск бота
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())