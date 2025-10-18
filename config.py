from aiogram import Bot
import os
from dotenv import load_dotenv
# Загружаем данные из .env
load_dotenv('data.env')
API_TOKEN = os.getenv('TOKEN')
# Создаём бота и диспетчер
bot = Bot(token=API_TOKEN)