"""
VK Quick — это высокоуровневная надстройка над API для ботов Вконтакте.
Инструменты, предлагаемые этим фреймворком, помогут Вам написать
мощного по возможностям и функционалу бота.
Большинство работы VK Quick берет на себя:
помощь разработчику в обработке содержимого команд,
огромное множество специальных оберток и функций,
создание документации к боту в виде команд в боте или же полноценного сайта
"""
from .current import fetch, curs
from .api import API, TokenOwner
from .bot import Bot
from .exceptions import VkApiError
from .signal import SignalCaller, SignalName, SignalHandler, ReservedSignal
from .debuggers import (
    ColoredDebugger,
    UncoloredDebugger,
    uncolored_text,
    Color,
)
from .utils import (
    AttrDict,
    SafeDict,
    peer,
    random_id,
    clear_console,
    sync_async_run,
)

from .json_parsers import BuiltinJSONParser

from .events_generators.event import Event
from .events_generators.longpoll import GroupLongPoll, UserLongPoll

from .event_handling.message import Message
from .event_handling.command import Command
from .event_handling.event_handler import EventHandler
from .event_handling.handling_info_scheme import HandlingInfoScheme

from .base.text_argument import TextArgument
from .base.text_argument import UnmatchedArgument
from .event_handling.text_arguments.integer import Integer
from .event_handling.text_arguments.word import Word
from .event_handling.text_arguments.string_ import String
from .event_handling.text_arguments.union import Union
from .event_handling.text_arguments.regex import Regex
from .event_handling.text_arguments.bool_ import Bool
from .event_handling.text_arguments.list_ import List
from .event_handling.text_arguments.mention import UserMention
from .event_handling.text_arguments.text_values_base import TextBase
from .event_handling.text_arguments.optional import Optional

from .base.payload_argument import PayloadArgument
from .event_handling.payload_arguments.sender import Sender
from .event_handling.payload_arguments.replied_user import RepliedUser
from .event_handling.payload_arguments.current import Current
from .event_handling.payload_arguments.captured_event import CapturedEvent
from .event_handling.payload_arguments.answer import Answer

from .base.filter import Filter, FilterResponse, Decision, DecisionStatus
from .event_handling.filters.enable import Enable, EnableStatus

from .wrappers.user import User

__version__ = "1.0.0a2"
