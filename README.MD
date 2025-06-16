# Scope. - Open Source 

A comprehensive Discord moderation bot built with Python and discord.py. This open-source version uses JSON file storage for maximum portability and ease of deployment.

## Features

### 🛡️ Moderation Commands
- **Kick** - Remove members from the server
- **Ban** - Permanently ban members with message deletion options
- **Timeout** - Temporarily restrict member access
- **Warn** - Issue warnings to members
- **Purge** - Bulk delete messages with filtering options

### 🔧 Utility Commands
- **Ping** - Check bot latency and status
- **Embed** - Create custom embedded messages
- **Role Management** - Add/remove roles from members
- **User Notes** - Add and view administrative notes for users

### ℹ️ Information Commands
- **Help** - Display comprehensive command information
- **User Info** - View detailed user information and statistics
- **Server Info** - Display server statistics and information

### ⚙️ Configuration Commands
- **Anti-Spam** - Configure automated spam detection and prevention
- **Logging** - View punishment, command, and action logs
- **Settings** - Manage bot configuration per server/channel

### 🔒 Security Features
- Permission-based command access
- Role hierarchy respect
- Comprehensive audit logging
- Anti-spam protection with configurable thresholds

## Requirements

- Python 3.8 or higher
- discord.py library
- aiofiles for async file operations

## Installation

1. **Clone or download the bot files**
   ```bash
   # Download the main bot file and commands folder
   # Ensure you have: main_opensource.py and commands/ folder
   ```

2. **Install dependencies**
   ```bash
   pip install discord.py aiofiles flask
   ```

3. **Create a Discord Bot**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" section
   - Create a bot and copy the token
   - Enable necessary intents (Message Content Intent, Server Members Intent)

4. **Configure the bot**
   - Create a `.env` file:
     ```
     DISCORD_TOKEN= # Your bot token here
     ```

5. **Invite the bot to your server**
   - Go to OAuth2 > URL Generator in Developer Portal
   - Select "bot" and "applications.commands" scopes
   - Select required permissions:
     - Send Messages
     - Use Slash Commands
     - Kick Members
     - Ban Members
     - Timeout Members
     - Manage Messages
     - Manage Roles
     - View Channel History
   - Use the generated URL to invite the bot

## Usage

### Starting the Bot
```bash
python main_opensource.py
```

### Basic Commands

All commands use Discord's slash command system (`/command`):

**Moderation:**
- `/kick @user [reason]` - Kick a member
- `/ban @user [reason] [delete_days]` - Ban a member
- `/timeout @user duration [reason]` - Timeout a member
- `/warn @user [reason]` - Warn a member
- `/purge amount [@user]` - Delete messages
- more...

**Utility:**
- `/ping` - Check bot status
- `/userinfo [@user]` - View user information
- `/serverinfo` - View server information
- `/addrole @user @role` - Add role to user
- `/removerole @user @role` - Remove role from user
- more...

**Configuration:**
- `/antispam configure` - Setup anti-spam protection
- `/punishment_logs` - View moderation history
- `/cmd_logs` - View command usage logs
- more...

**Entertainment**
- `/coin` Flip a coin
- `/dice` Roll a dice
- more...

### Anti-Spam Configuration

Configure automatic spam detection:

```
/antispam configure enabled:True messages:3 interval:5 action:mute
```

Parameters:
- `enabled` - Enable/disable anti-spam
- `messages` - Messages allowed per interval
- `interval` - Time window in seconds
- `action` - Action to take (warn/mute)
- `mute_duration` - Timeout duration in minutes
- `channel` - Configure for specific channel (optional)

## Data Storage

The bot stores all data in JSON files in the `data/` folder:

- `punishment_logs.json` - Moderation actions history
- `command_logs.json` - Command usage tracking
- `bot_logs.json` - Bot system events
- `user_notes.json` - Administrative notes
- `anti_spam_config.json` - Anti-spam settings

## Permissions

The bot requires these Discord permissions:

**Essential:**
- Send Messages
- Use Slash Commands
- Embed Links
- Read Message History

**Moderation:**
- Kick Members
- Ban Members
- Timeout Members
- Manage Messages

**Role Management:**
- Manage Roles (for role commands)

**Note:** The bot respects Discord's role hierarchy - it cannot moderate users with roles equal to or higher than its own highest role.

## Configuration Files

### Bot Settings
The bot automatically creates necessary configuration files. You can manually edit JSON files in the `data/` folder if needed.

### Log Retention
- Logs are automatically limited to the last 1000 entries
- Old entries are automatically removed to prevent excessive file growth

## Troubleshooting

### Common Issues

**Bot doesn't respond:**
- Check if the bot has proper permissions
- Verify the bot token is correct
- Ensure slash commands are synced (happens automatically on startup)

**Commands fail:**
- Check user permissions for the command
- Verify bot has necessary permissions in the channel
- Check role hierarchy (bot role must be higher than target user)

**Anti-spam not working:**
- Ensure anti-spam is enabled for the channel/server
- Check configuration with `/antispam view`
- Verify bot has timeout permissions

### Log Files

Check `bot.log` for detailed error information and bot activity.

## Development

### File Structure
```
├── main_opensource.py          # Main bot file
├── commands/                   # Command modules
│   ├── moderation_os.py       # Moderation commands
│   ├── utility_os.py          # Utility commands
│   ├── info_os.py             # Information commands
│   └── configuration_os.py    # Configuration commands
├── data/                      # Data storage (auto-created)
│   ├── punishment_logs.json
│   ├── command_logs.json
│   ├── bot_logs.json
│   ├── user_notes.json
│   └── anti_spam_config.json
└── bot.log                    # Log file
```

### Adding Custom Commands

1. Create a new command in the appropriate module
2. Use the `@app_commands.command` decorator
3. Add proper permission checks
4. Follow the existing error handling pattern

### Extending Functionality

The bot is designed to be easily extensible:
- Add new cogs in the `commands/` folder
- Load them in `setup_hook()` method
- Use the existing logging and data storage patterns

## Support

This is an open-source project. For issues:
1. Check the troubleshooting section
2. Review log files for errors
3. Ensure all requirements are met

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Version Information

- **Version:** Scope. 0.3.0
- **Discord.py Version:** 2.x
- **Python Version:** 3.8"

---

**Note:** This is the open-source version designed for easy deployment anywhere. It uses JSON file storage instead of databases for maximum portability.

---

## Special Thanks

- **Fex (@796cc):** Main Developer, Tester.
- **Delfonox:** Tester, Bug Reporter, Feature Suggestor.
- **And people who in .gg/AB6aWbJ8Jq ;)**
