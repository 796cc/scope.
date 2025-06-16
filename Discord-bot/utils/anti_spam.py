import asyncio
import json
import aiofiles
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import discord
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)

class AntiSpamManager:
    def __init__(self):
        self.config_file = "data/anti_spam_config.json"
        self.settings = {
            "default": {
                "enabled": False,
                "messagesPerInterval": 1,
                "intervalSeconds": 3,
                "warningThreshold": 3,
                "muteDurationMinutes": 5,
                "action": "mute",
                "clearMessagesOnMute": False,
                "channels": {}
            }
        }
        self.spam_state = {}  # Track user message counts
        
    async def load_config(self):
        """Load anti-spam configuration from file"""
        try:
            async with aiofiles.open(self.config_file, 'r') as f:
                content = await f.read()
                self.settings = json.loads(content)
                
            # Ensure default settings exist
            if "default" not in self.settings:
                self.settings["default"] = {
                    "enabled": False,
                    "messagesPerInterval": 1,
                    "intervalSeconds": 3,
                    "warningThreshold": 3,
                    "muteDurationMinutes": 5,
                    "action": "mute",
                    "clearMessagesOnMute": False,
                    "channels": {}
                }
                
            # Ensure channels property exists for all guild configs
            for guild_id in self.settings:
                if "channels" not in self.settings[guild_id]:
                    self.settings[guild_id]["channels"] = {}
                    
            logger.info("Anti-spam config loaded successfully")
            
        except FileNotFoundError:
            logger.info("Anti-spam config file not found, creating default")
            await self.save_config()
        except Exception as e:
            logger.error(f"Error loading anti-spam config: {e}")
            
    async def save_config(self):
        """Save anti-spam configuration to file"""
        try:
            # Ensure data directory exists
            import os
            os.makedirs("data", exist_ok=True)
            
            async with aiofiles.open(self.config_file, 'w') as f:
                await f.write(json.dumps(self.settings, indent=2))
            logger.info("Anti-spam config saved successfully")
        except Exception as e:
            logger.error(f"Error saving anti-spam config: {e}")
            
    async def get_guild_settings(self, guild_id: str) -> Dict[str, Any]:
        """Get anti-spam settings for a guild"""
        return self.settings.get(guild_id, self.settings["default"])
        
    async def set_guild_setting(self, guild_id: str, key: str, value: Any):
        """Set a guild-specific anti-spam setting"""
        if guild_id not in self.settings:
            self.settings[guild_id] = self.settings["default"].copy()
            self.settings[guild_id]["channels"] = {}
            
        self.settings[guild_id][key] = value
        await self.save_config()
        
    async def set_channel_settings(self, guild_id: str, channel_id: str, settings: Dict[str, Any]):
        """Set channel-specific anti-spam settings"""
        if guild_id not in self.settings:
            self.settings[guild_id] = self.settings["default"].copy()
            self.settings[guild_id]["channels"] = {}
            
        if "channels" not in self.settings[guild_id]:
            self.settings[guild_id]["channels"] = {}
            
        if channel_id not in self.settings[guild_id]["channels"]:
            self.settings[guild_id]["channels"][channel_id] = {}
            
        self.settings[guild_id]["channels"][channel_id].update(settings)
        await self.save_config()
        
    async def reset_guild_settings(self, guild_id: str):
        """Reset guild settings to default"""
        if guild_id in self.settings and guild_id != "default":
            del self.settings[guild_id]
            await self.save_config()
            
    async def process_message(self, message, bot):
        """Process a message for anti-spam checking"""
        # Ignore bots
        if message.author.bot:
            return

        # Ignore admins and owner
        if message.guild:
            if message.author.id == message.guild.owner_id:
                return
            if message.author.guild_permissions.administrator:
                return

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        # Get settings for this guild/channel
        guild_settings = await self.get_guild_settings(guild_id)
        
        # Check if anti-spam is enabled
        if not guild_settings.get("enabled", False):
            return
            
        # Get channel-specific settings if they exist
        channel_settings = guild_settings.get("channels", {}).get(channel_id, {})
        
        # Merge settings (channel overrides guild)
        active_settings = guild_settings.copy()
        active_settings.update(channel_settings)
        
        # Check if anti-spam is disabled for this specific channel
        if not active_settings.get("enabled", True):
            return
            
        # Initialize spam state for this channel
        if channel_id not in self.spam_state:
            self.spam_state[channel_id] = {}
            
        # Initialize user state
        current_time = datetime.now().timestamp()
        if user_id not in self.spam_state[channel_id]:
            self.spam_state[channel_id][user_id] = {
                "count": 0,
                "lastMessageTime": current_time,
                "warnings": 0,
                "muted": False
            }
            
        user_state = self.spam_state[channel_id][user_id]
        
        # Skip if user is already muted
        if user_state.get("muted", False):
            return
            
        # Check if enough time has passed to reset count
        interval_seconds = active_settings.get("intervalSeconds", 3)
        if current_time - user_state["lastMessageTime"] > interval_seconds:
            user_state["count"] = 1
        else:
            user_state["count"] += 1
            
        user_state["lastMessageTime"] = current_time
        
        # Check if user exceeded message limit
        messages_per_interval = active_settings.get("messagesPerInterval", 1)
        if user_state["count"] > messages_per_interval:
            await self.handle_spam_violation(message, bot, active_settings, user_state)
            
    async def handle_spam_violation(self, message: discord.Message, bot, settings: Dict[str, Any], user_state: Dict[str, Any]):
        """Handle a spam violation"""
        user_state["warnings"] += 1
        warning_threshold = settings.get("warningThreshold", 3)
        action = settings.get("action", "mute")
        
        if user_state["warnings"] >= warning_threshold:
            if action == "mute":
                await self.mute_user(message, bot, settings, user_state)
            else:
                await self.warn_user(message, bot, user_state)
        else:
            await self.warn_user(message, bot, user_state)
            
    async def warn_user(self, message: discord.Message, bot, user_state: Dict[str, Any]):
        """Send a warning to the user"""
        try:
            embed = discord.Embed(
                title="⚠️ Spam Warning",
                description=f"{message.author.mention}, please slow down your messages!",
                color=discord.Color.yellow()
            )
            embed.add_field(
                name="Warning Count",
                value=f"{user_state['warnings']}/3",
                inline=True
            )
            
            warning_msg = await message.channel.send(embed=embed)
            
            # Delete warning message after 5 seconds
            await asyncio.sleep(5)
            try:
                await warning_msg.delete()
            except discord.NotFound:
                pass
                
        except Exception as e:
            logger.error(f"Error sending spam warning: {e}")
            
    async def mute_user(self, message: discord.Message, bot, settings: Dict[str, Any], user_state: Dict[str, Any]):
        """Mute a user for spam"""
        try:
            duration_minutes = settings.get("muteDurationMinutes", 5)
            timeout_until = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
            
            # Apply timeout
            await message.author.edit(timed_out_until=timeout_until)
            
            user_state["muted"] = True
            
            # Clear messages if enabled
            if settings.get("clearMessagesOnMute", False):
                try:
                    def check(msg):
                        return (msg.author == message.author and 
                               (datetime.now() - msg.created_at).total_seconds() < 60)  # Last minute
                    
                    await message.channel.purge(limit=10, check=check)
                except Exception as e:
                    logger.error(f"Error clearing spam messages: {e}")
                    
            # Send mute notification
            embed = discord.Embed(
                title="🔇 User Muted for Spam",
                description=f"{message.author.mention} has been muted for {duration_minutes} minutes for spamming.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value="Exceeded message rate limit", inline=False)
            embed.add_field(name="Duration", value=f"{duration_minutes} minutes", inline=True)
            embed.add_field(name="Unmuted", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=True)
            
            await message.channel.send(embed=embed)
            
            # Log the punishment
            log_entry = {
                "type": "timeout",
                "userId": str(message.author.id),
                "username": str(message.author),
                "moderatorId": str(bot.user.id),
                "moderatorName": str(bot.user),
                "guildId": str(message.guild.id),
                "guildName": message.guild.name,
                "reason": "Anti-spam: Exceeded message limit",
                "duration": duration_minutes,
                "timestamp": discord.utils.utcnow().timestamp() * 1000
            }
            await bot.logging_system.add_punishment_log(log_entry)
            
            # Schedule unmute
            await asyncio.sleep(duration_minutes * 60)
            user_state["muted"] = False
            user_state["warnings"] = 0
            
        except discord.Forbidden:
            logger.warning(f"Cannot mute user {message.author} - insufficient permissions")
        except Exception as e:
            logger.error(f"Error muting user for spam: {e}")
            
    async def cleanup_old_data(self):
        """Clean up old spam state data"""
        current_time = datetime.now().timestamp()
        cleanup_threshold = 300  # 5 minutes
        
        for channel_id in list(self.spam_state.keys()):
            for user_id in list(self.spam_state[channel_id].keys()):
                user_data = self.spam_state[channel_id][user_id]
                if current_time - user_data.get("lastMessageTime", 0) > cleanup_threshold:
                    del self.spam_state[channel_id][user_id]
                    
            # Remove empty channel entries
            if not self.spam_state[channel_id]:
                del self.spam_state[channel_id]
