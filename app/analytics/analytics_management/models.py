from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time
from datetime import datetime

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

    # devices = relationship(
    #     "Device",
    #     secondary="analytic_device",
    #     viewonly=True
    # )  # Commented out due to missing relationship

    # apk_analytics = relationship(
    #     "ApkAnalytic",
    #     back_populates="analytic",
    #     cascade="all, delete-orphan"
    # )  # Commented out due to missing relationship

class AnalyticDevice(Base):
    __tablename__ = "analytic_device"

    id = Column(Integer, primary_key=True, index=True)
    analytic_id = Column(Integer, ForeignKey("analytics_history.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    analytic = relationship("Analytic", back_populates="analytic_devices")
    # device = relationship("Device", back_populates="analytic_devices")  # Commented out due to missing relationship


class ApkAnalytic(Base):
    __tablename__ = "apk_analytics"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=True)
    description = Column(String, nullable=True)
    status = Column(String, nullable=True)
    malware_scoring = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # === Foreign Keys ===
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    analytic_id = Column(Integer, ForeignKey("analytics_history.id"), nullable=False)  # 🔹 no unique=True

    # === Relationships ===
    # file = relationship(
    #     "File",
    #     back_populates="apk_analytic",
    #     uselist=False
    # )  # Commented out due to missing relationship

    # analytic = relationship(
    #     "Analytic",
    #     back_populates="apk_analytics"
    # )  # Commented out due to missing relationship