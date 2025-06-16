import json
import aiofiles
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
from discord import app_commands

logger = logging.getLogger(__name__)

class NotesManager:
    def __init__(self):
        self.notes_file = "data/user_notes.json"
        self.user_notes_data = {}  # {guild_id: {user_id: [notes...]}}
        
    async def load_notes(self):
        """Load user notes from file"""
        try:
            async with aiofiles.open(self.notes_file, 'r') as f:
                content = await f.read()
                self.user_notes_data = json.loads(content)
            logger.info("User notes loaded successfully")
        except FileNotFoundError:
            logger.info("User notes file not found, creating empty dict")
            self.user_notes_data = {}
            await self.save_notes()
        except Exception as e:
            logger.error(f"Error loading user notes: {e}")
            self.user_notes_data = {}
            
    async def save_notes(self):
        """Save user notes to file"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            async with aiofiles.open(self.notes_file, 'w') as f:
                await f.write(json.dumps(self.user_notes_data, indent=2))
            logger.info("User notes saved successfully")
        except Exception as e:
            logger.error(f"Error saving user notes: {e}")
            
    async def add_note(self, guild_id: int, user_id: int, note: str, admin_id: int):
        """Add a note for a user"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)
        if guild_id_str not in self.user_notes_data:
            self.user_notes_data[guild_id_str] = {}
        if user_id_str not in self.user_notes_data[guild_id_str]:
            self.user_notes_data[guild_id_str][user_id_str] = []
        note_entry = {
            "note": note,
            "timestamp": datetime.now().timestamp() * 1000,
            "adminId": str(admin_id)
        }
        self.user_notes_data[guild_id_str][user_id_str].append(note_entry)
        await self.save_notes()

    async def get_user_notes(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all notes for a user"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)
        return self.user_notes_data.get(guild_id_str, {}).get(user_id_str, [])

    async def remove_note(self, guild_id: int, user_id: int, note_index: int) -> bool:
        """Remove a specific note by index"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)
        if guild_id_str not in self.user_notes_data:
            return False
        if user_id_str not in self.user_notes_data[guild_id_str]:
            return False
        if note_index < 0 or note_index >= len(self.user_notes_data[guild_id_str][user_id_str]):
            return False
        self.user_notes_data[guild_id_str][user_id_str].pop(note_index)
        if not self.user_notes_data[guild_id_str][user_id_str]:
            del self.user_notes_data[guild_id_str][user_id_str]
        if not self.user_notes_data[guild_id_str]:
            del self.user_notes_data[guild_id_str]
        await self.save_notes()
        return True

    async def clear_user_notes(self, guild_id: int, user_id: int):
        """Clear all notes for a user"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)
        if guild_id_str in self.user_notes_data and user_id_str in self.user_notes_data[guild_id_str]:
            del self.user_notes_data[guild_id_str][user_id_str]
            if not self.user_notes_data[guild_id_str]:
                del self.user_notes_data[guild_id_str]
            await self.save_notes()

    async def search_notes(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search notes containing a specific term"""
        results = []
        
        for guild_id, users_notes in self.user_notes_data.items():
            for user_id, notes in users_notes.items():
                for note_data in notes:
                    if search_term.lower() in note_data['note'].lower():
                        result = note_data.copy()
                        result['userId'] = user_id
                        result['guildId'] = guild_id
                        results.append(result)
                        
                        if len(results) >= limit:
                            break
                            
                if len(results) >= limit:
                    break
                    
            if len(results) >= limit:
                break
                
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return results
        
    def format_notes(self, notes: List[Dict[str, Any]]) -> str:
        """Format notes for display"""
        if not notes:
            return "No notes found."
            
        formatted = []
        for i, note_data in enumerate(notes, 1):
            timestamp = datetime.fromtimestamp(note_data['timestamp'] / 1000)
            date_str = timestamp.strftime('%Y-%m-%d %H:%M')
            
            formatted.append(f"**{i}.** {note_data['note']}")
            formatted.append(f"*Added by <@{note_data['adminId']}> on {date_str}*\n")
            
        return "\n".join(formatted)
        
    async def get_notes_count(self, guild_id: int, user_id: int) -> int:
        """Get the number of notes for a user"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)
        return len(self.user_notes_data.get(guild_id_str, {}).get(user_id_str, []))
        
    async def get_all_users_with_notes(self) -> List[str]:
        """Get all user IDs that have notes"""
        return list(self.user_notes_data.keys())
        
    async def cleanup_old_notes(self, days_to_keep: int = 365):
        """Clean up notes older than specified days"""
        cutoff_timestamp = (datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)) * 1000
        
        users_modified = 0
        notes_removed = 0
        
        for guild_id in list(self.user_notes_data.keys()):
            for user_id in list(self.user_notes_data[guild_id].keys()):
                original_count = len(self.user_notes_data[guild_id][user_id])
                
                # Filter out old notes
                self.user_notes_data[guild_id][user_id] = [
                    note for note in self.user_notes_data[guild_id][user_id]
                    if note.get('timestamp', 0) > cutoff_timestamp
                ]
                
                new_count = len(self.user_notes_data[guild_id][user_id])
                
                if new_count != original_count:
                    users_modified += 1
                    notes_removed += (original_count - new_count)
                    
                # Remove user entry if no notes left
                if not self.user_notes_data[guild_id][user_id]:
                    del self.user_notes_data[guild_id][user_id]
                    
            # Remove guild entry if no users left
            if not self.user_notes_data[guild_id]:
                del self.user_notes_data[guild_id]
                
        if users_modified > 0:
            await self.save_notes()
            logger.info(f"Cleaned up {notes_removed} old notes from {users_modified} users")
            
        return notes_removed

    async def handle_add_note_interaction(self, interaction, note: str):
        """Handle the interaction for adding a note"""
        await self.add_note(
            interaction.guild.id,  # <-- Add this!
            interaction.user.id,
            note,
            interaction.user.id
        )
        notes = await self.get_user_notes(interaction.guild.id, interaction.user.id)
        return notes

@app_commands.command(name="note", description="Add a note for a user (server-specific).")
@app_commands.describe(user="The user to add a note for", note="The note text")
async def note_command(interaction, user: str, note: str):
    """Command to add a note for a user"""
    notes_manager = NotesManager()
    await notes_manager.load_notes()
    
    # Here you would resolve the user ID from the user mention or name
    user_id = int(user.strip("<@!>"))  # Remove <@!> and convert to int
    
    await notes_manager.add_note(interaction.guild.id, user_id, note, interaction.user.id)
    
    await interaction.response.send_message(f"Note added for <@{user_id}>")
