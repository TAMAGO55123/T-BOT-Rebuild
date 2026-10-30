import discord
from discord.ext import commands
from discord import app_commands
from func.dc import Bot
from func.log import get_log
from func.tools import convert_size
import datetime
import aiohttp
import jpholiday
from random import randint
import io
import re
import psutil
import os
import asyncio

class FunCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")

    class Fun(app_commands.Group):
        pass

    fun = Fun(name="fun", description="娯楽用コマンド")

    @fun.command(name="aniv", description="記念日を取得します。")
    @app_commands.describe(
        year="年を指定します(指定する場合はすべて指定してください)",
        month="月を指定します(指定する場合はすべて指定してください)",
        day="日を指定します(指定する場合はすべて指定してください)"
    )
    async def aniv(self, interaction:discord.Interaction, year:int = None, month:int = None, day:int = None):
        await interaction.response.defer(thinking=True)
        is_today = year == None or month == None and day == None
        if is_today is False:
            d = f"{str(month).zfill(2)}{str(day).zfill(2)}"
            date = datetime.date(year=year, month=month, day=day)
        else:
            d = datetime.date.today().strftime("%m%d")
            date = datetime.date.today()
        async with aiohttp.ClientSession() as session:
            # powered by whatistodayAPI | https://note.com/sooz/n/naffb68c7f53b
            async with session.get(f"https://api.whatistoday.cyou/index.cgi/v3/anniv/{d}") as resp:
                data = await resp.json()
        self.log.debug(data)
        holiday = jpholiday.is_holiday_name(date=date)
        anniv = []
        anniv.append(data["anniv1"])
        if data["anniv2"] != "":
            anniv.append(data["anniv2"])
        if data["anniv3"] != "":
            anniv.append(data["anniv3"])
        if data["anniv4"] != "":
            anniv.append(data["anniv4"])
        if data["anniv5"] != "":
            anniv.append(data["anniv5"])
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{"今日" if is_today else date.strftime("%Y/%m/%d")}は何の日?",
                description=f"{f"今日は祝日です！\n- {holiday}\n" if holiday else ""}- {"\n- ".join(anniv)}",
                colour=discord.Colour.green()
            )
            .set_footer(text="powered by whatistodayAPI")
        )

    @fun.command(name="role_count", description="ロールの数を数えます")
    @app_commands.describe(
        member="指定したユーザーのロールを数えます(指定しない場合自分自身になります)"
    )
    async def role_count(self, interaction:discord.Interaction, member:discord.Member = None):
        user = member if member else interaction.user
        color = discord.Colour.random()
        roles = user.roles[1:]
        roles.reverse()

        await interaction.response.send_message(
            embeds=[
                discord.Embed(
                    title=f"{user.display_name}のロール数",
                    description=f"{len(roles)}個",
                    colour=color
                ),
                discord.Embed(
                    title="ロール一覧",
                    description=f"- {"\n- ".join([i.name for i in roles])}",
                    colour=color
                )
            ]
        )

async def setup(bot):
    await bot.add_cog(FunCog(bot))
