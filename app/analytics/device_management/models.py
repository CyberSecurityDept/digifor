from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    type = Column(String, nullable=False)
    tools = Column(String, nullable=False)
    total_size = Column(Integer, nullable=True)
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
    
    messages = relationship(
        "Message",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    calls = relationship(
        "Call",
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

    analytic_devices = relationship(
        "AnalyticDevice",
        back_populates="device",
        cascade="all, delete-orphan"
    )

    analytics = relationship(
        "Analytic",
        secondary="analytic_device",
        viewonly=True
    )

    hash_files = relationship("HashFile", back_populates="device", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="device", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="device", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="device", cascade="all, delete-orphan")
    social_media_accounts = relationship("SocialMediaAccount", back_populates="device", cascade="all, delete-orphan")

class HashFile(Base):
    __tablename__ = "hash_files"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    
    file_hash = Column(String, nullable=True)
    hash_algorithm = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    source_type = Column(String, nullable=True)
    source_tool = Column(String, nullable=True)
    
    file_type = Column(String, nullable=True)
    file_extension = Column(String, nullable=True)
    is_duplicate = Column(String, nullable=True)
    is_suspicious = Column(String, nullable=True)
    
    malware_detection = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)  # Low, Medium, High
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    device = relationship("Device", back_populates="hash_files")

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    display_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    type = Column(String, nullable=True)
    last_time_contacted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    device = relationship("Device", back_populates="contacts")
    file = relationship("File", back_populates="contacts")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    index_row = Column(Integer, index=True)
    direction = Column(String, nullable=True)
    source = Column(String, nullable=True)
    type = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    sender = Column(Text, nullable=True)
    receiver = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    thread_id = Column(String, nullable=True)
    attachment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    device = relationship("Device", back_populates="messages")
    file = relationship("File", back_populates="messages")

class Call(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    index_row = Column(Integer, index=True)
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

    device = relationship("Device", back_populates="calls")
    file = relationship("File", back_populates="calls")
