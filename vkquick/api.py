from __future__ import annotations

import asyncio
import enum
import os
import re
import time
import typing as ty
import urllib.parse

import aiohttp
import cachetools
from loguru import logger

from vkquick.bases.api_serializable import APISerializableMixin
from vkquick.bases.session_container import SessionContainerMixin
from vkquick.exceptions import VKAPIError
from vkquick.json_parsers import json_parser_policy

if ty.TYPE_CHECKING:
    from vkquick.bases.json_parser import JSONParser


class TokenOwnerType(enum.Enum):
    """
    Тип владельца токена: пользователь/группа
    """

    USER = enum.auto()
    GROUP = enum.auto()


class TokenOwnerEntity:
    """
    Сущность владельца токена,
    возвращаемая при вызове метода [API.token_owner_entity](vkquick.api.API.fetch_token_owner_entity)
    """

    def __init__(
        self,
        entity_type: TokenOwnerType,
        scheme: ty.Optional[dict] = None,
    ) -> None:
        """
        Args:
            entity_type: Тип владельца токена
            scheme: Объект владельца токена (для сервисных токенов отсутствует)
        """
        self.entity_type = entity_type
        self.scheme = scheme

    def is_group(self) -> bool:
        """
        Является ли сущность группой
        """
        return self.entity_type == TokenOwnerType.GROUP

    def is_user(self) -> bool:
        """
        Является ли сущность пользователем
        """
        return self.entity_type == TokenOwnerType.USER


class API(SessionContainerMixin):
    """
    Api requests
    """

    def __init__(
        self,
        token: str,
        *,
        version: ty.Union[float, str] = "5.135",
        requests_url: str = "https://api.vk.com/method/",
        requests_session: ty.Optional[aiohttp.ClientSession] = None,
        json_parser: ty.Optional[JSONParser] = None,
    ) -> None:
        """
        Arguments:
            token: Токен пользователя/группы/сервисный для отправки API запросов.
                Можно использовать имя переменной окружения,
                если добавить в начало `"$"`, т.е. `"$ENV_VAR"`
            version: Версия используемого API.
            requests_url: URL для отправки запросов.
            requests_session: Собственная `aiohttp` сессия.
            json_parser: Кастомный JSON парсер
        """
        super().__init__(
            requests_session=requests_session, json_parser=json_parser
        )

        # Автоматическое получение токена из переменных окружения
        if token.startswith("$"):
            self._token = os.getenv(token[1:])
        else:
            self._token = token

        self._version = version
        self._requests_url = requests_url
        self._cache_table = cachetools.TTLCache(ttl=3600, maxsize=2 ** 15)

        self._method_name = ""
        self._last_request_stamp = 0
        self._requests_delay = 0
        self._token_owner = None
        self._stable_request_params = {
            "access_token": self._token,
            "v": self._version,
        }

    @property
    def token(self) -> str:
        """
        Токен, используемые для API запросов
        """
        return self._token

    def __getattr__(self, attribute: str) -> API:
        """
        Используя `__gettattr__`, класс предоставляет возможность
        вызывать методы API, как будто обращаясь к атрибутам.
        Пример есть в описании класса.

        Arguments:
            attribute: Имя/заголовок названия метода.
        Returns:
            Собственный инстанс класса для того,
            чтобы была возможность продолжить выстроить имя метода через точку.
        """
        if self._method_name:
            self._method_name += f".{attribute}"
        else:
            self._method_name = attribute
        return self

    async def __call__(
        self,
        __allow_cache: bool = False,
        **request_params,
    ) -> ty.Any:
        """
        Выполняет необходимый API запрос с нужным методом и параметрами,
        добавляя к ним токен и версию (может быть перекрыто).

        Arguments:
            __allow_cache: Если `True` -- результат запроса
                с подобными параметрами и методом будет получен из кэш-таблицы,
                если отсутствует -- просто занесен в таблицу. Если `False` -- запрос
                просто выполнится по сети.
            request_params: Параметры, принимаемы методом, которые описаны в документации API.

        Returns:
            Пришедший от API ответ.
        """
        method_name = self._method_name
        self._method_name = ""
        return await self._make_api_request(
            method_name=method_name,
            request_params=request_params,
            allow_cache=__allow_cache,
        )

    async def fetch_token_owner_entity(self) -> TokenOwnerEntity:
        """
        Возвращает сущность владельца токена.

        В зависимости от результата вызова метода `users.get`
        определяет тип владельца токена (пользователь, группа, токен сервисный)
        и задержку для запросов.

        :return: Сущность владельца токена
        """
        if self._token_owner is None:
            # Убираем `None`, чтобы запрос строкой ниже выполнился
            self._token_owner = ...
            owner = await self.users.get()

            if owner:
                self._token_owner = TokenOwnerEntity(
                    TokenOwnerType.USER, owner[0]
                )
                self._requests_delay = 1 / 3
            else:
                owner = await self.groups.get_by_id()
                self._token_owner = TokenOwnerEntity(
                    TokenOwnerType.GROUP, owner[0]
                )
                self._requests_delay = 1 / 20

            return self._token_owner

        else:
            return self._token_owner

    async def method(
        self,
        method_name: str,
        request_params: ty.Dict[str, ty.Any],
        /,
        *,
        allow_cache: bool = False,
    ) -> ty.Any:
        """
        Выполняет необходимый API запрос с нужным методом и параметрами.

        :param __method_name: Имя вызываемого метода API
        :param __request_params: Параметры, принимаемы методом, которые описаны в документации API.
        :param allow_cache: Если `True` -- реузультат запроса
            с подобными параметрами и методом будет получен из кэш-таблицы,
            если отсутствует -- просто занесен в таблицу. Если `False` -- запрос
            просто выполнится по сети.

        :return: Пришедший от API ответ.

        :raises VKAPIError: В случае ошибки, пришедшей от некорректного вызова запроса.
        """
        return await self._make_api_request(
            method_name=method_name,
            request_params=request_params,
            allow_cache=allow_cache,
        )

    async def execute(self, __code: str) -> ty.Any:
        """
        Исполняет API метод `execute` с переданным VKScript-кодом.

        Arguments:
            __code: VKScript код

        Returns:
            Пришедший ответ от API

        Raises:
            VKAPIError: В случае ошибки, пришедшей от некорректного вызова запроса.
        """
        return await self.method("execute", {"code": __code})

    async def _make_api_request(
        self,
        method_name: str,
        request_params: ty.Dict[str, ty.Any],
        allow_cache: bool,
    ) -> ty.Any:
        """
        Выполняет API запрос на определнный метод с заданными параметрами

        :param method_name: Имя метода API
        :param request_params: Параметры, переданные для метода
        :param allow_cache: Использовать кэширование

        :raises VKAPIError: В случае ошибки, пришедшей от некорректного вызова запроса.
        """
        # Конвертация параметров запроса под особенности API и имени метода
        real_method_name = _convert_method_name(method_name)
        real_request_params = _convert_params_for_api(request_params)
        extra_request_params = self._stable_request_params.copy()
        extra_request_params.update(real_request_params)
        real_request_params = extra_request_params

        # Определение владельца токена нужно
        # для определения задержки между запросами
        if self._token_owner is None:
            await self.fetch_token_owner_entity()

        # Кэширование запросов по их методу и переданным параметрам
        # `cache_hash` -- ключ кэш-таблицы
        if allow_cache:
            cache_hash = urllib.parse.urlencode(real_request_params)
            cache_hash = f"{method_name}#{cache_hash}"
            if cache_hash in self._cache_table:
                return self._cache_table[cache_hash]

        # Задержка между запросами необходима по правилам API
        api_request_delay = self._get_waiting_time()
        await asyncio.sleep(api_request_delay)

        # Отправка запроса с последующей проверкой ответа
        response = await self._send_api_request(
            real_method_name, real_request_params
        )
        logger.info(
            "Called method {method_name}({method_params})",
            method_name=method_name,
            method_params=request_params,
        )
        logger.debug("Response is: {response}", response=response)

        if "error" in response:
            raise VKAPIError.destruct_response(response)
        else:
            response = response["response"]

        # Если кэширование включено -- запрос добавится в таблицу
        if allow_cache:
            self._cache_table[cache_hash] = response

        return response

    async def _send_api_request(self, method_name: str, params: dict) -> dict:
        async with self.requests_session.post(
            self._requests_url + method_name, data=params
        ) as response:
            loaded_response = await self.parse_json_body(response)
            return loaded_response

    def _get_waiting_time(self) -> float:
        """
        Рассчитывает обязательное время задержки после
        последнего API запроса. Для групп -- 0.05s,
        для пользователей/сервисных токенов -- 0.333s

        Returns:
            Время, необходимое для ожидания.
        """
        now = time.time()
        diff = now - self._last_request_stamp
        if diff < self._requests_delay:
            wait_time = self._requests_delay - diff
            self._last_request_stamp += wait_time
            return wait_time
        else:
            self._last_request_stamp = now
            return 0

    def __repr__(self):
        owner = self._token_owner
        if owner is None:
            return f"<vkquick.{self.__class__.__name__}>"
        else:
            if owner.is_group():
                owner_name = owner.scheme["name"]
            else:
                owner_name = f"{owner.scheme['first_name']} {owner.scheme['last_name']}"
            return f"<vkquick.{self.__class__.__name__} owner={owner_name!r}>"


def _convert_param_value(value, /):
    """
    Конвертирует параметер API запроса в соотвествиями
    с особенностями API и дополнительными удобствами

    Args:
        value: Текущее значение параметра

    Returns:
        Новое значение параметра

    """
    # Для всех перечислений функция вызывается рекурсивно.
    # Массивы в запросе распознаются вк только если записать их как строку,
    # перечисляя значения через запятую
    if isinstance(value, (list, set, tuple)):
        updated_sequence = map(_convert_param_value, value)
        new_value = ",".join(updated_sequence)
        return new_value

    # Все словари, как списки, нужно сдампить в JSON
    elif isinstance(value, dict):
        new_value = json_parser_policy.dumps(value)
        return new_value

    # Особенности `aiohttp`
    elif isinstance(value, bool):
        new_value = int(value)
        return new_value

    # Если класс определяет протокол сериализации под параметр API,
    # используется соотвествующий метод
    elif isinstance(value, APISerializableMixin):
        new_value = value.represent_as_api_param()
        new_value = _convert_param_value(new_value)
        return new_value

    else:
        new_value = str(value)
        return new_value


def _convert_params_for_api(params: dict, /):
    """
    Конвертирует словарь из параметров для метода API,
    учитывая определенные особенности

    Args:
        params: Параметры, передаваемые для вызова метода API

    Returns:
        Новые параметры, которые можно передать
        в запрос и получить ожидаемый результат

    """
    updated_params = {
        (key[:-1] if key.endswith("_") else key): _convert_param_value(value)
        for key, value in params.items()
        if value is not None
    }
    return updated_params


def _upper_zero_group(match: ty.Match, /) -> str:
    """
    Поднимает все символы в верхний
    регистр у captured-группы `let`. Используется
    для конвертации snake_case в camelCase.

    Arguments:
      match: Регекс-группа, полученная в реультате `re.sub`

    Returns:
        Ту же букву из группы, но в верхнем регистре

    """
    return match.group("let").upper()


def _convert_method_name(name: str, /) -> str:
    """
    Конвертирует snake_case в camelCase.

    Args:
      name: Имя метода, который необходимо перевести в camelCase

    Returns:
        Новое имя метода в camelCase

    """
    return re.sub(r"_(?P<let>[a-z])", _upper_zero_group, name)
