import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.utils import MISSING
from func.dc import Bot
from func.log import get_log
from discord.http import Route
import aiohttp
from io import BytesIO
from func.tagimage import create_tag_image
from func import lang
import json

class ServerTagEndView(ui.View):
    def __init__(self, bot:Bot, tag_name:str, tag_invite:discord.Invite, tag_lang:str, tag_category:int):
        super().__init__(timeout=None)
        self.bot: Bot = bot
        self.tag_name = tag_name
        self.tag_invite = tag_invite
        self.tag_lang = tag_lang
        self.tag_category = tag_category
        

    @ui.button(label="OK", style=discord.ButtonStyle.primary)
    async def ok_button(self, interaction:discord.Interaction):
        check_channel_id = self.bot.config.get("check_channel_id", 0)
        if check_channel_id != 0:
            await interaction.response.defer(ephemeral=True)
            check_channel = self.bot.get_channel(check_channel_id)
            match self.tag_category:
                case 0:
                    cate = "標準"
                case 1:
                    cate = "参加申請"
                case _:
                    cate = "無効な値"
            data_json = {
                "name": self.tag_name,
                "invite": self.tag_invite.url,
                "lang": self.tag_lang,
                "at_id": interaction.user.id,
                "kind": self.tag_category
            }
            check_embeds = [
                discord.Embed(
                    title=f"タグの申請(From Other Server)",
                    description=f"タグ名:`{self.tag_name}\n招待リンク:`{self.tag_invite.url}`\n主言語:`{self.tag_lang}`\nアクセス範囲:`{cate}`\n申請者:`{interaction.user.name}`<@{interaction.user.id}>\n※Botによる自動タグ取得による判別であるため、危険サーバーかどうかの判別をお願いします。",
                    colour=discord.Colour.green()
                ),
                discord.Embed(
                    description=json.dumps(data_json, ensure_ascii=False,indent=None)
                )
            ]
            check_channel.send(
                content=f"Tag-Info\n{self.tag_invite.url}\n<@&{self.bot.config.get("tag_checkrole_id", 0)}>",
                embeds=check_embeds
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="申請を行いました!",
                    description=f"現在通知の実装は行われていません。\n[Tags Collection]({self.bot.config.get("tags_collection", "https://example.com")})からタグ通知ロールを取得すると通知されます。",
                    colour=discord.Colour.green()
                ),
                ephemeral=True
            )



class ServerTagModal(ui.Modal):
    def __init__(self, bot:Bot, tag_name: str, image: BytesIO, invite: discord.Invite):
        super().__init__(title="手動設定", timeout=None)
        self.bot:Bot = bot
        self.lang = ui.Label(
            text="主言語を選択してください",
            component=ui.Select(
                options=lang.ModalSelectOptions,
                required=True,
                min_values=1,
                max_values=1
            )
        )
        self.category = ui.Label(
            text="カテゴリーの選択",
            description="サーバーの招待区分を設定してください。\n参加申請が必要かつ、custom_inviteを指定しない場合は「参加申請」を選んでください。",
            component=ui.Select(
                options=[
                    discord.SelectOption(
                        label="標準",
                        value="0"
                    ),
                    discord.SelectOption(
                        label="参加申請",
                        value="1"
                    )
                ],
                required=True,
                min_values=1,
                max_values=1
            )
        )
        self.add_item(self.lang)
        self.add_item(self.category)
        self.tag_name: str = tag_name
        self.image: BytesIO = image
        self.invite: discord.Invite = invite
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="確認",
            description="以下の内容で申請を行います。よろしいですか？",
        )
        embed.add_field(
            name="タグ名",
            value=self.tag_name
        )
        embed.add_field(
            name="招待リンク",
            value=self.invite.url
        )
        embed.add_field(
            name="主言語",
            value=self.lang.component.values[0]
        )
        embed.add_field(
            name="カテゴリー",
            value=self.category.component.values[0]
        )
        file = discord.File(fp=self.image, filename="badge.png")
        embed.set_image(url=file.uri)
        
        await interaction.response.send_message(
            embed=embed,
            file=file,
            ephemeral=True
        )

class ServerTagCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")

    class Tag_Group(app_commands.Group):
        pass

    tag = Tag_Group(name="tag", description="サーバータグに関わるコマンドです。")

    @tag.command(name="register", description="Tags Collectionに掲載します。")
    async def register(self, interaction:discord.Interaction, channel: discord.abc.GuildChannel = None, custom_invite: str = None):
        c = channel if channel else interaction.channel
        if "GUILD_TAGS" not in interaction.guild.features:
            res = await interaction.client.http.request(Route("GET", "/guilds/{guild_id}/premium/subscriptions", guild_id=interaction.guild.id))
            used_boost = sum(
                r["tenant_metadata"]["guild_monetization"]["powerup"]["boost_price"]
                for r in res
                if not r["deleted"]
            )
            non_used_boost = interaction.guild.premium_subscription_count - used_boost
            if non_used_boost >= 3:
                str_boost = f"サーバータグは有効化可能です!設定から有効化して再度実行してください。(使用可能ブースト数:{non_used_boost} / {interaction.guild.premium_subscription_count})"
            else:
                str_boost = f"残り{3-non_used_boost}個のブーストでサーバータグを有効化できます。"
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラー",
                    description=f"このサーバーではサーバータグが有効化されていません。\n{str_boost}",
                    colour=discord.Colour.red()
                )
            )
        if custom_invite:
            try:
                invite = interaction.client.fetch_invite(url=custom_invite)
            except (discord.errors.NotFound, discord.errors.HTTPException):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="エラー",
                        description="指定されたカスタム招待リンクが間違っています。",
                        colour=discord.Colour.red()
                    ),
                    ephemeral=True
                )
                return
            res = await self.bot.http.request(Route("GET", "/invites/{invite_code}", invite_code=invite.code))
        else:
            if not c.permissions_for(interaction.guild.me).create_instant_invite:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="エラー",
                        description=f"指定されたチャンネル[ <#{c.id}> ]に以下の権限がないため、この操作を実行できません。\n```\n招待を作成\n```",
                        colour=discord.Colour.red()
                    ),
                    ephemeral=True
                )
                return
            invite = await c.create_invite(reason="サーバータグを取得するための招待")
            try:
                res = await self.bot.http.request(Route("GET", "/invites/{invite_code}", invite_code=invite.code))
            except discord.errors.NotFound:
                pass
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"https://cdn.discordapp.com/guild-tag-badges/{res["guild_id"]}/{res["profile"]["badge_hash"]}.png") as r:
                tag_icon = BytesIO(await r.read())
        image = await create_tag_image(icon=tag_icon, tag_name=res["profile"]["tag"])
        modal = ServerTagModal(bot=self.bot, tag_name=res["profile"]["tag"], image=image, invite=invite)
        
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(ServerTagCog(bot))
