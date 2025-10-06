import os
import asyncpg
from dotenv import load_dotenv

# Загружаем данные из .env
load_dotenv('data.env')
DBNAME = os.getenv('DBNAME')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

# БД будет сохраняться в этот словарь
user = dict()

# Указываем тип переменной, пул соединений пока не создан
pool: asyncpg.Pool = None
# Объявляем БД в словаре
database: dict = {}
temp_data: dict = {}

# Функция, создающая пул соединений, для оптимизации
async def init_db_pool():
    global pool
    pool = await asyncpg.create_pool(
        database=DBNAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=int(PORT)
    )

# Извлекаем данные из БД в словарь
async def GetDB():
    global database
    try:
        # Получаем данные из БД
        async with pool.acquire() as conn:
            rows = await conn.fetch('SELECT id, name, lastname FROM users')
            database = {r['id']: {'name': r['name'], 'lastname': r['lastname']} for r in rows}
        print('INFO: БД загружена')
        return database
    except Exception as error:
        print('INFO ERROR LOAD:', error)

# Добавляем/обновляем пользователей в БД
async def AddUser(data: dict):
    # Если массив пустой, выполнение функции сразу прекращается
    if not data:
        return
    records = [(id, v['name'], v['lastname']) for id, v in data.items()]
    # Запрос в БД
    query = '''
                INSERT INTO users(id, name, lastname)
                VALUES($1, $2, $3)
                ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name, lastname = EXCLUDED.lastname;
            '''
    try:
        async with pool.acquire() as conn:
            await conn.executemany(query, records)
        print('INFO: Пользователи добавлены/обновлены')
    except Exception as error:
        print('INFO ERROR UPDATE:', error)