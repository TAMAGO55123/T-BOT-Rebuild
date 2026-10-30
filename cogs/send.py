import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal
from func.dc import Bot
from func.log import get_log

class SendModal(Modal):
    def __init__(self, embed:bool):
        super().__init__(
            title="送信するメッセージを入力",
            timeout=None
        )
        self.message = discord.ui.Label(
            text="メッセージ",
            component=discord.ui.TextInput(
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=4000 if embed else 2000
            )
        )
        self.add_item(self.message)
        self.embed = embed
    
    async def on_submit(self, interaction:discord.Interaction):
        mes:discord.Message = None
        if self.embed:
            mes = await interaction.channel.send(
                embed=discord.Embed(
                    description=self.message.component.value
                )
            )
        else:
            mes = await interaction.channel.send(
                self.message.component.value
            )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="送信しました。",
                description=f"メッセージ : https://discord.com/channels/{mes.guild.id}/{mes.channel.id}/{mes.id}"
            ),
            ephemeral=True
        )

class SendCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")
    
    @app_commands.command(name="send", description="メッセージを送信します。")
    @app_commands.describe(
        embed = "埋め込みで送信するかを選択できます。"
    )
    @app_commands.default_permissions(administrator=True)
    async def send(self, interaction:discord.Interaction, embed:bool = False):
        await interaction.response.send_modal(SendModal(embed))

async def setup(bot):
    await bot.add_cog(SendCog(bot))
