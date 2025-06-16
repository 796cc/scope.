import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime
import json
import os

class Entertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jokes_file = os.path.join("data", "jokes.json")
        self.jokes = self._load_jokes()

    def _load_jokes(self):
        try:
            if os.path.exists(self.jokes_file):
                with open(self.jokes_file, 'r') as f:
                    return json.load(f)["jokes"]
        except json.JSONDecodeError as e:
            print(f"Error loading jokes file: {e}")
        except Exception as e:
            print(f"Unexpected error loading jokes: {e}")
        return []

    @app_commands.command(name="coin", description="Flip a coin!")
    async def coin(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**!")
        # Log command usage
        command_data = {
            "command": "coin",
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": True,
            "timestamp": datetime.utcnow().timestamp() * 1000
        }
        self.bot.db.add_command_log(command_data)

    @app_commands.command(name="flip", description="Flip a coin (alias)!")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**!")
        # Log command usage
        command_data = {
            "command": "flip",
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": True,
            "timestamp": datetime.utcnow().timestamp() * 1000
        }
        self.bot.db.add_command_log(command_data)

    @app_commands.command(name="dice", description="Roll a six-sided dice!")
    async def dice(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 You rolled a **{result}**!")
        # Log command usage
        command_data = {
            "command": "dice",
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": True,
            "timestamp": datetime.utcnow().timestamp() * 1000
        }
        self.bot.db.add_command_log(command_data)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question!")
    @app_commands.describe(question="Your question for the magic 8-ball")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain.", "Without a doubt.", "You may rely on it.",
            "Yes – definitely.", "Most likely.", "Outlook good.",
            "Yes.", "Signs point to yes.", "Reply hazy, try again.",
            "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Don't count on it.",
            "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        result = random.choice(responses)
        await interaction.response.send_message(f"🎱 **Question:** {question}\n**8-ball says:** {result}")
        # Log command usage
        command_data = {
            "command": "8ball",
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": True,
            "timestamp": datetime.utcnow().timestamp() * 1000
        }
        self.bot.db.add_command_log(command_data)

    @app_commands.command(name="joke", description="Tell a random joke!")
    async def joke(self, interaction: discord.Interaction):
        if not self.jokes:
            await interaction.response.send_message("Sorry, I don't know any jokes right now! 😅", ephemeral=True)
            return

        joke = random.choice(self.jokes)
        
        # Send setup and wait 2 seconds before punchline
        await interaction.response.send_message(f"**{joke['setup']}**")
        await interaction.channel.send(f"||{joke['punchline']}||")

        # Log command usage
        command_data = {
            "command": "joke",
            "user": {"id": str(interaction.user.id), "name": str(interaction.user)},
            "guild": {"id": str(interaction.guild.id), "name": interaction.guild.name} if interaction.guild else {},
            "channel": {"id": str(interaction.channel.id)},
            "success": True,
            "timestamp": datetime.utcnow().timestamp() * 1000
        }
        self.bot.db.add_command_log(command_data)

async def setup(bot):
    await bot.add_cog(Entertainment(bot))
