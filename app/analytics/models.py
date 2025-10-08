from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    analytic_name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    devices = relationship("Device", back_populates="group", cascade="all, delete-orphan")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    instagram = Column(String, nullable=True)
    whatsapp  = Column(String, nullable=True)
    x         = Column(String, nullable=True)
    facebook  = Column(String, nullable=True)
    tiktok    = Column(String, nullable=True)
    telegram  = Column(String, nullable=True)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    group = relationship("Group", back_populates="devices")
    created_at = Column(DateTime, default=datetime.utcnow)

    # relasi ke file
    files = relationship("HashFile", back_populates="device", cascade="all, delete-orphan")

    contacts = relationship("Contact", back_populates="device", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="device", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="device", cascade="all, delete-orphan")


class HashFile(Base):
    __tablename__ = "hashfiles"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="files")


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    index_row = Column(Integer, index=True)
    type = Column(String, nullable=True)
    source = Column(Text, nullable=True)
    contact = Column(Text, nullable=True)
    messages = Column(Text, nullable=True)
    phones_emails = Column(Text, nullable=True)
    internet = Column(Text, nullable=True)
    other = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="contacts")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="messages")


class Call(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="calls")
