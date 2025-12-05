from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Analytic(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    analytic_name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analytic_devices = relationship(
        "AnalyticDevice",
        back_populates="analytic",
        cascade="all, delete-orphan"
    )

    devices = relationship(
        "Device",
        secondary="analytic_device",
        viewonly=True
    )

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    type = Column(String(100), nullable=False)
    tools = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship(
        "Device",
        back_populates="file",
        uselist=False 
    )
    analytic_files = relationship(
        "AnalyticFile",
        back_populates="file",
        cascade="all, delete-orphan"
    )


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(Text, nullable=True)
    phone_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file = relationship("File", back_populates="device")

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


class AnalyticDevice(Base):
    __tablename__ = "analytic_device"

    id = Column(Integer, primary_key=True, index=True)
    analytic_id = Column(Integer, ForeignKey("analytics.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analytic = relationship("Analytic", back_populates="analytic_devices")
    device = relationship("Device", back_populates="analytic_devices")

class HashFile(Base):
    __tablename__ = "hashfiles"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(Text, nullable=True)
    file_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="hash_files")


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    index_row = Column(Integer, index=True)
    type = Column(String(100), nullable=True)
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
    direction = Column(String(50), nullable=True)
    source = Column(String(100), nullable=True)
    type = Column(String(100), nullable=True)
    timestamp = Column(String(100), nullable=True)
    text = Column(Text, nullable=True)
    sender = Column(Text, nullable=True)
    receiver = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    thread_id = Column(String(255), nullable=True)
    attachment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="messages")


class Call(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    index_row = Column(Integer, index=True)
    direction = Column(String(50), nullable=True)
    source = Column(String(100), nullable=True)
    type = Column(String(100), nullable=True)
    timestamp = Column(String(100), nullable=True)
    duration = Column(String(50), nullable=True)
    caller = Column(Text, nullable=True)
    receiver = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    thread_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="calls")
