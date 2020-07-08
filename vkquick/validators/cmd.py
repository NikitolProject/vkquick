"""
Валидатор для пользвоательской текстовой команды
"""
from typing import List
from typing import Optional
from re import fullmatch
from re import IGNORECASE

from .base import Validator
from vkquick import Reaction


class Cmd(Validator):
    """
    Декоратор реакции для валидации
    пользоватлеьской команды по тексту из ```event.object.message.text```

    ## Параметры
    * `prefs`: Возможные префиксы для текстовой команды

    * `names`: Имена команды. Следуют сразу за префиксом (без пробела)

    * `sensetive`: Для True -- чувствительный к регистру символов

    * `argline`: По умолчанию все аргументы команды разделяются `\s+`,
    но вы можете создать свою _кастомную_ строку для аргументов
    (которая поддерживает регулярные выражения),
    обозначая сами аргументы {внутри фигурных скобок} и
    передавая имена этих аргументов
    в аргументы функции, в аннтациях обозначая тип.
    Например команду
    ```python
    @vq.Cmd(names=["hello"], argline="::{name}")
    @vq.Reaction("message_new")
    def hello(name: vq.Word()):
        return f"Hello, {name}!"
    ```
    можно вызвать следующим образом:

    1. ```hello::Bob```

        Ответ -> ```Hello, Bob!```

    1. ```hello::Tom```

        Ответ -> ```Hello, Tom!```

    1. ```hello::Ann```

        Ответ -> ```Hello, Ann!```

    Если же убрать параметр argline, то команда вызывается так:

    1. ```hello Bob```

        Ответ -> ```Hello, Bob!```

    1. ```hello Tom```

        Ответ -> ```Hello, Tom!```

    1. ```hello Ann```

        Ответ -> ```Hello, Ann!```

    .. note::
        `argline` воспринимается как регулярное выражение, поэтому, например, вместо
        `argline="++{name}"`
        нужно писать
        `argline="\+\+{name}"`
        потому что `+` -- это квантификатор
    """

    def __init__(
        self,
        *,
        prefs: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
        argline: Optional[str] = None,
        sensetive: bool = False,
    ):
        self.prefs = [] if prefs is None else prefs
        self.names = [] if names is None else names
        self.sensetive = sensetive
        self.argline = argline

        if not self.prefs:
            reprefs = ""
        elif len(self.prefs) == 1:
            reprefs = self.prefs[0]
        else:
            reprefs = f"(?:{'|'.join(self.prefs)})"

        if not self.names:
            renames = ""
        elif len(self.names) == 1:
            renames = self.names[0]
        else:
            renames = f"(?:{'|'.join(self.names)})"
        self.rexp = reprefs + renames


    def __call__(self, func):
        if self.argline is None:
            for name, value in func.command_args.items():
                self.rexp += rf"\s+(?P<{name}>{Reaction.convert(value).rexp})"
        else:
            comkwargs = {}
            for name, value in func.command_args.items():
                comkwargs[name] = f"(?P<{name}>{Reaction.convert(value).rexp})"
            self.rexp += self.argline.format(**comkwargs)

        super().__call__(func)
        return func

    def isvalid(self, event, com, bin_stack):
        matched = (
            fullmatch(self.rexp, event.object.message.text)
            if self.sensetive else
            fullmatch(self.rexp, event.object.message.text, flags=IGNORECASE)
        )
        if matched:
            bin_stack.command_frame = matched
            return (True, "")
        return (False, f"String `{event.object.message.text}` isn't matched for pattern `{self.rexp}`")
