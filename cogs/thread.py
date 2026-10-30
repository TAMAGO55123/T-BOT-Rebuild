import discord
from discord.ext import commands
from discord import app_commands
from func.dc import Bot
from func.log import get_log
import asyncio
from func.file import File

class ThreadCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
        self.file: File = File("database/thread.json")
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")

    class Thread_Group(app_commands.Group):
        pass
    
    thread = Thread_Group(name="thread", description="スレッドに関するコマンドを追加します。")

    @thread.command(name="enable", description="スレッド自動招待機能を有効化します。")
    @app_commands.default_permissions(manage_threads=True)
    async def thread_enable(self, interaction:discord.Interaction, role: discord.Role):
        if self.file.get(f"{interaction.guild.id}"):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="すでに有効化されています。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        self.file.set(
            f"{interaction.guild.id}",
            {
                "role": role.id,
                "disable_channels": []
            }
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="スレッド自動招待機能を有効化しました。",
                description="有効化が完了しました。",
                colour=discord.Colour.green()
            ),
            ephemeral=True
        )

    @thread.command(name="disable", description="スレッド自動招待機能を無効化します。")
    @app_commands.default_permissions(manage_threads=True)
    async def thread_disable(self, interaction:discord.Interaction):
        if not self.file.get(f"{interaction.guild.id}"):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="すでに無効化されています。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
        self.file.delete(f"{interaction.guild.id}")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="スレッド自動招待機能を無効化しました。",
                description="無効化が完了しました。",
                colour=discord.Colour.green()
            ),
            ephemeral=True
        )

    class Thread_Blacklist_Group(app_commands.Group):
        pass

    thread_blacklist = Thread_Blacklist_Group(name="blacklist", description="スレッド自動招待機能のブラックリストを設定します。",  parent=thread)

    @thread_blacklist.command(name="add", description="ブラックリストを追加します。")
    @app_commands.default_permissions(manage_threads=True)
    async def thread_blacklist_add(self, interaction:discord.Interaction, channel: discord.abc.GuildChannel):
        if not self.file.get(f"{interaction.guild.id}"):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="有効化されていません。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        f:dict = self.file.get(f"{interaction.guild.id}")
        if channel.id in f.get("disable_channels", []):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="すでに追加されています。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        f.setdefault("disable_channels", []).append(channel.id)
        self.file.set(f"{interaction.guild.id}", f)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ブラックリストに追加しました。",
                description="正常に追加しました。",
                colour=discord.Colour.green()
            )
        )
    @thread_blacklist.command(name="remove", description="ブラックリストから削除します。")
    @app_commands.default_permissions(manage_threads=True)
    async def thread_blacklist_remove(self, interaction:discord.Interaction, channel: discord.abc.GuildChannel):
        if not self.file.get(f"{interaction.guild.id}"):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="有効化されていません。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        f:dict = self.file.get(f"{interaction.guild.id}")
        if channel.id not in f.get("disable_channels", []):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="ブラックリストに登録されていないチャンネルです。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        try:
            f.get("disable_channels", []).remove(channel.id)
        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description="ブラックリストに登録されていないチャンネルです。",
                    colour=discord.Colour.red()
                ),
                ephemeral=True
            )
            return
        self.file.set(f"{interaction.guild.id}", f)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ブラックリストから削除しました。",
                description="正常に削除しました。",
                colour=discord.Colour.green()
            )
        )

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if f"{thread.guild.id}" in self.file.get_all():
            f:dict = self.file.get(f"{thread.guild.id}")
            disable_id = set(f.get("disable_channels", []))
            channel_ids = {thread.id}
            parent = thread.parent
            while parent:
                channel_ids.add(parent.id)
                parent = parent.category
            if channel_ids & disable_id:
                return
            mes = await thread.send("スレッド自動招待機能")
            await asyncio.sleep(1)
            await mes.edit(content=f"<@&{f.get("role", 0)}")
            await asyncio.sleep(0.5)
            await mes.delete()

    @thread.command(name="invite", description="新しいユーザーをスレッドに参加させます。(スレ主または権限持ちのみ使用可能)")
    async def re_invite(self, interaction:discord.Interaction):
        if isinstance(interaction.channel, discord.Thread):
            if f"{interaction.guild.id}" in self.file.get_all():
                if interaction.channel.owner.id == interaction.user.id or interaction.channel.permissions_for(interaction.user):
                    f:dict = self.file.get(f"{interaction.guild.id}")
                    await interaction.response.defer(ephemeral=True)
                    mes = await interaction.channel.send("スレッド自動招待機能")
                    await asyncio.sleep(1)
                    await mes.edit(content=f"<@&{f.get("role", 0)}")
                    await asyncio.sleep(0.5)
                    await mes.delete()
                    
                    await interaction.followup.send(
                        content="招待しました。",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(content="スレ主または権限が無いので使用できません。", ephemeral=True)
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="エラー",
                        description="このサーバーではこの機能は有効化されていません。",
                        colour=discord.Colour.red()
                    ),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(content="ここはスレッドではないです。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ThreadCog(bot))
