from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time
from datetime import datetime

class Analytic(Base):
    __tablename__ = "analytics_history"

    id = Column(Integer, primary_key=True, index=True)
    analytic_name = Column(String(255), nullable=False)
    method = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    analytic_devices = relationship(
        "AnalyticDevice",
        back_populates="analytic",
        cascade="all, delete-orphan"
    )

    analytic_files = relationship(
        "AnalyticFile",
        back_populates="analytic",
        cascade="all, delete-orphan"
    )

class AnalyticDevice(Base):
    __tablename__ = "analytic_device"

    id = Column(Integer, primary_key=True, index=True)
    analytic_id = Column(Integer, ForeignKey("analytics_history.id", ondelete="CASCADE"), nullable=False)
    device_ids = Column(ARRAY(Integer), nullable=False)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    analytic = relationship("Analytic", back_populates="analytic_devices")

class AnalyticFile(Base):
    __tablename__ = "analytic_files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    analytic_id = Column(Integer, ForeignKey("analytics_history.id"), nullable=False)

    status = Column(String(50), default="pending")
    scoring = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    file = relationship("File", back_populates="analytic_files")
    analytic = relationship("Analytic", back_populates="analytic_files")

    apk_analytics = relationship(
        "ApkAnalytic",
        back_populates="analytic_file",
        cascade="all, delete-orphan"
    )

class ApkAnalytic(Base):
    __tablename__ = "apk_analytics"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    malware_scoring = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analytic_file_id = Column(Integer, ForeignKey("analytic_files.id"), nullable=False)

    analytic_file = relationship("AnalyticFile", back_populates="apk_analytics")
