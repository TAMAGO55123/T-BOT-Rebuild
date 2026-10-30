import discord

class BotAdminCheckFailure(discord.app_commands.CheckFailure):
    def __init__(self, message: str, *, user: discord.User):
        super().__init__(message)
        self.user = user