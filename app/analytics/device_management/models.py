from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BigInteger, Index
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    type = Column(String, nullable=False)
    tools = Column(String, nullable=True)
    method = Column(String, nullable=True)
    total_size = Column(Integer, nullable=True)
    amount_of_data = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    devices = relationship(
        "Device",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    contacts = relationship(
        "Contact",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    calls = relationship(
        "Call",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    social_media = relationship(
        "SocialMedia",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    hash_files = relationship(
        "HashFile",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    chat_messages = relationship(
        "ChatMessage",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    analytic_files = relationship(
        "AnalyticFile",
        back_populates="file",
        cascade="all, delete-orphan"
    )


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    owner_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    device_name = Column(String, nullable=True)
    app_data_size = Column(String, nullable=True)
    
    device_type = Column(String, nullable=True)
    device_model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    imei = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    
    extraction_tool = Column(String, nullable=True)
    extraction_date = Column(DateTime, nullable=True)
    extraction_method = Column(String, nullable=True)
    
    is_encrypted = Column(String, nullable=True)
    encryption_type = Column(String, nullable=True)
    is_rooted = Column(String, nullable=True)
    is_jailbroken = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="devices")

class HashFile(Base):
    __tablename__ = "hash_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file_name = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    path_original = Column(String, nullable=True)
    created_at_original = Column(DateTime, nullable=True)
    modified_at_original = Column(DateTime, nullable=True)
    
    md5_hash = Column(String, nullable=True)
    sha1_hash = Column(String, nullable=True)
    algorithm = Column(String, nullable=True)
    
    source_tool = Column(String, nullable=True)
    
    file_type = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="hash_files")
    __table_args__ = (
        Index("idx_hash_fileid_md5", "file_id", "md5_hash"),
        Index("idx_hash_fileid_sha1", "file_id", "sha1_hash"),
        Index("idx_hash_tool", "source_tool"),
    )

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    display_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    type = Column(String, nullable=True)
    last_time_contacted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="contacts")

class SocialMedia(Base):
    __tablename__ = "social_media"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    
    type = Column(String, nullable=True)
    source = Column(String, nullable=True)
    
    phone_number = Column(String, nullable=True)
    full_name = Column(Text, nullable=True)
    account_name = Column(Text, nullable=True)
    
    whatsapp_id = Column(String, nullable=True)
    telegram_id = Column(String, nullable=True)
    instagram_id = Column(String, nullable=True)
    X_id = Column(String, nullable=True)
    facebook_id = Column(String, nullable=True)
    tiktok_id = Column(String, nullable=True)
    
    location = Column(Text, nullable=True)
    
    sheet_name = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="social_media")


class Call(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    direction = Column(String, nullable=True)
    source = Column(String, nullable=True)
    type = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    caller = Column(Text, nullable=True)
    receiver = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="calls")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    platform = Column(String, nullable=False)
    message_text = Column(Text, nullable=True)
    account_name = Column(String, nullable=True)
    group_name = Column(String, nullable=True)
    group_id = Column(String, nullable=True)
    from_name = Column(String, nullable=True)
    sender_number = Column(String, nullable=True)
    to_name = Column(String, nullable=True)
    recipient_number = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    thread_id = Column(String, nullable=True)
    chat_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    message_type = Column(String, nullable=True) 
    chat_type = Column(String, nullable=True)
    status = Column(String, nullable=True)
    direction = Column(String, nullable=True)
    source_tool = Column(String, nullable=True)
    sheet_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="chat_messages")
