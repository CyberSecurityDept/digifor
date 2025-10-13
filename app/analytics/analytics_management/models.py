from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Analytic(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    analytic_name = Column(String, nullable=False)
    type = Column(String, nullable=True)
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

class AnalyticDevice(Base):
    __tablename__ = "analytic_device"

    id = Column(Integer, primary_key=True, index=True)
    analytic_id = Column(Integer, ForeignKey("analytics.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    analytic = relationship("Analytic", back_populates="analytic_devices")
    device = relationship("Device", back_populates="analytic_devices")
