import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick"
    )
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member from the server"""
        await interaction.response.defer(ephemeral=True)
        
        if member.id == interaction.guild.owner_id:
            await interaction.response.send_message("You cannot kick the server owner.", ephemeral=True)
            return
            
        # Permission checks
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.followup.send("You don't have permission to kick members.", ephemeral=True)
            
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.followup.send("You cannot kick this member due to role hierarchy.", ephemeral=True)
            
        if not interaction.guild.me.guild_permissions.kick_members:
            return await interaction.followup.send("I don't have permission to kick members.", ephemeral=True)
            
        try:
            # Send DM to user before kicking
            try:
                embed = discord.Embed(
                    title="You have been kicked",
                    description=f"You were kicked from **{interaction.guild.name}**",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
                
            await member.kick(reason=f"{reason} - By {interaction.user}")
            
            # Log the punishment
            log_entry = {
                "type": "kick",
                "userId": str(member.id),
                "username": str(member),
                "moderatorId": str(interaction.user.id),
                "moderatorName": str(interaction.user),
                "guildId": str(interaction.guild.id),
                "guildName": interaction.guild.name,
                "reason": reason,
                "timestamp": datetime.now().timestamp() * 1000
            }
            self.bot.db.add_punishment_log(log_entry)
            
            embed = discord.Embed(
                title="Member Kicked",
                description=f"**{member}** has been kicked from the server.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to kick this member.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await interaction.followup.send("An error occurred while trying to kick the member.", ephemeral=True)
            
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban",
        delete_messages="Delete messages from the last X days (0-7)"
    )
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_messages: int = 0):
        """Ban a member from the server"""
        await interaction.response.defer(ephemeral=True)
        
        if member.id == interaction.guild.owner_id:
            await interaction.response.send_message("You cannot ban the server owner.", ephemeral=True)
            return
            
        if delete_messages < 0 or delete_messages > 7:
            return await interaction.followup.send("Delete messages days must be between 0-7.", ephemeral=True)
            
        # Permission checks
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.followup.send("You don't have permission to ban members.", ephemeral=True)
            
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.followup.send("You cannot ban this member due to role hierarchy.", ephemeral=True)
            
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.followup.send("I don't have permission to ban members.", ephemeral=True)
            
        try:
            # Send DM to user before banning
            try:
                embed = discord.Embed(
                    title="You have been banned",
                    description=f"You were banned from **{interaction.guild.name}**",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
                
            await member.ban(reason=f"{reason} - By {interaction.user}", delete_message_days=delete_messages)
            
            # Log the punishment
            log_entry = {
                "type": "ban",
                "userId": str(member.id),
                "username": str(member),
                "moderatorId": str(interaction.user.id),
                "moderatorName": str(interaction.user),
                "guildId": str(interaction.guild.id),
                "guildName": interaction.guild.name,
                "reason": reason,
                "timestamp": datetime.now().timestamp() * 1000
            }
            self.bot.db.add_punishment_log(log_entry)
            
            embed = discord.Embed(
                title="Member Banned",
                description=f"**{member}** has been banned from the server.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Messages Deleted", value=f"{delete_messages} days", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to ban this member.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await interaction.followup.send("An error occurred while trying to ban the member.", ephemeral=True)
            
    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration in minutes",
        reason="Reason for the timeout"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        """Timeout a member"""
        await interaction.response.defer(ephemeral=True)
        
        if duration <= 0 or duration > 40320:  # Max 28 days
            return await interaction.followup.send("Duration must be between 1 and 40320 minutes (28 days).", ephemeral=True)
            
        # Permission checks
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.followup.send("You don't have permission to timeout members.", ephemeral=True)
            
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.followup.send("You cannot timeout this member due to role hierarchy.", ephemeral=True)
            
        try:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.edit(timed_out_until=timeout_until, reason=f"{reason} - By {interaction.user}")
            
            # Log the punishment
            log_entry = {
                "type": "timeout",
                "userId": str(member.id),
                "username": str(member),
                "moderatorId": str(interaction.user.id),
                "moderatorName": str(interaction.user),
                "guildId": str(interaction.guild.id),
                "guildName": interaction.guild.name,
                "reason": reason,
                "duration": duration,
                "timestamp": datetime.now().timestamp() * 1000
            }
            self.bot.db.add_punishment_log(log_entry)
            
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"**{member}** has been timed out for {duration} minutes.",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Until", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to timeout this member.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in timeout command: {e}")
            await interaction.followup.send("An error occurred while trying to timeout the member.", ephemeral=True)
            
    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(
        member="The member to remove timeout from",
        reason="Reason for removing timeout"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        await interaction.response.defer(ephemeral=True)
        
        if not member.is_timed_out():
            return await interaction.followup.send("This member is not timed out.", ephemeral=True)
            
        try:
            await member.timeout(None, reason=f"{reason} - By {interaction.user}")
            
            embed = discord.Embed(
                title="Timeout Removed",
                description=f"**{member}**'s timeout has been removed.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to remove timeout from this member.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in untimeout command: {e}")
            await interaction.followup.send("An error occurred while trying to remove timeout.", ephemeral=True)
            
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for the warning"
    )
    @app_commands.default_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn a member"""
        await interaction.response.defer(ephemeral=True)
        
        if member.id == interaction.guild.owner_id:
            if not interaction.response.is_done():
                await interaction.response.send_message("You cannot warn the server owner.", ephemeral=True)
            else:
                await interaction.followup.send("You cannot warn the server owner.", ephemeral=True)
            return
            
        try:
            # Send DM to user
            try:
                embed = discord.Embed(
                    title="You have been warned",
                    description=f"You received a warning in **{interaction.guild.name}**",
                    color=discord.Color.yellow()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
                
            # Log the punishment
            log_entry = {
                "type": "warn",
                "userId": str(member.id),
                "username": str(member),
                "moderatorId": str(interaction.user.id),
                "moderatorName": str(interaction.user),
                "guildId": str(interaction.guild.id),
                "guildName": interaction.guild.name,
                "reason": reason,
                "timestamp": datetime.now().timestamp() * 1000
            }
            await self.bot.logging_system.add_punishment_log(log_entry)
            
            embed = discord.Embed(
                title="Member Warned",
                description=f"**{member}** has been warned.",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            await interaction.followup.send("An error occurred while trying to warn the member.", ephemeral=True)
            
    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        member="Only delete messages from this member"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, member: discord.Member = None):
        """Delete multiple messages"""
        await interaction.response.defer(ephemeral=True)
        
        if amount <= 0 or amount > 100:
            return await interaction.followup.send("Amount must be between 1 and 100.", ephemeral=True)
            
        try:
            def check(msg):
                if member:
                    return msg.author == member
                return True
                
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = discord.Embed(
                title="Messages Purged",
                description=f"Deleted {len(deleted)} messages" + (f" from {member.mention}" if member else ""),
                color=discord.Color.blue()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in purge command: {e}")
            await interaction.followup.send("An error occurred while trying to purge messages.", ephemeral=True)
            
    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.describe(
        channel="The channel to lock",
        reason="Reason for locking"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
        """Lock a channel"""
        await interaction.response.defer(ephemeral=True)
        
        if not channel:
            channel = interaction.channel
            
        try:
            # Remove send messages permission for @everyone
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=f"{reason} - By {interaction.user}")
            
            embed = discord.Embed(
                title="Channel Locked",
                description=f"{channel.mention} has been locked.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            await channel.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage this channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in lock command: {e}")
            await interaction.followup.send("An error occurred while trying to lock the channel.", ephemeral=True)
            
    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(
        channel="The channel to unlock",
        reason="Reason for unlocking"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
        """Unlock a channel"""
        await interaction.response.defer(ephemeral=True)
        
        if not channel:
            channel = interaction.channel
            
        try:
            # Reset send messages permission for @everyone
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=f"{reason} - By {interaction.user}")
            
            embed = discord.Embed(
                title="Channel Unlocked",
                description=f"{channel.mention} has been unlocked.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            await channel.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage this channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in unlock command: {e}")
            await interaction.followup.send("An error occurred while trying to unlock the channel.", ephemeral=True)
            
    @app_commands.command(name="slowmode", description="Set slowmode for a channel")
    @app_commands.describe(
        seconds="Slowmode duration in seconds (0-21600)",
        channel="The channel to set slowmode for"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
        """Set slowmode for a channel"""
        await interaction.response.defer(ephemeral=True)
        
        if not channel:
            channel = interaction.channel
            
        if seconds < 0 or seconds > 21600:
            return await interaction.followup.send("Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
            
        try:
            await channel.edit(slowmode_delay=seconds, reason=f"Slowmode set by {interaction.user}")
            
            if seconds == 0:
                description = f"Slowmode has been disabled for {channel.mention}."
            else:
                description = f"Slowmode has been set to {seconds} seconds for {channel.mention}."
                
            embed = discord.Embed(
                title="Slowmode Updated",
                description=description,
                color=discord.Color.blue()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage this channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in slowmode command: {e}")
            await interaction.followup.send("An error occurred while trying to set slowmode.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))
