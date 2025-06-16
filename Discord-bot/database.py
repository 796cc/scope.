import os
import json
import aiofiles
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.punishment_logs_file = "data/punishment_logs.json"
        self.command_logs_file = "data/command_logs.json"
        self.bot_logs_file = "data/bot_logs.json"
        self.user_notes_file = "data/user_notes.json"
        os.makedirs("data", exist_ok=True)

    def create_tables(self):
        pass  # No-op for JSON

    def add_punishment_log(self, punishment_data: Dict[str, Any]) -> bool:
        return self._save_json(self.punishment_logs_file, punishment_data)

    def add_command_log(self, command_data: Dict[str, Any]) -> bool:
        return self._save_json(self.command_logs_file, command_data)

    def add_bot_log(self, action: str, important: bool = False) -> bool:
        log_data = {
            'action': action,
            'important': important,
            'timestamp': datetime.utcnow().timestamp() * 1000
        }
        return self._save_json(self.bot_logs_file, log_data)

    def _save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        try:
            logs = []
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    logs = json.load(f)
            logs.append(data)
            if len(logs) > 1000:
                logs = logs[-1000:]
            with open(file_path, 'w') as f:
                json.dump(logs, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {e}")
            return False

    def get_command_logs(
        self,
        guild_id: str = None,
        user_id: str = None,
        channel_id: str = None,
        limit: int = 100
    ) -> list:
        """Return filtered command logs (by guild, user, channel, up to limit)."""
        try:
            if os.path.exists(self.command_logs_file):
                with open(self.command_logs_file, 'r') as f:
                    logs = json.load(f)
                # Filter logs
                if guild_id:
                    logs = [log for log in logs if log.get("guild", {}).get("id") == str(guild_id)]
                if user_id:
                    logs = [log for log in logs if log.get("user", {}).get("id") == str(user_id)]
                if channel_id:
                    logs = [log for log in logs if log.get("channel", {}).get("id") == str(channel_id)]
                return logs[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error reading command logs: {e}")
            return []

    def get_punishment_logs(
        self,
        guild_id: int = None,
        user_id: int = None,
        log_type: str = None,
        limit: int = 10
    ) -> list:
        """Return filtered punishment logs (by guild, user, type, up to limit)."""
        try:
            if os.path.exists(self.punishment_logs_file):
                with open(self.punishment_logs_file, 'r') as f:
                    logs = json.load(f)
                # Filter logs
                if guild_id:
                    logs = [log for log in logs if str(log.get("guildId")) == str(guild_id)]
                if user_id:
                    logs = [log for log in logs if str(log.get("userId")) == str(user_id)]
                if log_type:
                    logs = [log for log in logs if log.get("type") == log_type]
                return logs[-limit:]
            return []
        except Exception as e:
            logger.error(f"Error reading punishment logs: {e}")
            return []