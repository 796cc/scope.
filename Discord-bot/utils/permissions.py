import discord
from typing import List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class PermissionManager:
    def __init__(self):
        self.permission_overrides = {}  # Store custom permission overrides
        
    def has_permission(self, member: discord.Member, permission: Union[str, discord.Permissions]) -> bool:
        """Check if a member has a specific permission"""
        if isinstance(permission, str):
            permission_flag = getattr(discord.Permissions, permission, None)
            if permission_flag is None:
                logger.warning(f"Unknown permission: {permission}")
                return False
        else:
            permission_flag = permission
            
        return member.guild_permissions.is_superset(permission_flag)
        
    def can_moderate(self, moderator: discord.Member, target: discord.Member) -> bool:
        """Check if a moderator can perform actions on a target member"""
        # Server owner can moderate anyone
        if moderator.id == moderator.guild.owner_id:
            return True
            
        # Can't moderate yourself
        if moderator.id == target.id:
            return False
            
        # Can't moderate the server owner
        if target.id == target.guild.owner_id:
            return False
            
        # Check role hierarchy
        if moderator.top_role <= target.top_role:
            return False
            
        return True
        
    def can_manage_role(self, member: discord.Member, role: discord.Role) -> bool:
        """Check if a member can manage a specific role"""
        # Server owner can manage any role
        if member.id == member.guild.owner_id:
            return True
            
        # Must have manage_roles permission
        if not member.guild_permissions.manage_roles:
            return False
            
        # Role must be below member's highest role
        if role >= member.top_role:
            return False
            
        return True
        
    def can_bot_manage_role(self, bot_member: discord.Member, role: discord.Role) -> bool:
        """Check if the bot can manage a specific role"""
        # Must have manage_roles permission
        if not bot_member.guild_permissions.manage_roles:
            return False
            
        # Role must be below bot's highest role
        if role >= bot_member.top_role:
            return False
            
        return True
        
    def get_missing_permissions(self, member: discord.Member, required_permissions: List[str]) -> List[str]:
        """Get a list of permissions that a member is missing"""
        missing = []
        
        for perm_name in required_permissions:
            if not hasattr(discord.Permissions, perm_name):
                logger.warning(f"Unknown permission: {perm_name}")
                continue
                
            if not getattr(member.guild_permissions, perm_name, False):
                missing.append(perm_name)
                
        return missing
        
    def format_permissions(self, permissions: discord.Permissions) -> List[str]:
        """Format permissions into a readable list"""
        perm_list = []
        
        permission_names = {
            'administrator': 'Administrator',
            'manage_guild': 'Manage Server',
            'manage_roles': 'Manage Roles',
            'manage_channels': 'Manage Channels',
            'manage_messages': 'Manage Messages',
            'manage_webhooks': 'Manage Webhooks',
            'manage_nicknames': 'Manage Nicknames',
            'manage_emojis': 'Manage Emojis',
            'kick_members': 'Kick Members',
            'ban_members': 'Ban Members',
            'moderate_members': 'Moderate Members',
            'view_audit_log': 'View Audit Log',
            'view_guild_insights': 'View Server Insights',
            'create_instant_invite': 'Create Invite',
            'change_nickname': 'Change Nickname',
            'view_channel': 'View Channels',
            'send_messages': 'Send Messages',
            'send_tts_messages': 'Send TTS Messages',
            'embed_links': 'Embed Links',
            'attach_files': 'Attach Files',
            'read_message_history': 'Read Message History',
            'mention_everyone': 'Mention Everyone',
            'use_external_emojis': 'Use External Emojis',
            'add_reactions': 'Add Reactions',
            'connect': 'Connect to Voice',
            'speak': 'Speak in Voice',
            'mute_members': 'Mute Members',
            'deafen_members': 'Deafen Members',
            'move_members': 'Move Members',
            'use_voice_activation': 'Use Voice Activity',
            'priority_speaker': 'Priority Speaker',
            'stream': 'Video/Stream',
            'use_slash_commands': 'Use Slash Commands',
            'request_to_speak': 'Request to Speak'
        }
        
        for perm_name, is_set in permissions:
            if is_set and perm_name in permission_names:
                perm_list.append(permission_names[perm_name])
                
        return sorted(perm_list)
        
    def check_bot_permissions(self, guild: discord.Guild, required_permissions: List[str]) -> dict:
        """Check if the bot has required permissions in a guild"""
        bot_member = guild.me
        if not bot_member:
            return {"has_permissions": False, "missing": required_permissions}
            
        missing = self.get_missing_permissions(bot_member, required_permissions)
        
        return {
            "has_permissions": len(missing) == 0,
            "missing": missing,
            "member": bot_member
        }
        
    def get_permission_level(self, member: discord.Member) -> str:
        """Get a member's permission level as a string"""
        if member.id == member.guild.owner_id:
            return "Owner"
        elif member.guild_permissions.administrator:
            return "Administrator"
        elif any([
            member.guild_permissions.manage_guild,
            member.guild_permissions.manage_roles,
            member.guild_permissions.manage_channels,
        ]):
            return "Manager"
        elif any([
            member.guild_permissions.kick_members,
            member.guild_permissions.ban_members,
            member.guild_permissions.moderate_members,
            member.guild_permissions.manage_messages,
        ]):
            return "Moderator"
        else:
            return "Member"
            
    def requires_permission(self, permission: str):
        """Decorator to check permissions before command execution"""
        def decorator(func):
            async def wrapper(interaction: discord.Interaction, *args, **kwargs):
                if not self.has_permission(interaction.user, permission):
                    await interaction.response.send_message(
                        f"You need the `{permission}` permission to use this command.",
                        ephemeral=True
                    )
                    return
                return await func(interaction, *args, **kwargs)
            return wrapper
        return decorator
        
    def requires_role_hierarchy(self, func):
        """Decorator to check role hierarchy for moderation commands"""
        async def wrapper(interaction: discord.Interaction, target: discord.Member, *args, **kwargs):
            if not self.can_moderate(interaction.user, target):
                await interaction.response.send_message(
                    "You cannot perform this action on this member due to role hierarchy.",
                    ephemeral=True
                )
                return
            return await func(interaction, target, *args, **kwargs)
        return wrapper
