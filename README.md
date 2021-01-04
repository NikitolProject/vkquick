# VK Quick
[![Downloads](https://static.pepy.tech/personalized-badge/vkquick?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/vkquick)

> Хорошие инструменты порождают не только творения, но и идеи

Можно много говорить о VK Quick, но сразу перейдем к созданию бота ВКонтакте...

# Установка
Для начала нужно проверить версию Python:
```shell script
python -V
```
Если она выше, чем `3.8`, можно переходить к установке:

```shell script
python -m pip install vkquick
```

> До релиза 1.0: `python -m pip install git+https://github.com/Rhinik/vkquick@1.0`

Нужно проверить, корректно ли установился VK Quick:
```shell script
python -m pip show vkquick
```

Вместе с фреймворком устанавливается `vq` — терминальная утилита (CLI), немного упрощающая создание ботов. Проверим и её:

```shell script
vq --help
```

> Если `vq` установился некорректно, можно запустить CLI через запуск самого пакета: `python -m vkquick --help`

Если установка прошла успешно, можно переходить к созданию самого простого бота


# Hello-бот
Для начала нам необходимо получить специальный токен — ключ, с помощью которого можно будет взаимодействовать с группой или аккаунтом пользователя

* Как получить токен для пользователя

* Как получить токен для группы и включить необходимые настройки для ботов

В качестве примера мы будем создавать бота именно для группы, но Вы всегда сможете просто подставить другой токен и писать бота уже для пользователя всё с тем же интерфейсом

```python
import vkquick as vq


bot =  vq.Bot.init_via_token("your-token")


@bot.add_command(names="hi")
def hello():
    return "hello!"


bot.run()
```

Запускаем пример выше, подставляя токен. Теперь, если написать боту `hi` в личные сообщения, то он ответит нам `hello!`

> Бот также будет работать в любой беседе, но для этого необходимо в беседе выдать боту права администратора или полного доступа к переписке
