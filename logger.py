# Импорт библиотек
import logging
from rich.logging import RichHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Минимальный уровень сообщений, которые будут отображаться
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",  # Формат вывода
    datefmt="[%X]",  # Формат времени (часы:минуты:секунды)
    handlers=[
        RichHandler(rich_tracebacks=True, show_path=False),  # Красивый вывод в консоль
        logging.FileHandler("bot.log", encoding="utf-8"),  # Запись логов в файл
    ]
)

# Отсечение служебной информации библиотек, логируются только ошибки
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Создаём главный логер
logger = logging.getLogger("Bot")