import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BotConfig:
    def __init__(self):
        self.token = os.getenv('DISCORD_TOKEN')
        self.default_prefix = '!'
        self.owner_ids = self._parse_owner_ids()
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Bot settings
        self.max_punishment_logs = 10000
        self.max_command_logs = 1000
        self.max_bot_logs = 1000
        self.cleanup_interval_hours = 24
        self.log_retention_days = 30
        
        # Anti-spam default settings
        self.default_anti_spam = {
            "enabled": False,
            "messagesPerInterval": 1,
            "intervalSeconds": 3,
            "warningThreshold": 3,
            "muteDurationMinutes": 5,
            "action": "mute",
            "clearMessagesOnMute": False
        }
        
        # Voice monitoring settings
        self.voice_afk_threshold_minutes = 10
        self.voice_cleanup_interval_minutes = 5
        
        # Validate configuration
        self._validate_config()
        
    def _parse_owner_ids(self) -> list:
        """Parse owner IDs from environment variable"""
        owner_ids_str = os.getenv('OWNER_IDS', '')
        if not owner_ids_str:
            return []
            
        try:
            return [int(uid.strip()) for uid in owner_ids_str.split(',') if uid.strip()]
        except ValueError as e:
            logger.warning(f"Invalid owner IDs format: {e}")
            return []
            
    def _validate_config(self):
        """Validate bot configuration"""
        if not self.token:
            logger.error("DISCORD_TOKEN environment variable is required!")
            raise ValueError("Missing DISCORD_TOKEN")
            
        if self.debug:
            logger.info("Debug mode enabled")
            
        logger.info(f"Bot configuration loaded with {len(self.owner_ids)} owner(s)")
        
    def is_owner(self, user_id: int) -> bool:
        """Check if a user is a bot owner"""
        return user_id in self.owner_ids
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting"""
        return getattr(self, key, default)
        
    def update_setting(self, key: str, value: Any):
        """Update a configuration setting"""
        if hasattr(self, key):
            setattr(self, key, value)
            logger.info(f"Updated config setting {key} = {value}")
        else:
            logger.warning(f"Unknown config setting: {key}")
            
    def get_database_settings(self) -> Dict[str, str]:
        """Get database-related settings"""
        return {
            "punishment_logs": "data/punishment_logs.json",
            "bot_logs": "data/bot_logs.json",
            "command_logs": "data/command_logs.json",
            "user_notes": "data/user_notes.json",
            "anti_spam_config": "data/anti_spam_config.json"
        }
        
    def get_permissions_config(self) -> Dict[str, Any]:
        """Get permissions configuration"""
        return {
            "require_hierarchy_check": True,
            "allow_owner_bypass": True,
            "default_mod_permissions": [
                "kick_members",
                "ban_members",
                "manage_messages",
                "moderate_members"
            ],
            "default_admin_permissions": [
                "administrator",
                "manage_guild",
                "manage_roles",
                "manage_channels"
            ]
        }
        
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "log_commands": True,
            "log_moderation_actions": True,
            "log_bot_actions": True,
            "log_level": "INFO" if not self.debug else "DEBUG",
            "max_log_size_mb": 10,
            "backup_count": 5
        }
        
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        return {
            "anti_spam_enabled": True,
            "voice_monitoring_enabled": True,
            "punishment_logging_enabled": True,
            "user_notes_enabled": True,
            "auto_moderation_enabled": True,
            "command_logging_enabled": True
        }
        
    def __str__(self) -> str:
        """String representation of config (without sensitive data)"""
        return f"BotConfig(debug={self.debug}, owners={len(self.owner_ids)}, prefix='{self.default_prefix}')"
