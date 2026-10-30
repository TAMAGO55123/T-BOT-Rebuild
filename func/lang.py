import discord
from typing import Literal
from enum import Enum

langs = [
    "Japanese",
    "English",
    "Chinese",
    "Korean"
]

ModalSelectOptions:list[discord.SelectOption] = [discord.SelectOption(label=i, value=i) for i in langs]
CommandOptions = Literal[*langs]