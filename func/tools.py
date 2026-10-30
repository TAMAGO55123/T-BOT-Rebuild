from typing import TypeVar, Tuple
import copy
import discord
from os import getenv
from dotenv import load_dotenv
import math
from func import errors as Errors
load_dotenv()

T = TypeVar("T")

def list_all(*args:T) -> list[T]:
    r_l:list[T] = []
    for i in args:
        if i != None:
            r_l.append(i)
    return r_l

Mention_False:discord.AllowedMentions = discord.AllowedMentions(
    roles=False,
    users=False,
    replied_user=False,
    everyone=False
)



def is_bot_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in interaction.client.config.get("admin", []):
            return True
        else:
            raise Errors.BotAdminCheckFailure(message=f"The User ({interaction.user.name}) is not Bot Admin.", user=interaction.user)
    return discord.app_commands.check(predicate)

def convert_size(size:int) -> str:
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB")
    i = math.floor(math.log(size, 1024)) if size > 0 else 0
    size = round(size / 1024 ** i, 2)

    return f"{size} {units[i]}"