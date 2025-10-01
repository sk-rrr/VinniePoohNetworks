import os
import psycopg2
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

# Извлекаем данные из БД в словарь
def GetDB():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as conn:
        with conn.cursor() as cur:
            # Получаем данные из БД
            cur.execute('SELECT id, name, lastname FROM users')
            rows = cur.fetchall()
            # Преобразуем в словарь
            user = {
                id: {'name': name, 'lastname': lastname}
                for id, name, lastname in rows
            }
            print('INFO: БД загружена')
            return user

# Обновляем данные в БД из словаря
def UpdateBD(data):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as conn:
        with conn.cursor() as cur:
            # Полная очистка БД
            cur.execute('TRUNCATE TABLE users')
            # Загрузка новых данных
            for id, value in data.items():
                cur.execute(
                    'INSERT INTO users (id, name, lastname) VALUES (%s, %s, %s)',
                    (id, value['name'], value['lastname'])
                    )
        # Сохранение изменений
        conn.commit()
        print('INFO: БД обновлена')