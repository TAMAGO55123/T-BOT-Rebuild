import discord
from discord.ext import commands
from discord import app_commands
from func.dc import Bot
from func.log import get_log
from discord.http import Route
import aiohttp
from io import BytesIO
import base64
from discord.errors import HTTPException
import json
from func.file import File

def detect_image_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "png"

def bytesio_to_base64(bio: BytesIO) -> str:
    data = bio.getvalue()
    ext = detect_image_type(data)
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/{ext};base64,{b64}"

class ChangeCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")
    
    @app_commands.command(name="change", description="BOTのアイコンを名前などを変更します(限定サーバーのみ)")
    @app_commands.describe(
        name="Botの名前を指定します。指定しない場合、サーバーの名前が指定されます。",
        # banner_url="BotのバナーのURLを入力します。指定しない場合、ブーストが有効化されている場合はサーバーバナー、有効化されていない場合は何も指定されません。",
        avatar="BotのアイコンURLを入力します。指定しない場合、サーバーアイコン、アイコンがない場合は何も指定されません。",
        banner="現在無効になっています。設定してもなにもされません。",
        bio="ユーザーのプロフィールに表示される文字列を指定します。指定しない場合、何も指定されません。"
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def change(self, interaction:discord.Interaction, name:str = None, banner:discord.Attachment = None, avatar:discord.Attachment = None, bio:str = None):
        if f"{interaction.guild.id}" not in self.bot.config.get("change_ignore", []):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description=f"このサーバーは/changeが有効化されているサーバーではありません。\n承認を受けるには{self.bot.config.get("support", "(未設定)")}でチケットを作成してください。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            banner_bytes: BytesIO = None
            # avatar_bytes: BytesIO = None
            # https://docs.discord.com/developers/resources/guild#modify-current-member
            # if banner == None:
            #     if interaction.guild.banner:
            #         banner_bytes = BytesIO(await interaction.guild.banner.read())
            #     else:
            #         banner_bytes = None
            # else:
            #     banner_bytes = BytesIO(await banner.read())
            if avatar == None:
                if interaction.guild.icon:
                    avatar_bytes = BytesIO(await interaction.guild.icon.read())
                else:
                    avatar_bytes = None
            else:
                avatar_bytes = BytesIO(await avatar.read())
            
            params = {
                "nick": name if name else interaction.guild.name
            }
            # if banner_bytes:
            #     params["banner"] = bytesio_to_base64(banner_bytes)
            if avatar_bytes:
                params["avatar"] = bytesio_to_base64(avatar_bytes)
            if bio:
                params["bio"] = bio
            res = await interaction.client.http.request(Route("PATCH", "/guilds/{guild_id}/members/@me", guild_id=interaction.guild.id), json=params)
            print(json.dumps(res, indent=4,ensure_ascii=False))
            # {"、バナー" if banner_bytes else ""}
            # {f"\nbanner : https://cdn.discordapp.com/guilds/{interaction.guild.id}/users/{self.bot.user.id}/banners/{res["banner"]}" if banner_bytes else ""}
            await interaction.followup.send(
                embed=discord.Embed(
                    title="データを更新",
                    description=f"""\
Botの名前{"、アイコン" if avatar_bytes else ""}{"、プロフィール" if bio else ""}を変更しました。

Name : `{res["nick"]}`{f"\navatar : https://cdn.discordapp.com/guilds/{interaction.guild.id}/users/{self.bot.user.id}/avatars/{res["avatar"]}" if avatar_bytes else ""}{f"\nBio : ```\n{res['bio']}\n```" if res['bio'] else ""}""",
                    colour=discord.Colour.green()
                )
            )
        except HTTPException as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="データの更新に失敗しました。",
                    description=f"""\
                    Status Code: `{e.status}`
                    Message: `{e.text}`
                    """,
                    colour=discord.Colour.red()
                )
            )
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="プログラムエラー",
                    description=f"""\
                    エラーが出ました
                    ```
                    {e}
                    ```
                    """,
                    colour=discord.Colour.red()
                )
            )


async def setup(bot):
    await bot.add_cog(ChangeCog(bot))
