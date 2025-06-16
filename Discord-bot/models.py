from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Guild(Base):
    __tablename__ = 'guilds'
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    punishment_logs = relationship("PunishmentLog", back_populates="guild")
    user_notes = relationship("UserNote", back_populates="guild")
    anti_spam_configs = relationship("AntiSpamConfig", back_populates="guild")
    command_logs = relationship("CommandLog", back_populates="guild")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String(32), nullable=False)
    discriminator = Column(String(4))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    punishment_logs = relationship("PunishmentLog", foreign_keys="PunishmentLog.user_id", back_populates="user")
    moderator_logs = relationship("PunishmentLog", foreign_keys="PunishmentLog.moderator_id", back_populates="moderator")
    user_notes = relationship("UserNote", foreign_keys="UserNote.user_id", back_populates="user")
    command_logs = relationship("CommandLog", back_populates="user")

class PunishmentLog(Base):
    __tablename__ = 'punishment_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False)  # kick, ban, warn, timeout, etc.
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    moderator_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    reason = Column(Text)
    duration = Column(Integer)  # For timeouts, in minutes
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="punishment_logs")
    moderator = relationship("User", foreign_keys=[moderator_id], back_populates="moderator_logs")
    guild = relationship("Guild", back_populates="punishment_logs")

class UserNote(Base):
    __tablename__ = 'user_notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    admin_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    note = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_notes")
    guild = relationship("Guild", back_populates="user_notes")
    admin = relationship("User", foreign_keys=[admin_id])

class AntiSpamConfig(Base):
    __tablename__ = 'anti_spam_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    channel_id = Column(BigInteger, nullable=True)  # NULL means guild-wide settings
    enabled = Column(Boolean, default=False)
    messages_per_interval = Column(Integer, default=1)
    interval_seconds = Column(Integer, default=3)
    warning_threshold = Column(Integer, default=3)
    mute_duration_minutes = Column(Integer, default=5)
    action = Column(String(10), default='mute')  # 'mute' or 'warn'
    clear_messages_on_mute = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guild = relationship("Guild", back_populates="anti_spam_configs")

class CommandLog(Base):
    __tablename__ = 'command_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    command = Column(String(50), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    channel_id = Column(BigInteger, nullable=False)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="command_logs")
    guild = relationship("Guild", back_populates="command_logs")

class BotLog(Base):
    __tablename__ = 'bot_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(Text, nullable=False)
    important = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)