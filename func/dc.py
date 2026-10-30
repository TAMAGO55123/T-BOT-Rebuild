from discord import app_commands
from discord.app_commands.tree import CommandTree
from discord.ext import commands
from discord.ext.commands.bot import _default
from discord.utils import MISSING
from func.file import File
class Bot(commands.Bot):
    def __init__(self, command_prefix, config_path: str, *, help_command = _default, tree_cls = app_commands.CommandTree, description = None, allowed_contexts = MISSING, allowed_installs = MISSING, intents, **options):
        super().__init__(command_prefix, help_command=help_command, tree_cls=tree_cls, description=description, allowed_contexts=allowed_contexts, allowed_installs=allowed_installs, intents=intents, **options)
        self.config: File = File(config_path)