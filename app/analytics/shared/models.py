# Import all models for backward compatibility
from app.analytics.analytics_management.models import Analytic, AnalyticDevice
from app.analytics.device_management.models import (
    File, Device, HashFile, Contact, Call, SocialMedia, ChatMessage
)

# Export all models
__all__ = [
    "Analytic",
    "AnalyticDevice", 
    "File",
    "Device",
    "HashFile",
    "Contact",
    "Call",
    "SocialMedia",
    "ChatMessage"
]
