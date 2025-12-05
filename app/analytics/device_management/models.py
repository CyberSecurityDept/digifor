from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BigInteger, Index
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    type = Column(String(100), nullable=False)
    tools = Column(String(100), nullable=True)
    method = Column(String(100), nullable=True)
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
    owner_name = Column(Text, nullable=True)
    phone_number = Column(String(50), nullable=True)
    device_name = Column(String(255), nullable=True)
    app_data_size = Column(String(50), nullable=True)
    
    device_type = Column(String(100), nullable=True)
    device_model = Column(String(255), nullable=True)
    os_version = Column(String(100), nullable=True)
    imei = Column(String(50), nullable=True)
    serial_number = Column(String(100), nullable=True)
    
    extraction_tool = Column(String(100), nullable=True)
    extraction_date = Column(DateTime, nullable=True)
    extraction_method = Column(String(100), nullable=True)
    
    is_encrypted = Column(String(20), nullable=True)
    encryption_type = Column(String(100), nullable=True)
    is_rooted = Column(String(20), nullable=True)
    is_jailbroken = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="devices")

class HashFile(Base):
    __tablename__ = "hash_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file_name = Column(Text, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    path_original = Column(Text, nullable=True)
    created_at_original = Column(DateTime, nullable=True)
    modified_at_original = Column(DateTime, nullable=True)
    
    md5_hash = Column(String(32), nullable=True)
    sha1_hash = Column(String(40), nullable=True)
    algorithm = Column(String(50), nullable=True)
    
    source_tool = Column(String(100), nullable=True)
    
    file_type = Column(String(100), nullable=True)
    
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
    display_name = Column(Text, nullable=True)
    phone_number = Column(String(50), nullable=True)
    type = Column(String(100), nullable=True)
    last_time_contacted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="contacts")

class SocialMedia(Base):
    __tablename__ = "social_media"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    type = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    phone_number = Column(String(50), nullable=True)
    full_name = Column(Text, nullable=True)
    account_name = Column(Text, nullable=True)
    whatsapp_id = Column(String(255), nullable=True)
    telegram_id = Column(String(255), nullable=True)
    instagram_id = Column(String(255), nullable=True)
    X_id = Column(String(255), nullable=True)
    facebook_id = Column(String(255), nullable=True)
    tiktok_id = Column(String(255), nullable=True)
    location = Column(Text, nullable=True)
    sheet_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="social_media")


class Call(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    direction = Column(String(50), nullable=True)
    source = Column(String(100), nullable=True)
    type = Column(String(100), nullable=True)
    timestamp = Column(String(100), nullable=True)
    duration = Column(String(50), nullable=True)
    caller = Column(Text, nullable=True)
    receiver = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    thread_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="calls")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    platform = Column(String(100), nullable=False)
    message_text = Column(Text, nullable=True)
    account_name = Column(String(255), nullable=True)
    group_name = Column(Text, nullable=True)
    group_id = Column(String(255), nullable=True)
    from_name = Column(Text, nullable=True)
    sender_number = Column(String(50), nullable=True)
    to_name = Column(Text, nullable=True)
    recipient_number = Column(String(50), nullable=True)
    timestamp = Column(String(100), nullable=True)
    thread_id = Column(String(255), nullable=True)
    chat_id = Column(String(255), nullable=True)
    message_id = Column(String(255), nullable=True)
    message_type = Column(String(100), nullable=True) 
    chat_type = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True)
    direction = Column(String(50), nullable=True)
    source_tool = Column(String(100), nullable=True)
    sheet_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    file = relationship("File", back_populates="chat_messages")
