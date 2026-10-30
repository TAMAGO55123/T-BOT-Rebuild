from os import getenv, listdir
from os.path import isdir, join, dirname
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.app_commands import default_permissions
from discord import app_commands
from func.dc import Bot
from func.log import get_log, stream_handler
from asyncio import create_task, run
load_dotenv()

async def main(bot: Bot):
    log = get_log("Main")
    @bot.event
    async def on_ready():
        log.info(f"{bot.user.name}としてログインしました")
    
    @bot.event
    async def setup_hook():
        try:
            log.info("Cogを読み込んでいます...")
            for cog in listdir("cogs"):
                if cog.endswith(".py"):
                    try:
                        cog = f"cogs.{cog[:-3]}"
                        await bot.load_extension(cog)
                    except commands.errors.ExtensionAlreadyLoaded:
                        log.error(f"{cog}はすでに読み込まれています。")
                        continue
                    except commands.errors.ExtensionNotFound:
                        log.error(f"{cog}というCogは存在しません。")
                        continue
                    except commands.errors.NoEntryPointError:
                        log.error(f"{cog}にsetup_hook関数が存在しません")
                        continue
                    except commands.errors.ExtensionFailed as e:
                        log.error(f"{cog}内でエラーが発生しました。\n{e}")
                        continue
            
            synced = await bot.tree.sync()
            log.info(f"{len(synced)}個のコマンドを同期しました。")
        except Exception as e:
            log.error(f"コマンドの同期中にエラーが発生しました。")
    
    class SendEmbedModal(discord.ui.Modal):
        def __init__(self, channel:discord.TextChannel, message:str):
            super().__init__(
                title="フォーム",
                timeout=None,
            )

            self.messages = discord.ui.TextInput(
                label="カラーコードを送信してください(例:5865f2)",
                style=discord.TextStyle.short,
                max_length=6,
                required=False,
            )
            self.add_item(self.messages)

            self.channel = channel
            self.message = message

        async def on_submit(self, interaction:discord.Interaction):
            if self.messages.value:
                a = int(f"0x{self.messages.value}", 16)
            else:
                a = None
            await self.channel.send(embed=discord.Embed(description=self.message, color=a))
            await interaction.response.send_message("sended.",ephemeral=True)

    @bot.tree.context_menu(name="メッセージを再送信")
    @default_permissions(administrator=True)
    async def message_re_send(interaction:discord.Interaction, message:discord.Message):
        await message.channel.send(content=message.content, embeds=message.embeds)
        await interaction.response.send_message(content="sended.",ephemeral=True)

    @bot.tree.context_menu(name="メッセージを埋め込みに変換")
    @default_permissions(administrator=True)
    async def message_send_embed(interaction:discord.Interaction, message:discord.Message):
        modal = SendEmbedModal(channel=message.channel, message=message.content)
        await interaction.response.send_modal(modal)
    
    @bot.tree.context_menu(name="埋め込みをメッセージに変換")
    @default_permissions(administrator=True)
    async def embed_send_message(interaction:discord.Interaction, message:discord.Message):
        a = ""
        for i in message.embeds:
            a = a + i.description
        await message.channel.send(content=a)
        await interaction.response.send_message("sended.", ephemeral=True)

    class SendEditModal(discord.ui.Modal):
        def __init__(self, message:discord.Message):
            super().__init__(
                title="編集するメッセージを入力",
                timeout=None
            )
            if len(message.embeds) == 0:
                embed = False
            else:
                embed = True
            self.message = discord.ui.Label(
                text="メッセージ",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.paragraph,
                    required=True,
                    max_length=4000 if embed else 2000,
                    default=message.embeds[0].description if embed else message.content
                )
            )
            self.add_item(self.message)
            self.embed = embed
            self.smessage = message
        
        async def on_submit(self, interaction:discord.Interaction):
            mes:discord.Message = None
            if self.embed:
                mes = await self.smessage.edit(
                    embed=discord.Embed(
                        description=self.message.component.value
                    )
                )
            else:
                mes = await self.smessage.edit(
                    content=self.message.component.value
                )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="編集しました。",
                    description=f"メッセージ : https://discord.com/channels/{mes.guild.id}/{mes.channel.id}/{mes.id}"
                ),
                ephemeral=True
            )
    @bot.tree.context_menu(name="メッセージを編集")
    @default_permissions(administrator=True)
    async def edit_message(interaction:discord.Interaction, message:discord.Message):
        if message.author.id != bot.user.id:
            await interaction.response.send_message("このBotで送信されたメッセージではありません。", ephemeral=True)
            return
        await interaction.response.send_modal(SendEditModal(message))

    @bot.tree.context_menu(name="スレッドでメッセージをピン止めする")
    @app_commands.guilds(1541248982712328287)
    @app_commands.guild_only()
    async def supiki_pin(interaction: discord.Interaction, message: discord.Message):
        if isinstance(message.channel, discord.Thread):
            if message.channel.owner.id == interaction.user.id:
                await message.pin(reason="スレ主ピン")
                await interaction.response.send_message(content="ピン止めしました。", ephemeral=True)
            elif interaction.user.guild_permissions.pin_messages:
                await message.pin(reason="権限持ちピン")
                await interaction.response.send_message(content="ピン止めしました。", ephemeral=True)
            else:
                await interaction.response.send_message(content="スレ主または権限が無いので使用できません。", ephemeral=True)
        else:
            await interaction.response.send_message(content="ここはスレッドではないです。", ephemeral=True)

    
    await bot.start(getenv("TOKEN"))

if __name__ == "__main__":
    intents = discord.Intents.all()
    bot = Bot(command_prefix="t!", intents=intents, config_path="database/config.json")
    discord.utils.setup_logging(handler=stream_handler)
    run(main(bot))
