# Импорт библиотек
import aiohttp
import asyncio
from transliterate import translit
import os
import uuid
from dotenv import load_dotenv
import ssl
import json
from logger import logger
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log

from transliterate.conf import settings

# Загружаем данные из .env
load_dotenv('data.env')
IP3XUI = os.getenv('IP3XUI')
LOG3XUI = os.getenv('LOG3XUI')
PASS3XUI = os.getenv('PASS3XUI')
INBOUND = os.getenv('INBOUND')
VLESSPORT = os.getenv('VLESSPORT')

# Класс для работы с 3x-ui
class XUI:
    global_headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json'
    }
    # Аргументы класса
    def __init__(self, host: str = IP3XUI, username: str = LOG3XUI, password: str = PASS3XUI, timeout: int = 3):
        self.__host = host
        self.__username = username
        self.__password = password
        self.__timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self.inbound = None

    # Добавляем возможность работать асинхронно с контекстным менеджером with
    async def __aenter__(self):
        # Для игнорирования самоподписанного сертификата
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.session = aiohttp.ClientSession(timeout=self.__timeout, connector=aiohttp.TCPConnector(ssl=ssl_context))
        # Логинимся при создании клиента и возвращаем self для последующих вызовов клиента
        await self.login()
        return self

    # Автоматический выход при завершении контекстного менеджера
    async def __aexit__(self, *args):
        await self.session.close()

    # Авторизация через логин и пароль
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),  # увеличивает время ожидания между попытками
        stop=stop_after_attempt(3),  # максимум 3 попытки
        before=before_log(logger, logger.info),  # лог перед каждой попыткой
        after=after_log(logger, logger.warning)  # лог после каждой попытки
    )
    async  def login(self):
        # Подготовка к запросу
        login_url = f'{self.__host.replace('panel/', 'login')}'
        data = {'username': self.__username, 'password': self.__password}
        # Пробуем 3 раза на случай кратковременных сбоем
        try:
            async with self.session.post(login_url, json=data, headers=self.global_headers) as response:
                if response.status == 200:
                    logger.info('Успешное подключение к 3x-ui')
                    self.session.cookie_jar.update_cookies(response.cookies)
                    return
                elif response.status == 401:
                    logger.error('Неверный логин или пароль для 3x-ui')
                # Обрабатывает остальные ошибки
                else:
                    logger.error(f'{response.status} {await response.text()}')
        except aiohttp.ClientConnectionError as error:
            logger.exception(f'Cервер недоступен({error})')
        except asyncio.TimeoutError as error:
            logger.exception(f'Таймаут соединения(>{self.__timeout} секунд)({error})')
        except aiohttp.ClientError as error:
            logger.exception(f'Ошибка клиента aiohttp: {error}')
        except Exception as error:
            logger.exception(f'Неизвестная ошибка: {error}')
        logger.error('Не удалось подключиться к 3x-ui после 3 попыток')
        raise ConnectionError('Не удалось подключиться к 3x-ui после 3 попыток')

    # Функция запроса inbound`a
    async def get_inbound(self, inbound_id: str = INBOUND):
        async with self.session.get(f'{IP3XUI}api/inbounds/get/{inbound_id}', headers=self.global_headers) as response:
            if response.status == 200:
                self.inbound = await response.json()
                logger.info('Успешно получен inbound из 3X-UI')
            else:
                logger.error(f"Ошибка получения inbound`а: {response.status} {await response.json()}")
                raise Exception(f"Ошибка получения inbound`а: {response.status} {await response.json()}")

    # Формирование ссылки для пользователя
    async def create_link_for_user(self, email: str, user_id: str, port: str = VLESSPORT):
        # Извлекаем нужные параметры из inbound
        stream = self.inbound.get('streamSettings', {})
        reality = stream.get('realitySettings', {})
        security = stream.get('security', 'reality')
        sni = stream.get('serverNames')[0]
        public_key = stream.get('publicKey')
        short_id = ''.join(stream.get('shortIds'))
        network_type = stream.get('network', 'tcp')
        link = (
            f"vless://{user_id}@{self.__host.replace('http://', '').replace('https://', '').replace('2808', f'{port}').replace('/dashboard/panel/', '')}"
            f"?security={security}"
            f"&sni={sni}"
            f"&fp=chrome"
            f"&pbk={public_key}"
            f"&sid={short_id}"
            f"&spx=/"
            f"&type={network_type}"
            f"&flow={settings['clients'][0]['flow']}"
            f"&encryption=none"
            f"#{email}"
        )
        return link

    # Добавления пользователя в 3x-ui
    async def add_user(self, tg_id: str, username: str, inbound_id: str = INBOUND):
        # Получаем существующий inbound
        await self.get_inbound()

        # Создаём нового пользователя в готовом inbound с параметрами
        # email: имя пользователя_tgid, в id сгенерированный id(uuid),  flow: xtls-rprx-vision
        email = f'{translit(username, 'ru', reversed=True)}_{tg_id}'
        user_id = str(uuid.uuid4())
        settings = {"clients": [{
                    "id": f"{user_id}",
                    "flow": "xtls-rprx-vision",
                    "email": f"{email}",
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "enable": True,
                    "tgId": "",
                    "subId": "",
                    "comment": "",
                    "reset": 0
                    }]}
        payload = {'id': int(inbound_id), 'settings': json.dumps(settings)}
        # Формируем ссылку запроса
        url = f'{self.__host}api/inbounds/addClient'

        # Отправка POST запроса
        async with self.session.post(url, json=payload, headers=self.global_headers) as response:
            if response.status in [200, 201]:
                link = await self.create_link_for_user(email, user_id)
                logger.info(f'Успешное создание профиля пользователя {tg_id} в 3X-UI')
            else:
                logger.error(f"Ошибка профиля пользователя {tg_id} в 3X-UI: {response.status} {await response.json()}")
                raise Exception(f"Ошибка профиля пользователя {tg_id} в 3X-UI: {response.status} {await response.json()}")
            return link, user_id
        logger.info(f'Успешно добавлен профиль пользователя {tg_id} в 3X-UI')

    # Обновление ссылки пользователя
    async def get_link(self, user_id: str, tg_id: str, username: str):
        # Получаем существующий inbound
        await self.get_inbound()

        # Обновляем параметры с имеющимся параметрами
        # email: имя пользователя_tgid, в id переданный id(uuid)
        email = f'{translit(username, 'ru', reversed=True)}_{tg_id}'
        # Генерация ссылки
        link = await self.create_link_for_user(email, user_id)
        logger.info(f'Успешно обновлена ссылка пользователя {tg_id}')
        return link

    # Удаление пользователя из 3x-ui
    async def del_user(self, uuid: str, inbound_id: str = INBOUND):
        # Формируем ссылку запроса
        url = f'{self.__host}api/inbounds/{inbound_id}/delClient/{uuid}'
        # Отправка POST запроса
        try:
            async with self.session.post(url, headers=self.global_headers) as response:
                if response.status in [200, 201, 204]:
                    logger.info(f"Пользователь {uuid} успешно удалён из inbound {inbound_id}")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Ошибка удаления пользователя {uuid}: {response.status} {text}")
                    raise Exception(f"Ошибка удаления пользователя {uuid}: {response.status} {text}")
        except Exception as error:
            logger.exception(f"Не удалось удалить пользователя {uuid}: {error}")