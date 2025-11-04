from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.utils.timezone import get_indonesia_time
from datetime import datetime

class Analytic(Base):
    __tablename__ = "analytics_history"

    id = Column(Integer, primary_key=True, index=True)
    analytic_name = Column(String, nullable=False)
    method = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_indonesia_time)
    updated_at = Column(DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

    analytic_devices = relationship(
        "AnalyticDevice",
        back_populates="analytic",
        cascade="all, delete-orphan"
    )

    apk_analytics = relationship(
        "ApkAnalytic",
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


class ApkAnalytic(Base):
    __tablename__ = "apk_analytics"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=True)
    description = Column(String, nullable=True)
    status = Column(String, nullable=True)
    malware_scoring = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    analytic_id = Column(Integer, ForeignKey("analytics_history.id"), nullable=False)
    
    analytic = relationship("Analytic", back_populates="apk_analytics")
