import discord
from discord.ext import commands
from discord import ui, app_commands, Interaction, Embed
import os
import json
from datetime import datetime, timezone

class SupportResolveView(ui.View):
    def __init__(self, user):
        super().__init__(timeout=600)
        self.user = user

    @ui.button(label="Mark as Resolved", style=discord.ButtonStyle.success)
    async def resolve(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Support ticket marked as resolved.", ephemeral=True)
        try:
            await self.user.send("Your support ticket has been marked as resolved by the server owner.")
        except Exception:
            pass
        self.stop()

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # 1. Ignore @everyone and @here
        if message.mention_everyone:
            return

        # 2. Ignore replies (messages with a reference)
        if message.reference is not None:
            return

        # 3. Ignore role mentions (roles the bot has)
        bot_roles = {role.id for role in message.guild.me.roles}
        mentioned_roles = {role.id for role in message.role_mentions}
        if bot_roles & mentioned_roles:
            return

        # 4. Only trigger if the bot is directly mentioned (not via role, not everyone/here)
        if self.bot.user in message.mentions:
            # Remove the mention from the content
            mention_str = message.clean_content.split()[0]
            reason = message.clean_content[len(mention_str):].strip()
            if reason:
                owner = message.guild.owner
                embed = discord.Embed(
                    title="New Support Ticket",
                    description=f"From: {message.author.mention}\nReason: {reason}",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                view = SupportResolveView(message.author)
                try:
                    await owner.send(embed=embed, view=view)
                except Exception:
                    pass
                try:
                    await message.author.send("Your support ticket has been sent to the server owner.")
                except Exception:
                    pass

                # --- LOG THE TICKET ---
                log_dir = "data"
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"support_tickets_{message.guild.id}.json")
                ticket = {
                    "user_id": str(message.author.id),
                    "username": str(message.author),
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                # Read, append, and write
                tickets = []
                if os.path.exists(log_file):
                    try:
                        with open(log_file, "r") as f:
                            tickets = json.load(f)
                    except Exception:
                        tickets = []
                tickets.append(ticket)
                with open(log_file, "w") as f:
                    json.dump(tickets, f, indent=2)

            else:
                await message.channel.send(
                    f"{message.author.mention}, please provide a reason after mentioning the bot.",
                    delete_after=10
                )

    @app_commands.command(name="support-logs", description="View recent support tickets for this server.")
    @app_commands.describe(limit="Number of tickets to show (max 20)")
    async def support_logs(self, interaction: Interaction, limit: int = 10):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return

        log_file = os.path.join("data", f"support_tickets_{interaction.guild.id}.json")
        if not os.path.exists(log_file):
            await interaction.response.send_message("No support tickets found for this server.", ephemeral=True)
            return

        with open(log_file, "r") as f:
            tickets = json.load(f)

        limit = max(1, min(limit, 20))
        tickets = tickets[-limit:]

        embed = Embed(
            title=f"Last {len(tickets)} Support Tickets",
            color=discord.Color.orange()
        )
        for t in tickets:
            user = t.get("username", "Unknown")
            reason = t.get("reason", "No reason provided")
            ts = t.get("timestamp", "Unknown")
            embed.add_field(
                name=f"{user} at {ts}",
                value=reason,
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Support(bot))