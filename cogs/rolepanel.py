import discord
from discord.ext import commands
from discord import app_commands, ButtonStyle
from func.dc import Bot
from func.log import get_log
import json
from func.file import File
from func.tools import list_all, Mention_False
import asyncio
from func.dc import Bot

class RoleButton(discord.ui.Button):
    def __init__(self, *, role:discord.Role, style: discord.ButtonStyle = ButtonStyle.secondary, label: str | None = None, disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | discord.Emoji | discord.PartialEmoji | None = None, row: int | None = None, sku_id: int | None = None, id: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row, sku_id=sku_id, id=id)
        self.role = role
    async def callback(self, interaction: discord.Interaction):
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            await interaction.response.send_message(
                f"<@&{self.role.id}>を削除しました。",
                ephemeral=True,
                allowed_mentions=Mention_False
            )
        else:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(
                f"<@&{self.role.id}>を付与しました。",
                ephemeral=True,
                allowed_mentions=Mention_False
            )

class NextStepView(discord.ui.View):
    def __init__(self, modal_factory):
        super().__init__(timeout=300)
        self.modal_factory = modal_factory

    @discord.ui.button(label="次へ", style=discord.ButtonStyle.primary)
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.modal_factory())
        self.stop()

class MultiRolePanelView(discord.ui.LayoutView):
    def __init__(self, roles: list[discord.Role], message:int, description:dict[int, str], title:str):
        super().__init__(timeout=None)
        self.roles = roles
        self.container = discord.ui.Container()
        self.add_item(self.container)
        self.des = description
        self.title = title
        titleText = discord.ui.TextDisplay(f"## {title}")
        self.container.add_item(titleText)

        for role in roles:
            button = RoleButton(
                role=role,
                style=discord.ButtonStyle.secondary,
                label="取得",
                custom_id=f"{role.guild.id}_{message}_{role.id}"
            )
            section = discord.ui.Section(
                discord.ui.TextDisplay(
                    f'<@&{role.id}>\n{"\n".join([f"-# {i}" for i in (self.des[role.id] if role.id in self.des else "").splitlines()])}'
                ),
                accessory=button
            )
            self.container.add_item(section)

class RoleTitleModal(discord.ui.Modal):
    def __init__(self, roles:list[discord.Role], bot:Bot, file:File):
        super().__init__(title="情報を入力", timeout=None)
        self.roles = roles
        self.bot = bot
        self.file = file
        self._title = discord.ui.Label(
            text="タイトル",
            component=discord.ui.TextInput(
                style=discord.TextStyle.short,
                placeholder="ロールパネル",
                required=False
            )
        )
        self.add_item(self._title)
    async def on_submit(self, interaction:discord.Interaction):
        title = self._title.component.value if self._title.component.value != "" else "ロールパネル"
        await interaction.response.send_message(
            "タイトルを受け付けました。次へ進んでください。",
            ephemeral=True,
            view=NextStepView(lambda: RoleDescriptionModal1(
                roles=self.roles,
                bot=self.bot,
                file=self.file,
                title=title
            ))
        )

class RoleDescriptionModal1(discord.ui.Modal):
    def __init__(self, roles:list[discord.Role], bot:Bot, file:File, title:str):
        super().__init__(title="情報を入力", timeout=None)
        self.roles = roles
        self.bot = bot
        self.file = file
        self.descriptions:dict[int, str] = []
        self.des_text:dict[int, discord.ui.Label] = {}
        self.title = title
        r = roles[:5]
        for role in r:
            des = discord.ui.Label(
                text=f"ロール\"{role.name}\"の説明を入力",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.paragraph,
                    required=False
                )
            )
            self.add_item(des)
            self.des_text.update({role.id: des})

    async def on_submit(self, interaction:discord.Interaction):
        des:dict[int, str] = {}
        for i in self.des_text:
            des[i] = self.des_text[i].component.value
        if len(self.roles) > 5:
            modal = RoleDescriptionModal2(
                roles=self.roles,
                bot=self.bot,
                file=self.file,
                title=self.title,
                des=des
            )
            await interaction.response.send_message(
                "前半の説明を受け付けました。次へ進んでください。",
                ephemeral=True,
                view=NextStepView(lambda: modal)
            )
        else:
            await create_role_panel(
                interaction=interaction,
                bot=self.bot,
                file=self.file,
                _title=self.title,
                roles=self.roles,
                des=des
            )

class RoleDescriptionModal2(discord.ui.Modal):
    def __init__(self, roles:list[discord.Role], bot:Bot, file:File, title:str, des:dict[int, str]):
        super().__init__(title="情報を入力", timeout=None)
        self.roles = roles
        self.bot = bot
        self.file = file
        self.descriptions:dict[int, str] = []
        self.des_text:dict[int, discord.ui.Label] = {}
        self.des = des
        self.panel_title = title
        r = roles[5:10]
        for role in r:
            des = discord.ui.Label(
                text=f"ロール\"{role.name}\"の説明を入力",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.paragraph,
                    required=False
                )
            )
            self.add_item(des)
            self.des_text.update({role.id: des})

    async def on_submit(self, interaction:discord.Interaction):
        for i in self.des_text:
            self.des[i] = self.des_text[i].component.value

        await create_role_panel(
            interaction=interaction,
            bot=self.bot,
            file=self.file,
            _title=self.panel_title,
            roles=self.roles,
            des=self.des
        )

async def create_role_panel(interaction:discord.Interaction, bot:Bot, file:File, _title:str, roles:list[discord.Role], des:dict[int, str]):
    await interaction.response.send_message("待機...(うまくいかない場合は再実行してください)", ephemeral=True)
    mes = await interaction.channel.send(
        "作成待機中...",
        allowed_mentions=Mention_False
    )
    title = _title if _title != "" else "ロールパネル"
    view = MultiRolePanelView(
        roles,
        mes.id,
        des,
        title
    )
    await mes.edit(content=None, view=view, allowed_mentions=Mention_False)
    bot.add_view(view)
    file.set(
        f"{interaction.guild.id}_{mes.id}",
        {
            "roles": [i.id for i in roles],
            "title": title,
            "description": des
        }
    )
    await interaction.edit_original_response(content="作成しました。")


class RoleCog(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.log = get_log(self.__class__.__name__)
        self.file:File = None
    @commands.Cog.listener()
    async def on_ready(self):
        self.log.info(f"{self.__class__.__name__}が読み込まれました！")
        self.file = File("database/role.json")
        tasks = []
        f_d = self.file.get_all()
        for gm_id in f_d:
            datas = f_d[gm_id]
            role_ids = datas["roles"]
            title = datas["title"]
            description = datas["description"]
            guild_id, message_id = tuple(gm_id.split("_"))
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                roles = [guild.get_role(role_id) for role_id in role_ids if guild.get_role(role_id)]
                if roles:
                    view = MultiRolePanelView(
                        roles,
                        message_id,
                        description,
                        title
                    )
                    self.bot.add_view(view)
                    print(f"ビューを再登録しました: {[role.name for role in roles]} (Guild ID: {guild_id}, Message ID: {message_id})")
                    tasks.append(asyncio.create_task(asyncio.sleep(0)))
        if tasks:
            await asyncio.gather(*tasks)
    
    @app_commands.command(name="rolepanel", description="ロールパネルを作成します(最大10個)")
    @app_commands.default_permissions(manage_roles=True, manage_guild=True)
    @app_commands.describe(
        role1="ロール1",
        role2="ロール2",
        role3="ロール3",
        role4="ロール4",
        role5="ロール5",
        role6="ロール6",
        role7="ロール7",
        role8="ロール8",
        role9="ロール9",
        role10="ロール10"
    )
    async def rolepanel(
        self,
        interaction:discord.Interaction,
        role1:discord.Role,
        role2:discord.Role = None,
        role3:discord.Role = None,
        role4:discord.Role = None,
        role5:discord.Role = None,
        role6:discord.Role = None,
        role7:discord.Role = None,
        role8:discord.Role = None,
        role9:discord.Role = None,
        role10:discord.Role = None,
        ):
        roles:list[discord.Role] = list_all(
            role1,
            role2,
            role3,
            role4,
            role5,
            role6,
            role7,
            role8,
            role9,
            role10
        )
        await interaction.response.send_modal(
            RoleTitleModal(
                roles=roles,
                bot=self.bot,
                file=self.file
            )
        )

async def setup(bot):
    await bot.add_cog(RoleCog(bot))
