import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui
from discord.utils import get

class VerifyButton(ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

    @ui.button(label="Verify", style=discord.ButtonStyle.success)
    async def verify(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "Please type your reason for joining this server:", ephemeral=True)
        def check(m):
            return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=120)
        except Exception:
            await interaction.followup.send("Verification timed out.", ephemeral=True)
            return

        guild = self.bot.get_guild(self.guild_id)
        owner = guild.owner
        embed = discord.Embed(
            title="Verification Request",
            description=f"User: {interaction.user.mention}\nReason: {msg.content}",
            color=discord.Color.blue()
        )
        view = OwnerVerifyView(self.bot, guild.id, interaction.user.id)
        await owner.send(embed=embed, view=view)
        await interaction.followup.send("Your reason has been sent to the server owner for approval.", ephemeral=True)

class OwnerVerifyView(ui.View):
    def __init__(self, bot, guild_id, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id

    @ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve(self, interaction: Interaction, button: ui.Button):
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        role = get(guild.roles, name="Member")
        if not role:
            role = await guild.create_role(name="Member")
        if member:
            await member.add_roles(role, reason="Verification approved")
            await member.send(f"You have been verified in **{guild.name}**! Welcome!")
            await interaction.response.send_message("User approved and verified.", ephemeral=True)
        else:
            await interaction.response.send_message("User not found in guild.", ephemeral=True)
        self.stop()

    @ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: Interaction, button: ui.Button):
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        if member:
            await member.send(f"Your verification in **{guild.name}** was denied. You have been removed from the server.")
            await member.kick(reason="Verification denied")
            await interaction.response.send_message("User denied and kicked.", ephemeral=True)
        else:
            await interaction.response.send_message("User not found in guild.", ephemeral=True)
        self.stop()

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            view = VerifyButton(self.bot, member.guild.id)
            await member.send(
                f"Welcome to **{member.guild.name}**!\nPlease verify yourself to continue.",
                view=view
            )
        except Exception:
            pass  # User has DMs closed or other error

async def setup(bot):
    await bot.add_cog(Verification(bot))