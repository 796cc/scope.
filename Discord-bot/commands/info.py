import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all bot commands grouped by category.")
    async def help(self, interaction: Interaction):
        embed = Embed(
            title="Bot Commands Help",
            description="Here are all available slash commands grouped by category:",
            color=discord.Color.blurple()
        )

        # Group commands by cog/category
        categories = {}
        for cmd in self.bot.tree.get_commands():
            if cmd.parent is None:
                # Use the last part of the module name as the category
                category = (cmd.module or "Other").split('.')[-1].capitalize()
                categories.setdefault(category, []).append(cmd)

        for category, cmds in sorted(categories.items()):
            value = ""
            for cmd in cmds:
                desc = cmd.description or 'No description.'
                # Add notes for special commands
                if cmd.name == "say":
                    desc += " (Admins: 1/2.5min, Owner: unlimited)"
                if cmd.name == "automate":
                    desc += " (Admins only: schedule automated messages)"
                if cmd.name == "stop_automate":
                    desc += " (Admins only: stop automated messages)"
                value += f"/{cmd.name} — {desc}\n"
            embed.add_field(name=category, value=value, inline=False)

        embed.set_footer(text="Use /<command> to run a command.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))
