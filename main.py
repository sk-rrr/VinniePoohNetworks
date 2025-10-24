# Импорт библиотек
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from logger import logger
import work_with_bd

# Создаём бота и диспетчер
from config import bot
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
    # Функция запуск бота
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())