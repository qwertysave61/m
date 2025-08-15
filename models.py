from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
from typing import Optional

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="uz")
    is_admin = Column(Boolean, default=False)
    balance = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_banned = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)
    
    # Relationships
    bots = relationship("Bot", back_populates="owner")
    payments = relationship("Payment", back_populates="user")
    referrals = relationship("Referral", foreign_keys="[Referral.referred_user_id]", back_populates="referred_user")

class BotTemplate(Base):
    __tablename__ = "bot_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # business, utility, social, professional
    template_code = Column(Text, nullable=False)
    config_schema = Column(JSON, nullable=True)
    creation_fee = Column(Float, nullable=False)
    daily_fee = Column(Float, nullable=False)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    complexity_level = Column(String(50), default="beginner")  # beginner, intermediate, advanced
    estimated_setup_time = Column(Integer, default=5)  # minutes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    bots = relationship("Bot", back_populates="template")

class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("bot_templates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    token = Column(String(500), nullable=False)
    status = Column(String(50), default="created")  # created, running, stopped, suspended, deleted
    config = Column(JSON, nullable=True)
    process_id = Column(Integer, nullable=True)
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    next_payment_date = Column(DateTime(timezone=True), nullable=True)
    total_messages = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    will_be_deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="bots")
    template = relationship("BotTemplate", back_populates="bots")
    payments = relationship("Payment", back_populates="bot")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=True)
    amount = Column(Float, nullable=False)
    payment_type = Column(String(50), nullable=False)  # creation_fee, daily_fee, balance_topup
    status = Column(String(50), default="pending")  # pending, completed, failed, cancelled
    payment_method = Column(String(100), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    bot = relationship("Bot", back_populates="payments")

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_amount = Column(Float, default=0.0)
    status = Column(String(50), default="pending")  # pending, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    referred_user = relationship("User", foreign_keys=[referred_user_id])

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BotAnalytics(Base):
    __tablename__ = "bot_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    uptime_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
