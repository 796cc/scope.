import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VoiceMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.voice_activity = {}  # Track user voice activity
        self.afk_threshold_minutes = 10  # Minutes before considering AFK
        
    async def handle_voice_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state updates"""
        user_id = str(member.id)
        current_time = datetime.now()
        
        # User joins or moves to a voice channel
        if after.channel and not before.channel:
            self.voice_activity[user_id] = {
                "lastActive": current_time,
                "channelId": str(after.channel.id),
                "guildId": str(member.guild.id)
            }
            logger.debug(f"User {member} joined voice channel {after.channel.name}")
            
        # User moves between voice channels
        elif after.channel and before.channel and after.channel.id != before.channel.id:
            self.voice_activity[user_id] = {
                "lastActive": current_time,
                "channelId": str(after.channel.id),
                "guildId": str(member.guild.id)
            }
            logger.debug(f"User {member} moved from {before.channel.name} to {after.channel.name}")
            
        # User leaves voice channel
        elif not after.channel and before.channel:
            if user_id in self.voice_activity:
                del self.voice_activity[user_id]
            logger.debug(f"User {member} left voice channel {before.channel.name}")
            
        # User changes state in same channel (mute/unmute, deaf/undeaf)
        elif after.channel and before.channel and after.channel.id == before.channel.id:
            # Update activity time for any voice state change
            if user_id in self.voice_activity:
                self.voice_activity[user_id]["lastActive"] = current_time
            logger.debug(f"User {member} changed voice state in {after.channel.name}")
            
    async def check_afk_users(self):
        """Check for AFK users and move them to AFK channel if configured"""
        current_time = datetime.now()
        afk_threshold = timedelta(minutes=self.afk_threshold_minutes)
        
        for user_id, activity_data in list(self.voice_activity.items()):
            last_active = activity_data["lastActive"]
            
            # Check if user has been inactive for too long
            if current_time - last_active > afk_threshold:
                try:
                    # Get guild and member
                    guild = self.bot.get_guild(int(activity_data["guildId"]))
                    if not guild:
                        continue
                        
                    member = guild.get_member(int(user_id))
                    if not member or not member.voice:
                        # User is no longer in voice, clean up
                        del self.voice_activity[user_id]
                        continue
                        
                    # Check if guild has an AFK channel configured
                    if guild.afk_channel and member.voice.channel.id != guild.afk_channel.id:
                        # Move user to AFK channel
                        await member.move_to(guild.afk_channel, reason="Moved to AFK channel due to inactivity")
                        logger.info(f"Moved {member} to AFK channel due to inactivity")
                        
                        # Update activity data for AFK channel
                        self.voice_activity[user_id]["channelId"] = str(guild.afk_channel.id)
                        self.voice_activity[user_id]["lastActive"] = current_time
                        
                except discord.Forbidden:
                    logger.warning(f"Cannot move user {user_id} to AFK channel - insufficient permissions")
                except discord.HTTPException as e:
                    logger.error(f"Error moving user {user_id} to AFK channel: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error checking AFK user {user_id}: {e}")
                    
    async def cleanup_afk_users(self):
        """Clean up disconnected users from voice activity tracking"""
        users_to_remove = []
        
        for user_id, activity_data in self.voice_activity.items():
            try:
                guild = self.bot.get_guild(int(activity_data["guildId"]))
                if not guild:
                    users_to_remove.append(user_id)
                    continue
                    
                member = guild.get_member(int(user_id))
                if not member or not member.voice:
                    users_to_remove.append(user_id)
                    continue
                    
                # Check if user is still in the channel we think they're in
                current_channel_id = str(member.voice.channel.id)
                tracked_channel_id = activity_data["channelId"]
                
                if current_channel_id != tracked_channel_id:
                    # Update the channel ID
                    self.voice_activity[user_id]["channelId"] = current_channel_id
                    self.voice_activity[user_id]["lastActive"] = datetime.now()
                    
            except Exception as e:
                logger.error(f"Error during voice activity cleanup for user {user_id}: {e}")
                users_to_remove.append(user_id)
                
        # Remove users that are no longer in voice
        for user_id in users_to_remove:
            if user_id in self.voice_activity:
                del self.voice_activity[user_id]
                
        if users_to_remove:
            logger.debug(f"Cleaned up {len(users_to_remove)} disconnected users from voice tracking")
            
    async def get_voice_activity_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get voice activity statistics for a guild"""
        guild_users = {
            user_id: data for user_id, data in self.voice_activity.items()
            if data["guildId"] == str(guild_id)
        }
        
        current_time = datetime.now()
        active_users = 0
        afk_users = 0
        
        for user_id, activity_data in guild_users.items():
            time_since_active = current_time - activity_data["lastActive"]
            
            if time_since_active < timedelta(minutes=self.afk_threshold_minutes):
                active_users += 1
            else:
                afk_users += 1
                
        return {
            "total_users": len(guild_users),
            "active_users": active_users,
            "afk_users": afk_users,
            "afk_threshold_minutes": self.afk_threshold_minutes
        }
        
    async def set_afk_threshold(self, minutes: int):
        """Set the AFK threshold in minutes"""
        if minutes < 1 or minutes > 60:
            raise ValueError("AFK threshold must be between 1 and 60 minutes")
            
        self.afk_threshold_minutes = minutes
        logger.info(f"AFK threshold set to {minutes} minutes")
        
    async def is_user_afk(self, user_id: int) -> bool:
        """Check if a user is considered AFK"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.voice_activity:
            return False
            
        activity_data = self.voice_activity[user_id_str]
        time_since_active = datetime.now() - activity_data["lastActive"]
        
        return time_since_active >= timedelta(minutes=self.afk_threshold_minutes)
        
    async def get_user_voice_time(self, user_id: int) -> Optional[timedelta]:
        """Get how long a user has been in voice"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.voice_activity:
            return None
            
        activity_data = self.voice_activity[user_id_str]
        return datetime.now() - activity_data["lastActive"]
