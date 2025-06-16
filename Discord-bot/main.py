import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import logging
from datetime import datetime, timezone
import aiofiles
from keep_alive import keep_alive
from bot_config import BotConfig
from utils.anti_spam import AntiSpamManager
from utils.logging_system import LoggingSystem
from utils.notes_manager import NotesManager
from utils.voice_monitor import VoiceMonitor
from utils.permissions import PermissionManager
from database import DatabaseManager
from dotenv import load_dotenv
import time
import threading
import socket
import sys

# Load environment variables from .env file
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONTROL_PORT = 8765  # You can change this port if needed

class ModerationBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.message_content = True
        intents.voice_states = True

        super().__init__(
            command_prefix="/",  # You can use any prefix you like
            intents=intents,
            help_command=None
        )

        # Initialize managers
        self.config = BotConfig()
        self.db = DatabaseManager()
        self.anti_spam = AntiSpamManager()
        self.logging_system = LoggingSystem()
        self.notes_manager = NotesManager()
        self.voice_monitor = VoiceMonitor(self)
        self.permission_manager = PermissionManager()

        # Data storage
        self.punishment_logs = []
        self.user_notes_data = {}
        # self.last_command_times = {}  # REMOVE anti-spam tracking

    async def setup_hook(self):
        """Load cogs and initialize data when bot starts"""
        # Load command cogs
        await self.load_extension('commands.moderation')
        await self.load_extension('commands.utility')
        await self.load_extension('commands.info')
        await self.load_extension('commands.configuration')
        await self.load_extension('commands.entertainment')
        await self.load_extension('commands.verification')
        await self.load_extension('commands.support')
        
        # Log that the moderation cog has been loaded
        self.db.add_bot_log("Loaded cog: moderation", False)
        
        # Load data
        await self.load_all_data()
        
        # Sync slash commands globally
        try:
            synced = await self.tree.sync()
            logger.info(f"Globally synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
            
        # Start background tasks
        self.cleanup_task.start()
        
        # Load command logs data
        await self.logging_system.load_command_logs()
        print([cmd.name for cmd in self.tree.get_commands()])
        
    async def load_all_data(self):
        """Load all persistent data"""
        await self.anti_spam.load_config()
        await self.logging_system.load_punishment_logs()
        await self.notes_manager.load_notes()
        self.punishment_logs = self.logging_system.punishment_logs
        self.user_notes_data = self.notes_manager.user_notes_data
        
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'Bot is ready! Logged in as {self.user}')
        await self.change_presence(
            activity=discord.CustomActivity(name="luv u :3", type=discord.ActivityType.playing)
        )
        self.db.add_bot_log(f"Bot started: Logged in as {self.user}", True)
        
    async def on_message(self, message):
        """Handle message events for anti-spam"""
        if message.author.bot:
            return
            
        # Process anti-spam
        await self.anti_spam.process_message(message, self)
        
        # Process commands (fallback)
        await self.process_commands(message)
        
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates for AFK monitoring"""
        await self.voice_monitor.handle_voice_update(member, before, after)
        
    async def on_guild_join(self, guild):
        self.db.add_bot_log(f"Joined guild: {guild.name} (ID: {guild.id})", True)

    async def on_guild_remove(self, guild):
        self.db.add_bot_log(f"Left guild: {guild.name} (ID: {guild.id})", True)
        
    async def on_command(self, ctx):
        """Log every command invocation."""
        log_msg = (
            f"Command '{ctx.command}' run by {ctx.author} (ID: {ctx.author.id}) "
            f"in #{ctx.channel} (ID: {ctx.channel.id}) of {ctx.guild} (ID: {ctx.guild.id})"
        )
        self.db.add_bot_log(log_msg, important=True)

    async def on_command_error(self, ctx, error):
        """Log command errors."""
        log_msg = (
            f"Error in command '{ctx.command}' by {ctx.author} (ID: {ctx.author.id}) "
            f"in #{ctx.channel} (ID: {ctx.channel.id}) of {ctx.guild} (ID: {ctx.guild.id}): {error}"
        )
        self.db.add_bot_log(log_msg, important=True)
        await ctx.send(f"An error occurred: {error}")

    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        """Log every slash command invocation."""
        command_data = {
            "command": command.qualified_name,
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": True,
            "timestamp": datetime.now(timezone.utc).timestamp() * 1000
        }
        self.db.add_command_log(command_data)

    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Log slash command errors."""
        command = getattr(interaction.command, "qualified_name", "unknown")
        command_data = {
            "command": command,
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": False,
            "error": str(error),
            "timestamp": datetime.now(timezone.utc).timestamp() * 1000
        }
        self.db.add_command_log(command_data)

    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        """Periodic cleanup task"""
        try:
            # Cleanup anti-spam data
            await self.anti_spam.cleanup_old_data()
            # Cleanup voice monitor data
            await self.voice_monitor.cleanup_afk_users()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            
    @cleanup_task.before_loop
    async def before_cleanup_task(self):
        """Wait until bot is ready before starting cleanup"""
        await self.wait_until_ready()

def control_server(bot):
    """Threaded server to listen for control commands."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', CONTROL_PORT))
        s.listen(1)
        print(f"[Control] Listening for commands on port {CONTROL_PORT}...")
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if not data:
                    continue
                try:
                    cmd = data.decode().strip()
                    print(f"[Control] Received: {cmd}")
                    # Parse and execute commands
                    if cmd == "restart":
                        # Restart the bot (soft restart)
                        os.execv(sys.executable, ['python'] + sys.argv)
                    elif cmd == "shutdown":
                        await_shutdown = getattr(bot, "close", None)
                        if await_shutdown:
                            import asyncio
                            asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                        conn.sendall(b"Bot shutting down.\n")
                        break
                    elif cmd.startswith("status "):
                        # Usage: status <text> [type]
                        parts = cmd.split()
                        if len(parts) >= 2:
                            status_text = parts[1]
                            # Allow spaces in status text
                            if len(parts) > 2:
                                # If type is specified, it should be the last word
                                activity_type_str = parts[-1].lower()
                                status_text = " ".join(parts[1:-1])
                            else:
                                activity_type_str = "playing"
                            # Map string to discord.ActivityType
                            activity_type_map = {
                                "playing": discord.ActivityType.playing,
                                "watching": discord.ActivityType.watching,
                                "listening": discord.ActivityType.listening,
                                "competing": discord.ActivityType.competing,
                                "streaming": discord.ActivityType.streaming,
                            }
                            activity_type = activity_type_map.get(activity_type_str, discord.ActivityType.playing)
                            asyncio.run_coroutine_threadsafe(
                                bot.change_presence(activity=discord.Activity(type=activity_type, name=status_text)),
                                bot.loop
                            )
                            conn.sendall(f"Status changed to: {status_text} (type={activity_type_str})\n".encode())
                        else:
                            conn.sendall(b"Usage: status <text> [type]\n")
                    elif cmd.startswith("list "):
                        dtype = cmd[5:]
                        file_map = {
                            "notes": "user_notes.json",
                            "punishment": "punishment_logs.json",
                            "command": "command_logs.json",
                            "support": f"support_tickets_{bot.guilds[0].id}.json" if bot.guilds else None
                        }
                        fname = file_map.get(dtype)
                        if fname:
                            fpath = os.path.join("data", fname)
                            if os.path.exists(fpath):
                                with open(fpath, "r") as f:
                                    logs = json.load(f)
                                conn.sendall((json.dumps(logs, indent=2) + "\n").encode())
                            else:
                                conn.sendall(b"File not found.\n")
                        else:
                            conn.sendall(b"Unknown data type.\n")
                    elif cmd == "logs":
                        fpath = os.path.join("data", "bot_logs.json")
                        if os.path.exists(fpath):
                            with open(fpath, "r") as f:
                                logs = json.load(f)
                            conn.sendall((json.dumps(logs, indent=2) + "\n").encode())
                        else:
                            conn.sendall(b"No logs found.\n")
                    else:
                        conn.sendall(b"Unknown command.\n")
                except Exception as e:
                    conn.sendall(f"Error: {e}\n".encode())

# Start the control server in a thread after bot is ready
def start_control_server(bot):
    t = threading.Thread(target=control_server, args=(bot,), daemon=True)
    t.start()

# Initialize and run bot
bot = ModerationBot()

async def main():
    """Main function to run the bot"""
    # Start keep-alive server
    keep_alive()
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not found!")
        return
        
    try:
        # Start control server
        start_control_server(bot)
        
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        # Don't use self here since we're not in a class
        bot.db.add_bot_log(f"Bot crashed: {e}", True)
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        bot = ModerationBot()
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        # Don't use self here since we're not in a class
        bot.db.add_bot_log(f"Bot crashed: {e}", True)
