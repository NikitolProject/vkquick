from __future__ import annotations

import typing as ty

from vkquick.ext.chatbot.ui_builders.base import UIBuilder
from vkquick.ext.chatbot.ui_builders.button import InitializedButton


class Keyboard(UIBuilder):
    def __init__(
        self,
        *buttons: ty.Union[InitializedButton, type(Ellipsis)],
        one_time: bool = True,
        inline: bool = False
    ) -> None:
        self.scheme = {"inline": inline, "buttons": [[]]}
        if not inline:
            self.scheme.update(one_time=one_time)

        self.build(*buttons)

    @staticmethod
    def empty():
        return '{"buttons":[],"one_time":true}'

    def add(self, button: InitializedButton) -> Keyboard:
        """
        Добавляет в клавиатуру кнопку
        """
        self.scheme["buttons"][-1].append(button.scheme)
        return self

    def add_line(self) -> Keyboard:
        if not self.scheme["buttons"][-1]:
            raise ValueError("Can't add a new line if the last line is empty")
        self.scheme["buttons"].append([])
        return self

    def build(
        self, *buttons: ty.Union[InitializedButton, type(Ellipsis)]
    ) -> Keyboard:
        for button in buttons:
            if button is Ellipsis:
                self.add_line()
            else:
                self.add(button)
        return self
