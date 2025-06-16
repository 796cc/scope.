import json
import aiofiles
import logging
from datetime import datetime
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

class LoggingSystem:
    def __init__(self):
        self.punishment_logs_file = "data/punishment_logs.json"
        self.bot_logs_file = "data/bot_logs.json"
        self.command_logs_file = "data/command_logs.json"
        
        self.punishment_logs = []
        self.bot_logs = []
        self.command_logs = []
        
    async def load_punishment_logs(self):
        """Load punishment logs from file"""
        try:
            async with aiofiles.open(self.punishment_logs_file, 'r') as f:
                content = await f.read()
                self.punishment_logs = json.loads(content)
            logger.info("Punishment logs loaded successfully")
        except FileNotFoundError:
            logger.info("Punishment logs file not found, creating empty list")
            self.punishment_logs = []
            await self.save_punishment_logs()
        except Exception as e:
            logger.error(f"Error loading punishment logs: {e}")
            self.punishment_logs = []
            
    async def save_punishment_logs(self):
        """Save punishment logs to file"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            async with aiofiles.open(self.punishment_logs_file, 'w') as f:
                await f.write(json.dumps(self.punishment_logs, indent=2))
            logger.info("Punishment logs saved successfully")
        except Exception as e:
            logger.error(f"Error saving punishment logs: {e}")
            
    async def add_punishment_log(self, log_entry: Dict[str, Any]):
        """Add a new punishment log entry"""
        self.punishment_logs.append(log_entry)
        await self.save_punishment_logs()
        
    async def get_user_punishments(self, user_id: str, guild_id: str = None) -> List[Dict[str, Any]]:
        """Get punishment logs for a specific user"""
        logs = [log for log in self.punishment_logs if log.get('userId') == user_id]
        
        if guild_id:
            logs = [log for log in logs if log.get('guildId') == guild_id]
            
        return sorted(logs, key=lambda x: x.get('timestamp', 0), reverse=True)
        
    async def load_bot_logs(self):
        """Load bot action logs from file"""
        try:
            async with aiofiles.open(self.bot_logs_file, 'r') as f:
                content = await f.read()
                self.bot_logs = json.loads(content)
            logger.info("Bot logs loaded successfully")
        except FileNotFoundError:
            logger.info("Bot logs file not found, creating empty list")
            self.bot_logs = []
            await self.save_bot_logs()
        except Exception as e:
            logger.error(f"Error loading bot logs: {e}")
            self.bot_logs = []
            
    async def save_bot_logs(self):
        """Save bot logs to file"""
        try:
            os.makedirs("data", exist_ok=True)
            
            async with aiofiles.open(self.bot_logs_file, 'w') as f:
                await f.write(json.dumps(self.bot_logs, indent=2))
        except Exception as e:
            logger.error(f"Error saving bot logs: {e}")
            
    async def log_bot_action(self, action: str, is_important: bool = False):
        """Log a bot action"""
        log_entry = {
            "action": action,
            "timestamp": datetime.now().timestamp() * 1000,
            "important": is_important
        }
        
        self.bot_logs.append(log_entry)
        
        # Keep only last 1000 entries to prevent file from growing too large
        if len(self.bot_logs) > 1000:
            self.bot_logs = self.bot_logs[-1000:]
            
        await self.save_bot_logs()
        
    async def load_command_logs(self):
        """Load command logs from file"""
        try:
            async with aiofiles.open(self.command_logs_file, 'r') as f:
                content = await f.read()
                self.command_logs = json.loads(content)
            logger.info("Command logs loaded successfully")
        except FileNotFoundError:
            logger.info("Command logs file not found, creating empty list")
            self.command_logs = []
            await self.save_command_logs()
        except Exception as e:
            logger.error(f"Error loading command logs: {e}")
            self.command_logs = []
            
    async def save_command_logs(self):
        """Save command logs to file"""
        try:
            os.makedirs("data", exist_ok=True)
            
            async with aiofiles.open(self.command_logs_file, 'w') as f:
                await f.write(json.dumps(self.command_logs, indent=2))
        except Exception as e:
            logger.error(f"Error saving command logs: {e}")
            
    async def log_command_execution(self, interaction, success: bool = True, error: str = None):
        """Log a command execution"""
        log_entry = {
            "command": interaction.command.name if interaction.command else "unknown",
            "user": {
                "id": str(interaction.user.id),
                "name": str(interaction.user),
                "discriminator": interaction.user.discriminator
            },
            "guild": {
                "id": str(interaction.guild.id) if interaction.guild else None,
                "name": interaction.guild.name if interaction.guild else "DM"
            },
            "channel": {
                "id": str(interaction.channel.id) if interaction.channel else None,
                "name": getattr(interaction.channel, 'name', 'Unknown')
            },
            "success": success,
            "error": error,
            "timestamp": datetime.now().timestamp() * 1000
        }
        
        self.command_logs.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.command_logs) > 1000:
            self.command_logs = self.command_logs[-1000:]
            
        await self.save_command_logs()
        
    async def get_recent_logs(self, log_type: str = "punishment", limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent logs of specified type"""
        if log_type == "punishment":
            logs = self.punishment_logs
        elif log_type == "bot":
            logs = self.bot_logs
        elif log_type == "command":
            logs = self.command_logs
        else:
            return []
            
        # Sort by timestamp (newest first) and limit
        sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', 0), reverse=True)
        return sorted_logs[:limit]
        
    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up logs older than specified days"""
        cutoff_timestamp = (datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)) * 1000
        
        # Clean punishment logs
        original_count = len(self.punishment_logs)
        self.punishment_logs = [log for log in self.punishment_logs if log.get('timestamp', 0) > cutoff_timestamp]
        
        if len(self.punishment_logs) != original_count:
            await self.save_punishment_logs()
            logger.info(f"Cleaned up {original_count - len(self.punishment_logs)} old punishment logs")
            
        # Clean bot logs
        original_count = len(self.bot_logs)
        self.bot_logs = [log for log in self.bot_logs if log.get('timestamp', 0) > cutoff_timestamp]
        
        if len(self.bot_logs) != original_count:
            await self.save_bot_logs()
            logger.info(f"Cleaned up {original_count - len(self.bot_logs)} old bot logs")
            
        # Clean command logs
        original_count = len(self.command_logs)
        self.command_logs = [log for log in self.command_logs if log.get('timestamp', 0) > cutoff_timestamp]
        
        if len(self.command_logs) != original_count:
            await self.save_command_logs()
            logger.info(f"Cleaned up {original_count - len(self.command_logs)} old command logs")
