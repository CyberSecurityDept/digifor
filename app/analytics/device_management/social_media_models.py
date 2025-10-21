from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

def get_indonesia_time():
    indonesia_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(indonesia_tz)

class SocialMediaAccount(Base):
    __tablename__ = "social_media_accounts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    
    platform = Column(String, nullable=False)
    username = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    profile_url = Column(String, nullable=True)
    
    following_count = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)
    
    is_verified = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
    last_activity = Column(DateTime, nullable=True)
    
    device = relationship("Device", back_populates="social_media_accounts")

class SocialMediaFollower(Base):
    __tablename__ = "social_media_followers"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_media_accounts.id"), nullable=False)
    
    follower_username = Column(String, nullable=False)
    follower_display_name = Column(String, nullable=True)
    follower_user_id = Column(String, nullable=True)
    follower_profile_url = Column(String, nullable=True)
    
    relationship_type = Column(String, nullable=False)
    
    is_verified = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
    
    account = relationship("SocialMediaAccount")

class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_media_accounts.id"), nullable=False)
    
    post_id = Column(String, nullable=False)
    post_type = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    media_urls = Column(Text, nullable=True)
    
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
    
    location = Column(String, nullable=True)
    hashtags = Column(Text, nullable=True)
    mentions = Column(Text, nullable=True)
    
    account = relationship("SocialMediaAccount")

class SocialMediaChat(Base):
    __tablename__ = "social_media_chats"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_media_accounts.id"), nullable=False)
    
    chat_id = Column(String, nullable=False)
    chat_type = Column(String, nullable=True)
    chat_name = Column(String, nullable=True)
    participants = Column(Text, nullable=True)
    
    total_messages = Column(Integer, default=0)
    sent_messages = Column(Integer, default=0)
    received_messages = Column(Integer, default=0)
    
    first_message_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
    
    account = relationship("SocialMediaAccount")

class SocialMediaMessage(Base):
    __tablename__ = "social_media_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("social_media_chats.id"), nullable=False)

    message_id = Column(String, nullable=False)
    sender_username = Column(String, nullable=True)
    sender_display_name = Column(String, nullable=True)
    receiver_username = Column(String, nullable=True)
    receiver_display_name = Column(String, nullable=True)
    
    message_type = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    media_urls = Column(Text, nullable=True)
    
    direction = Column(String, nullable=True)
    is_forwarded = Column(Boolean, default=False)
    is_reply = Column(Boolean, default=False)
    reply_to_message_id = Column(String, nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
    
    chat = relationship("SocialMediaChat")
