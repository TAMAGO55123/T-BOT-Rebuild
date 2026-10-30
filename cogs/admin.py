import discord
from discord.ext import commands
from discord import app_commands
from func.dc import Bot
from func.log import get_log
from func.tools import is_bot_admin
from func.file import File
from func import errors as Errors
import sys
import os

class AdminCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
        self.bot.config.default("admin", [])
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")

    class Admin(app_commands.Group):
        pass
    admin = Admin(name="admin", description="Bot管理者用コマンド", default_permissions=discord.Permissions(administrator=True))

    @admin.error
    async def admin_error(interaction:discord.Interaction, error):
        if isinstance(error, Errors.BotAdminCheckFailure):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="このコマンドはBot管理者専用です。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        get_log("AdminCog").error(error)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="エラー",
                description="コマンドの実行中に予期しないエラーが発生しました。",
                colour=discord.Colour.red()
            ),
            ephemeral=True
        )
    
    @admin.command(name="reload", description="再起動")
    @is_bot_admin()
    async def reload2(self, interaction: discord.Interaction):
        try:
            reload_mes = await interaction.response.send_message("Botを再起動します...")
            os.execv(sys.executable, ['python'] + sys.argv)
            await reload_mes.edit("再起動しました。")
            await self.bot.close()

        except Exception as e:
            await interaction.response.send_message(f"リロードに失敗しました: {e}")

    @admin.command(name="serverlist", description="サーバーリスト")
    @is_bot_admin()
    async def serverlist(self, interaction:discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="サーバーリスト",
                description=f"- {"\n- ".join(list(map(lambda i: f"{i.name}({i.id})", self.bot.guilds)))}",
                colour=discord.Colour.blue()
            ),
            ephemeral=True
        )

    @admin.command(name="invite_create", description="指定した導入済みサーバーの招待リンクを取得します")
    @is_bot_admin()
    @app_commands.describe(
        id="サーバーID"
    )
    async def invite_create(self, interaction:discord.Interaction, id:int):
        guild = discord.utils.get(self.bot.guilds, id=id)
        if guild:
            channel = next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).create_instant_invite
                ),
                None
            )

            if channel:
                invite = await channel.create_invite(reason="Bot管理者によるチェック用招待リンク作成")
                await interaction.response.send_message(
                    content=invite.url,
                    embed=discord.Embed(
                        title="招待を作成しました。",
                        description=f"対象: {guild.name}",
                        colour=discord.Colour.green()
                    )
                )
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="エラー",
                        description="権限のあるチャンネルが見つかりませんでした。",
                        colour=discord.Colour.red()
                    )
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="対象のサーバーが見つかりませんでした。",
                    colour=discord.Colour.red()
                )
            )

    @admin.command(name="changeok", description="/changeの許可リストを変更します")
    @is_bot_admin()
    async def changeok(self, interaction:discord.Interaction, add:str = None, remove:str = None):
        d:list[int] = self.bot.config.get("change_ignore", [])
        if add is not None and remove is None:
            if int(add) in d:
                await interaction.response.send_message(content="登録済み", ephemeral=True)
                return
            d.append(int(add))
            self.bot.config.set("change_ignore", d)
            d = self.bot.config.get("change_ignore", [])
            l = []
            for i in d:
                l.append(f"- {i}")
            await interaction.response.send_message(embed=discord.Embed(
                title="追加",
                description=f"現在のリスト\n{'\n'.join(l)}",
                colour=discord.Colour.green()
            ))
        elif add is None and remove is not None:
            if int(remove) not in d:
                await interaction.response.send_message(content="登録されていません", ephemeral=True)
                return
            d.remove(int(remove))
            self.bot.config.set("change_ignore", d)
            d = self.bot.config.get("change_ignore", [])
            l = []
            for i in d:
                l.append(f"- {i}")
            await interaction.response.send_message(embed=discord.Embed(
                title="削除",
                description=f"現在のリスト\n{'\n'.join(l)}",
                colour=discord.Colour.green()
            ))
        else:
            l = []
            for i in d:
                l.append(f"- {i}")
            await interaction.response.send_message(embed=discord.Embed(
                title="Now",
                description=f"現在のリスト\n{'\n'.join(l)}",
                colour=discord.Colour.green()
            ))



async def setup(bot):
    await bot.add_cog(AdminCog(bot))
