from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time

class Analytic(Base):
    __tablename__ = "analytics_history"

    id = Column(Integer, primary_key=True, index=True)
    analytic_name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    method = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

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
    analytic_id = Column(Integer, ForeignKey("analytics_history.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    analytic = relationship("Analytic", back_populates="analytic_devices")
    device = relationship("Device", back_populates="analytic_devices")
