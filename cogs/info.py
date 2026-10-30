import discord
from discord.ext import commands
from discord import app_commands
from func.dc import Bot
from func.log import get_log

class InfoCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")

    class Member(app_commands.Group):
        pass
    user = Member(name="member", description="メンバーに関するコマンド")

    @user.command(name="banner", description="ユーザーのバナーを取得します")
    async def banner(self, interaction:discord.Interaction, user:discord.Member = None):
        u = user if user else interaction.user
        b = u.display_banner
        if b:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{u.display_name}のバナー"
                ).set_image(url=b.url)
            )
        else:
            await interaction.response.send_message(content=f"{u.display_name}のバナーはありません。")
async def setup(bot):
    await bot.add_cog(InfoCog(bot))
