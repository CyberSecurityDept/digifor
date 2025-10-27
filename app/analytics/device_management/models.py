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
    
    deep_communications = relationship(
        "DeepCommunication",
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


    hash_files = relationship("HashFile", back_populates="device", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="device", cascade="all, delete-orphan")
    deep_communications = relationship("DeepCommunication", back_populates="device", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="device", cascade="all, delete-orphan")
    social_media = relationship("SocialMedia", back_populates="device", cascade="all, delete-orphan")

class HashFile(Base):
    __tablename__ = "hash_files"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    name = Column(String, nullable=True)
    
    file_name = Column(String, nullable=True)
    kind = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    path_original = Column(String, nullable=True)
    created_at_original = Column(DateTime, nullable=True)
    modified_at_original = Column(DateTime, nullable=True)
    
    md5_hash = Column(String, nullable=True)
    sha1_hash = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    source_type = Column(String, nullable=True)
    source_tool = Column(String, nullable=True)
    
    file_type = Column(String, nullable=True)
    file_extension = Column(String, nullable=True)
    is_duplicate = Column(String, nullable=True)
    is_suspicious = Column(String, nullable=True)
    
    malware_detection = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    device = relationship("Device", back_populates="hash_files")
    file = relationship("File", back_populates="hash_files")

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

class SocialMedia(Base):
    __tablename__ = "social_media"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=True)
    account_name = Column(Text, nullable=True)
    account_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)

    device = relationship("Device", back_populates="social_media")
    file = relationship("File", back_populates="social_media")

class DeepCommunication(Base):
    __tablename__ = "deep_communications"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    direction = Column(String, nullable=True)
    source = Column(String, nullable=True)
    type = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    sender = Column(Text, nullable=True)
    receiver = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    device = relationship("Device", back_populates="deep_communications")
    file = relationship("File", back_populates="deep_communications")

class Call(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
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

    device = relationship("Device", back_populates="calls")
    file = relationship("File", back_populates="calls")
