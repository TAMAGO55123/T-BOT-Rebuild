import discord
from discord.ext import commands
from discord import app_commands
from func.dc import Bot
from func.log import get_log
from func.file import File
import numpy as np
import numpy.random as rd
import regex as re
import time

class DiceCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
        self.dice_re = re.compile(r'^(\d+)d(\d+)(?: +(\d+))?(?: +(.*))?$')
        self.file = File("database/dice.json")

        self.bot.config.default("dice_guild", [])
        self.bot.config.default("dice_channel", [])
        self.bot.config.default("dice_limit", 0)
        self.bot.config.default("dice_count_limit", 0)

    @staticmethod
    def format_result(
        values: np.ndarray,
        dice_count: int,
        dice_sides: int,
        target: int | None,
        success: bool | None,
        elapsed: str,
        result_limit: int
    ) -> tuple[str, bool]:
        total = np.sum(values)
        header = f"**{dice_count}d{dice_sides}{f' {target}' if target is not None else ''}**\n-->"
        suffix = f"-->合計{total}"
        status = f"{'-->成功' if success else '-->失敗'}" if success is not None else ""
        displayed: list[str] = []
        omitted = False

        for index, value in enumerate(map(str, values)):
            remaining = index < len(values) - 1
            candidate = ",".join(displayed + [value])
            candidate_array = f"{candidate},..." if remaining else candidate
            candidate_message = f"{header}{candidate_array}{suffix}{status}{elapsed}"
            if (
                len(candidate_array) > result_limit
                or len(candidate_message) > 4096
            ):
                omitted = True
                break
            displayed.append(value)

        result = ",".join(displayed)
        if omitted:
            result = f"{result},..." if result else "..."
        return f"{header}{result}{suffix}{status}{elapsed}", omitted

    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.guild is None:
            return
        if message.guild.id in self.file.get("dice_guild", []) or message.channel.id in self.file.get("dice_channel", []):
            b_t = time.time()
            reg = re.match(self.dice_re, message.content)
            if message.content == "dd":
                r = rd.randint(low=0, high=50) + 1
                embed = discord.Embed(
                    description=f"**1d100**\n-->{r}",
                    colour=discord.Colour.brand_green()
                )
                embed.set_author(
                    name=message.author.display_name,
                    icon_url=message.author.display_avatar.url
                )
                await message.reply(
                    embed=embed
                )
            elif reg:
                t = reg.groups()
                dice_limit = self.bot.config.get("dice_limit", 0)
                dice_count = int(t[0])
                dice_sides = int(t[1])
                target = int(t[2]) if t[2] is not None else None
                if isinstance(dice_limit, int) and dice_limit > 0:
                    if dice_count > dice_limit:
                        await message.reply(
                            embed=discord.Embed(
                                title="エラー",
                                description=f"個数制限は{dice_limit}個です。指定された個数は{dice_count}個です。",
                                colour=discord.Colour.red()
                            ),
                            silent=True
                        )
                        return
                r = rd.randint(low=1, high=dice_sides + 1, size=dice_count)
                sum = np.sum(r)
                if target is not None:
                    if target >= sum:
                        suc = True
                        colour = discord.Colour.brand_green()
                    else:
                        suc = False
                        colour = discord.Colour.red()
                else:
                    suc = None
                    colour = discord.Colour.brand_green()

                dice_count_limit = self.bot.config.get("dice_count_limit", 100)
                if not isinstance(dice_count_limit, int) or dice_count_limit <= 0:
                    dice_count_limit = 100
                a_t = time.time()
                mes, omitted = self.format_result(
                    r,
                    dice_count,
                    dice_sides,
                    target,
                    suc,
                    f"\n\n計算時間: {a_t - b_t}ミリ秒",
                    dice_count_limit
                )
                embed = discord.Embed(
                    description=mes,
                    colour=colour
                )
                embed.set_author(
                    name=message.author.display_name,
                    icon_url=message.author.display_avatar.url
                )
                if omitted:
                    embed.set_footer(text="計算結果が長いため途中を省略しています。")
                await message.reply(
                    embed=embed
                )

    class diceGroup(app_commands.Group):
        pass
    dice = diceGroup(name="dice", description="ダイス機能を管理します。", default_permissions=discord.Permissions(manage_guild=True))

    @dice.command(name="enable", description="ダイス機能をサーバー全体で有効化します。" )
    async def enable(self, interaction:discord.Interaction):
        l:list[int] = self.file.get("dice_guild", [])
        if interaction.guild.id in l:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="すでに有効化されています",
                    colour=discord.Colour.red()
                )
            )
            return
        l.append(interaction.guild.id)
        self.file.set("dice_guild", l)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ダイス",
                description="正常に有効化されました。",
                colour=discord.Colour.green()
            )
        )

    @dice.command(name="disable", description="ダイス機能をサーバー全体で無効化します。")
    async def disable(self, interaction:discord.Interaction):
        l:list[int] = self.file.get("dice_guild", [])
        if interaction.guild.id not in l:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="無効化されています。",
                    colour=discord.Colour.red()
                )
            )
            return
        l.remove(interaction.guild.id)
        self.file.set("dice_guild", l)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ダイス",
                description="正常に無効化されました。",
                colour=discord.Colour.green()
            )
        )

    @dice.command(name="channel_enable", description="ダイス機能をチャンネル単位で有効化します。")
    @app_commands.describe(channel="指定したチャンネルで有効化します(指定しない場合は現在のチャンネルで有効化されます)")
    async def channel_enable(self, interaction:discord.Interaction, channel:discord.TextChannel = None):
        c = channel if channel else interaction.channel
        l:list[int] = self.file.get("dice_channel", [])
        if c in l:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="すでに有効化されています",
                    colour=discord.Colour.red()
                )
            )
            return
        l.append(c.id)
        self.file.set("dice_channel", l)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ダイス",
                description="正常に有効化されました。",
                colour=discord.Colour.green()
            )
        )

    @dice.command(name="channel_disable", description="ダイス機能をチャンネル単位で無効化します。")
    @app_commands.describe(channel="指定したチャンネルで無効化します(指定しない場合は現在のチャンネルで無効化されます)")
    async def channel_disable(self, interaction:discord.Interaction, channel:discord.TextChannel = None):
        c = channel if channel else interaction.channel
        l:list[int] = self.file.get("dice_channel", [])
        if c.id not in l:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="無効化されています。",
                    colour=discord.Colour.red()
                )
            )
            return
        l.remove(c.id)
        self.file.set("dice_channel", l)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ダイス",
                description="正常に無効化されました。",
                colour=discord.Colour.green()
            )
        )

    @dice.command(name="dice", description="ダイスを振ります")
    @app_commands.describe(
        dice="1d100の形式"
    )
    async def dice_only(self, interaction:discord.Interaction, dice:str):
        b_t = time.time()
        await interaction.response.defer()
        reg = re.match(self.dice_re, dice)
        t = reg.groups()
        dice_limit = self.bot.config.get("dice_limit", 0)
        dice_count = int(t[0])
        dice_sides = int(t[1])
        target = int(t[2]) if t[2] is not None else None
        if isinstance(dice_limit, int) and dice_limit > 0:
            if dice_count > dice_limit:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="エラー",
                        description=f"個数制限は{dice_limit}個です。指定された個数は{dice_count}個です。",
                        colour=discord.Colour.red()
                    ),
                    silent=True
                )
                return
        r = rd.randint(low=1, high=dice_sides + 1, size=dice_count)
        sum = np.sum(r)
        dice_count_limit = self.bot.config.get("dice_count_limit", 100)
        
        if target is not None:
            if target >= sum:
                suc = True
                colour = discord.Colour.brand_green()
            else:
                suc = False
                colour = discord.Colour.red()
        else:
            suc = None
            colour = discord.Colour.brand_green()
        
        if not isinstance(dice_count_limit, int) or dice_count_limit <= 0:
            dice_count_limit = 100
        a_t = time.time()
        mes, omitted = self.format_result(
            r,
            dice_count,
            dice_sides,
            target,
            suc,
            f"\n\n計算時間: {a_t - b_t}ミリ秒",
            dice_count_limit
        )
        embed = discord.Embed(
            description=mes,
            colour=colour
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )
        if omitted:
            embed.set_footer(text="計算結果が長いため途中を省略しています。")
        await interaction.followup.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(DiceCog(bot))
