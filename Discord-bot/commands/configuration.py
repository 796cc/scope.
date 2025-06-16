import discord
from discord import app_commands, Interaction, Embed
from discord.ext import commands
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)

class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="antispam", description="Configure anti-spam settings")
    @app_commands.describe(
        action="Action to perform",
        enabled="Enable or disable anti-spam",
        messages="Messages per interval",
        interval="Interval in seconds",
        warnings="Warning threshold before action",
        mute_duration="Mute duration in minutes",
        action_type="Action to take (mute or warn)",
        clear_messages="Clear messages on mute",
        channel="Specific channel to configure"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="enable", value="enable"),
            app_commands.Choice(name="disable", value="disable"),
            app_commands.Choice(name="configure", value="configure"),
            app_commands.Choice(name="status", value="status"),
            app_commands.Choice(name="reset", value="reset")
        ],
        action_type=[
            app_commands.Choice(name="mute", value="mute"),
            app_commands.Choice(name="warn", value="warn")
        ]
    )
    @app_commands.default_permissions(administrator=True)
    async def antispam(
        self,
        interaction: discord.Interaction,
        action: str,
        enabled: bool = None,
        messages: int = None,
        interval: int = None,
        warnings: int = None,
        mute_duration: int = None,
        action_type: str = None,
        clear_messages: bool = None,
        channel: discord.TextChannel = None
    ):
        """Configure anti-spam settings"""
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        
        if action == "enable":
            await self.bot.anti_spam.set_guild_setting(guild_id, "enabled", True)
            embed = discord.Embed(
                title="Anti-Spam Enabled",
                description="Anti-spam protection has been enabled for this server.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        elif action == "disable":
            await self.bot.anti_spam.set_guild_setting(guild_id, "enabled", False)
            embed = discord.Embed(
                title="Anti-Spam Disabled",
                description="Anti-spam protection has been disabled for this server.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        elif action == "configure":
            settings_updated = []
            
            if enabled is not None:
                await self.bot.anti_spam.set_guild_setting(guild_id, "enabled", enabled)
                settings_updated.append(f"Enabled: {enabled}")
                
            if messages is not None:
                if messages < 1 or messages > 50:
                    return await interaction.followup.send("Messages per interval must be between 1 and 50.", ephemeral=True)
                await self.bot.anti_spam.set_guild_setting(guild_id, "messagesPerInterval", messages)
                settings_updated.append(f"Messages per interval: {messages}")
                
            if interval is not None:
                if interval < 1 or interval > 300:
                    return await interaction.followup.send("Interval must be between 1 and 300 seconds.", ephemeral=True)
                await self.bot.anti_spam.set_guild_setting(guild_id, "intervalSeconds", interval)
                settings_updated.append(f"Interval: {interval} seconds")
                
            if warnings is not None:
                if warnings < 1 or warnings > 20:
                    return await interaction.followup.send("Warning threshold must be between 1 and 20.", ephemeral=True)
                await self.bot.anti_spam.set_guild_setting(guild_id, "warningThreshold", warnings)
                settings_updated.append(f"Warning threshold: {warnings}")
                
            if mute_duration is not None:
                if mute_duration < 1 or mute_duration > 1440:
                    return await interaction.followup.send("Mute duration must be between 1 and 1440 minutes (24 hours).", ephemeral=True)
                await self.bot.anti_spam.set_guild_setting(guild_id, "muteDurationMinutes", mute_duration)
                settings_updated.append(f"Mute duration: {mute_duration} minutes")
                
            if action_type is not None:
                await self.bot.anti_spam.set_guild_setting(guild_id, "action", action_type)
                settings_updated.append(f"Action: {action_type}")
                
            if clear_messages is not None:
                await self.bot.anti_spam.set_guild_setting(guild_id, "clearMessagesOnMute", clear_messages)
                settings_updated.append(f"Clear messages on mute: {clear_messages}")
                
            if channel is not None:
                # Configure channel-specific settings
                channel_id = str(channel.id)
                channel_settings = {}
                
                if enabled is not None:
                    channel_settings["enabled"] = enabled
                if messages is not None:
                    channel_settings["messagesPerInterval"] = messages
                if interval is not None:
                    channel_settings["intervalSeconds"] = interval
                if warnings is not None:
                    channel_settings["warningThreshold"] = warnings
                if mute_duration is not None:
                    channel_settings["muteDurationMinutes"] = mute_duration
                if action_type is not None:
                    channel_settings["action"] = action_type
                if clear_messages is not None:
                    channel_settings["clearMessagesOnMute"] = clear_messages
                    
                await self.bot.anti_spam.set_channel_settings(guild_id, channel_id, channel_settings)
                settings_updated.append(f"Channel-specific settings for {channel.mention}")
                
            if not settings_updated:
                return await interaction.followup.send("No settings were provided to update.", ephemeral=True)
                
            embed = discord.Embed(
                title="Anti-Spam Settings Updated",
                description="The following settings have been updated:",
                color=discord.Color.blue()
            )
            embed.add_field(name="Changes", value="\n".join(settings_updated), inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        elif action == "status":
            settings = await self.bot.anti_spam.get_guild_settings(guild_id)
            
            embed = discord.Embed(
                title="Anti-Spam Settings",
                color=discord.Color.blue() if settings.get("enabled", False) else discord.Color.red()
            )
            
            embed.add_field(name="Enabled", value="✅ Yes" if settings.get("enabled", False) else "❌ No", inline=True)
            embed.add_field(name="Messages per Interval", value=str(settings.get("messagesPerInterval", 1)), inline=True)
            embed.add_field(name="Interval", value=f"{settings.get('intervalSeconds', 3)} seconds", inline=True)
            embed.add_field(name="Warning Threshold", value=str(settings.get("warningThreshold", 3)), inline=True)
            embed.add_field(name="Mute Duration", value=f"{settings.get('muteDurationMinutes', 5)} minutes", inline=True)
            embed.add_field(name="Action", value=settings.get("action", "mute").title(), inline=True)
            embed.add_field(name="Clear Messages on Mute", value="✅ Yes" if settings.get("clearMessagesOnMute", False) else "❌ No", inline=True)
            
            # Show channel-specific settings if any
            channels = settings.get("channels", {})
            if channels:
                channel_info = []
                for channel_id, channel_settings in list(channels.items())[:5]:  # Limit to 5 channels
                    channel_obj = interaction.guild.get_channel(int(channel_id))
                    if channel_obj:
                        channel_info.append(f"{channel_obj.mention}: {'Enabled' if channel_settings.get('enabled', True) else 'Disabled'}")
                        
                if channel_info:
                    embed.add_field(name="Channel Overrides", value="\n".join(channel_info), inline=False)
                    
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        elif action == "reset":
            await self.bot.anti_spam.reset_guild_settings(guild_id)
            embed = discord.Embed(
                title="Anti-Spam Settings Reset",
                description="All anti-spam settings have been reset to default values.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="punishment-logs", description="View punishment logs")
    @app_commands.describe(
        user="View logs for a specific user",
        log_type="Filter by punishment type",
        limit="Number of logs to display (1-20)"
    )
    @app_commands.choices(log_type=[
        app_commands.Choice(name="all", value="all"),
        app_commands.Choice(name="warn", value="warn"),
        app_commands.Choice(name="kick", value="kick"),
        app_commands.Choice(name="ban", value="ban"),
        app_commands.Choice(name="timeout", value="timeout")
    ])
    @app_commands.default_permissions(kick_members=True)
    async def punishment_logs(self, interaction: discord.Interaction, user: discord.Member = None, log_type: str = "all", limit: int = 10):
        """View punishment logs"""
        await interaction.response.defer(ephemeral=True)
        
        if limit < 1 or limit > 20:
            return await interaction.followup.send("Limit must be between 1 and 20.", ephemeral=True)
            
        # Get punishment logs from database
        logs = self.bot.db.get_punishment_logs(
            interaction.guild.id, 
            user.id if user else None, 
            log_type if log_type != "all" else None,
            limit
        )
        
        if not logs:
            return await interaction.followup.send("No punishment logs found matching your criteria.", ephemeral=True)
            
        embed = discord.Embed(
            title="Punishment Logs",
            color=discord.Color.blue()
        )
        
        if user:
            embed.description = f"Showing logs for {user.mention}"
        if log_type != "all":
            embed.description = (embed.description or "") + f" | Type: {log_type}"
            
        for i, log in enumerate(logs):
            timestamp = int(log.get('timestamp', 0) / 1000)
            user_obj = self.bot.get_user(int(log.get('userId', 0)))
            moderator_obj = self.bot.get_user(int(log.get('moderatorId', 0)))
            
            user_name = user_obj.mention if user_obj else f"<@{log.get('userId')}>"
            moderator_name = moderator_obj.mention if moderator_obj else f"<@{log.get('moderatorId')}>"
            
            value = f"**User:** {user_name}\n"
            value += f"**Moderator:** {moderator_name}\n"
            value += f"**Reason:** {log.get('reason', 'No reason provided')}\n"
            value += f"**Date:** <t:{timestamp}:R>"
            
            if log.get('duration'):
                value += f"\n**Duration:** {log.get('duration')} minutes"
                
            embed.add_field(
                name=f"{log.get('type', 'Unknown').title()} #{i+1}",
                value=value,
                inline=False
            )
            
        if len(logs) == limit:
            embed.set_footer(text=f"Showing {limit} most recent logs. Use a smaller limit or more specific filters to see different results.")
            
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    @app_commands.command(name="cmd-logs", description="Show recent command logs")
    @app_commands.describe(
        user="Filter by user",
        channel="Filter by channel",
        limit="Number of logs to show (max 50)"
    )
    async def cmd_logs(
        self,
        interaction: Interaction,
        user: discord.User = None,
        channel: discord.TextChannel = None,
        limit: int = 10
    ):
        """Show recent command logs, optionally filtered by user or channel."""
        guild_id = str(interaction.guild.id) if interaction.guild else None
        user_id = str(user.id) if user else None
        channel_id = str(channel.id) if channel else None
        limit = max(1, min(limit, 50))  # Clamp limit between 1 and 50

        logs = self.bot.db.get_command_logs(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            limit=limit
        )

        if not logs:
            await interaction.response.send_message("No command logs found for the given filters.", ephemeral=True)
            return

        embed = Embed(
            title=f"Last {len(logs)} Command Logs",
            color=discord.Color.blue()
        )
        for log in logs:
            user_str = log.get("user", {}).get("name", "Unknown")
            cmd = log.get("command", "Unknown")
            ch = log.get("channel", {}).get("id", "Unknown")
            status = "✅" if log.get("success", True) else "❌"
            ts = log.get("timestamp")
            time_str = f"<t:{int(ts/1000)}:R>" if ts else "Unknown"
            embed.add_field(
                name=f"{status} {cmd}",
                value=f"User: `{user_str}`\nChannel: <#{ch}>\nTime: {time_str}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="version", description="Show the bot's name, logo, and version.")
    async def version(self, interaction: Interaction):
        info_path = os.path.join("data", "bot_info.json")
        if not os.path.exists(info_path):
            await interaction.response.send_message("Bot info file not found.", ephemeral=True)
            return
        with open(info_path, "r") as f:
            info = json.load(f)
        name = info.get("name", "Unknown Bot")
        version = info.get("version", "Unknown Version")
        logo_url = info.get("logo_url", None)
        embed = Embed(title=f"{name} Version", description=f"**Version:** `{version}`", color=discord.Color.green())
        if logo_url:
            embed.set_thumbnail(url=logo_url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Configuration(bot))
