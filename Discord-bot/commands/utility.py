import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction
import asyncio
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.say_cooldowns = {}  # {guild_id: {user_id: last_used_timestamp}}
        self.automated_tasks = {}  # {(guild_id, channel_id): task}
        self.automate_data_dir = "data"
        # Load automations on startup
        self.bot.loop.create_task(self.load_automations())

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency"""
        api_latency = round((datetime.now().timestamp() - interaction.created_at.timestamp()) * 1000)
        websocket_ping = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="Pong! 🏓",
            color=discord.Color.blue()
        )
        embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="WebSocket Ping", value=f"{websocket_ping}ms", inline=True)
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="embed", description="Create a custom embed message")
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        color="Embed color (hex code without #)",
        channel="Channel to send the embed to"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def embed(self, interaction: discord.Interaction, title: str, description: str, color: str = None, channel: discord.TextChannel = None):
        """Create a custom embed"""
        await interaction.response.defer(ephemeral=True)
        
        if not channel:
            channel = interaction.channel
            
        try:
            # Parse color
            embed_color = discord.Color.blue()  # default
            if color:
                try:
                    embed_color = discord.Color(int(color, 16))
                except ValueError:
                    return await interaction.followup.send("Invalid color format. Use hex without # (e.g., 0099ff)", ephemeral=True)
                    
            embed = discord.Embed(
                title=title,
                description=description,
                color=embed_color
            )
            embed.set_footer(text=f"Created by {interaction.user}", icon_url=interaction.user.display_avatar.url)
            
            await channel.send(embed=embed)
            await interaction.followup.send(f"Embed sent to {channel.mention}", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in embed command: {e}")
            await interaction.followup.send("An error occurred while creating the embed.", ephemeral=True)
            
    @app_commands.command(name="sticky", description="Create a sticky message that stays at the bottom")
    @app_commands.describe(
        message="The message content",
        channel="Channel to send the sticky message to"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def sticky(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
        """Create a sticky message"""
        await interaction.response.defer(ephemeral=True)
        
        if not channel:
            channel = interaction.channel
            
        try:
            embed = discord.Embed(
                description=message,
                color=discord.Color.gold()
            )
            embed.set_footer(text="📌 Sticky Message")
            
            sent_message = await channel.send(embed=embed)
            
            # Store sticky message info (you might want to implement persistent storage)
            # For now, just pin the message
            try:
                await sent_message.pin()
            except discord.HTTPException:
                pass  # Channel might have too many pins
                
            await interaction.followup.send(f"Sticky message created in {channel.mention}", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in sticky command: {e}")
            await interaction.followup.send("An error occurred while creating the sticky message.", ephemeral=True)
            
    @app_commands.command(name="note", description="Manage user notes")
    @app_commands.describe(
        action="Action to perform",
        user="The user to manage notes for",
        note="Note content (for add action)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="clear", value="clear")
    ])
    @app_commands.default_permissions(kick_members=True)
    async def note(self, interaction: discord.Interaction, action: str, user: discord.Member, note: str = None):
        """Manage user notes"""
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id

        if action == "add":
            if not note:
                return await interaction.followup.send("Note content is required for add action.", ephemeral=True)
            await self.bot.notes_manager.add_note(guild_id, user.id, note, interaction.user.id)
            embed = discord.Embed(
                title="Note Added",
                description=f"Note added for {user.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Note", value=note, inline=False)
            embed.add_field(name="Added by", value=interaction.user.mention, inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif action == "list":
            notes = await self.bot.notes_manager.get_user_notes(guild_id, user.id)
            if not notes:
                return await interaction.followup.send(f"No notes found for {user.mention}.", ephemeral=True)
            embed = discord.Embed(
                title=f"Notes for {user}",
                color=discord.Color.blue()
            )
            for i, note_data in enumerate(notes[:10]):  # Limit to 10 notes
                timestamp = datetime.fromtimestamp(note_data['timestamp'] / 1000)
                admin = self.bot.get_user(int(note_data['adminId']))
                admin_name = admin.mention if admin else f"<@{note_data['adminId']}>"
                embed.add_field(
                    name=f"Note #{i+1}",
                    value=f"{note_data['note']}\n*Added by {admin_name} on {timestamp.strftime('%Y-%m-%d %H:%M')}*",
                    inline=False
                )
            if len(notes) > 10:
                embed.set_footer(text=f"Showing 10 of {len(notes)} notes")
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif action == "remove":
            if not note:
                return await interaction.followup.send("Note index is required for remove action.", ephemeral=True)
            try:
                index = int(note) - 1
                removed = await self.bot.notes_manager.remove_note(guild_id, user.id, index)
                if removed:
                    embed = discord.Embed(
                        title="Note Removed",
                        description=f"Note #{note} removed for {user.mention}",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("Invalid note index.", ephemeral=True)
            except ValueError:
                await interaction.followup.send("Invalid note index. Please provide a number.", ephemeral=True)

        elif action == "clear":
            await self.bot.notes_manager.clear_user_notes(guild_id, user.id)
            embed = discord.Embed(
                title="Notes Cleared",
                description=f"All notes cleared for {user.mention}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="addrole", description="Add a role to a member")
    @app_commands.describe(
        member="The member to add the role to",
        role="The role to add"
    )
    @app_commands.default_permissions(manage_roles=True)
    async def addrole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Add a role to a member"""
        await interaction.response.defer(ephemeral=True)
        
        # Permission checks
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.followup.send("You cannot assign this role due to role hierarchy.", ephemeral=True)
            
        if role >= interaction.guild.me.top_role:
            return await interaction.followup.send("I cannot assign this role due to role hierarchy.", ephemeral=True)
            
        if role in member.roles:
            return await interaction.followup.send(f"{member.mention} already has the {role.mention} role.", ephemeral=True)
            
        try:
            await member.add_roles(role, reason=f"Role added by {interaction.user}")
            
            embed = discord.Embed(
                title="Role Added",
                description=f"{role.mention} has been added to {member.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage roles.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in addrole command: {e}")
            await interaction.followup.send("An error occurred while adding the role.", ephemeral=True)
            
    @app_commands.command(name="removerole", description="Remove a role from a member")
    @app_commands.describe(
        member="The member to remove the role from",
        role="The role to remove"
    )
    @app_commands.default_permissions(manage_roles=True)
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Remove a role from a member"""
        await interaction.response.defer(ephemeral=True)
        
        # Permission checks
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.followup.send("You cannot remove this role due to role hierarchy.", ephemeral=True)
            
        if role >= interaction.guild.me.top_role:
            return await interaction.followup.send("I cannot remove this role due to role hierarchy.", ephemeral=True)
            
        if role not in member.roles:
            return await interaction.followup.send(f"{member.mention} doesn't have the {role.mention} role.", ephemeral=True)
            
        try:
            await member.remove_roles(role, reason=f"Role removed by {interaction.user}")
            
            embed = discord.Embed(
                title="Role Removed",
                description=f"{role.mention} has been removed from {member.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage roles.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in removerole command: {e}")
            await interaction.followup.send("An error occurred while removing the role.", ephemeral=True)
            
    @app_commands.command(name="say", description="Make the bot say something.")
    @app_commands.describe(message="The message for the bot to say")
    async def say(self, interaction: Interaction, message: str):
        user = interaction.user
        guild = interaction.guild
        now = discord.utils.utcnow().timestamp()
        is_owner = (guild is not None and user.id == guild.owner_id)
        is_admin = (guild is not None and user.guild_permissions.administrator)

        # Cooldown logic
        if not is_owner:
            last_used = self.say_cooldowns.get(guild.id, {}).get(user.id, 0)
            if now - last_used < 150 and is_admin:
                remaining = int(150 - (now - last_used))
                await interaction.response.send_message(
                    f"You can use this command again in {remaining} seconds.", ephemeral=True
                )
                return
            # Update cooldown
            self.say_cooldowns.setdefault(guild.id, {})[user.id] = now

        # Respond ephemerally and delete the invocation, then send the message as the bot
        await interaction.response.send_message("✅", ephemeral=True)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass  # Ignore if already deleted or not possible

        await interaction.channel.send(message)

    async def load_automations(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            file_path = os.path.join(self.automate_data_dir, f"automate_{guild.id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    actions = json.load(f)
                for action in actions:
                    channel_id = action["channel_id"]
                    message = action["message"]
                    seconds = action["interval"]
                    await self.start_automation(guild.id, channel_id, message, seconds)

    async def start_automation(self, guild_id, channel_id, message, seconds):
        key = (guild_id, channel_id)
        # Cancel existing task if present
        if key in self.automated_tasks:
            self.automated_tasks[key].cancel()

        async def send_message_task():
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(channel_id)
            while True:
                await channel.send(message)
                await asyncio.sleep(seconds)

        task = self.bot.loop.create_task(send_message_task())
        self.automated_tasks[key] = task

    def save_automation(self, guild_id, channel_id, message, seconds):
        os.makedirs(self.automate_data_dir, exist_ok=True)
        file_path = os.path.join(self.automate_data_dir, f"automate_{guild_id}.json")
        actions = []
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                actions = json.load(f)
        # Remove any existing automation for this channel
        actions = [a for a in actions if a["channel_id"] != channel_id]
        actions.append({
            "channel_id": channel_id,
            "message": message,
            "interval": seconds
        })
        with open(file_path, "w") as f:
            json.dump(actions, f, indent=2)

    def remove_automation(self, guild_id, channel_id):
        file_path = os.path.join(self.automate_data_dir, f"automate_{guild_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                actions = json.load(f)
            actions = [a for a in actions if a["channel_id"] != channel_id]
            with open(file_path, "w") as f:
                json.dump(actions, f, indent=2)

    @app_commands.command(name="automate", description="Automate a message at a set interval.")
    @app_commands.describe(
        message="The message to send",
        interval="Interval value (number)",
        unit="Interval unit (seconds, minutes, hours, days)"
    )
    @app_commands.choices(
        unit=[
            app_commands.Choice(name="seconds", value="seconds"),
            app_commands.Choice(name="minutes", value="minutes"),
            app_commands.Choice(name="hours", value="hours"),
            app_commands.Choice(name="days", value="days"),
        ]
    )
    async def automate(
        self,
        interaction: Interaction,
        message: str,
        interval: int,
        unit: app_commands.Choice[str]
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return

        multiplier = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }
        seconds = interval * multiplier[unit.value]
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id

        await self.start_automation(guild_id, channel_id, message, seconds)
        self.save_automation(guild_id, channel_id, message, seconds)

        await interaction.response.send_message(
            f"Automated message scheduled every {interval} {unit.value} in this channel.", ephemeral=True
        )

    @app_commands.command(name="stop_automate", description="Stop automated messages in this channel.")
    async def stop_automate(self, interaction: Interaction):
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        key = (guild_id, channel_id)
        if key in self.automated_tasks:
            self.automated_tasks[key].cancel()
            del self.automated_tasks[key]
            self.remove_automation(guild_id, channel_id)
            await interaction.response.send_message("Automated messages stopped for this channel.", ephemeral=True)
        else:
            await interaction.response.send_message("No automated messages are running in this channel.", ephemeral=True)

    @commands.command()
    @commands.cooldown(1, 1.5, commands.BucketType.user)
    async def mycommand(self, ctx):
        await ctx.send("This is a prefix command with anti-spam cooldown!")

async def setup(bot):
    await bot.add_cog(Utility(bot))
