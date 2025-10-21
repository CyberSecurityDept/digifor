# Import all models for backward compatibility
from app.analytics.analytics_management.models import Analytic, AnalyticDevice
from app.analytics.device_management.models import (
    File, Device, HashFile, Contact, Message, Call
)
from app.analytics.device_management.social_media_models import (
    SocialMediaAccount, SocialMediaFollower, SocialMediaPost, 
    SocialMediaChat, SocialMediaMessage
)

# Export all models
__all__ = [
    "Analytic",
    "AnalyticDevice", 
    "File",
    "Device",
    "HashFile",
    "Contact",
    "Message",
    "Call",
    "SocialMediaAccount",
    "SocialMediaFollower", 
    "SocialMediaPost",
    "SocialMediaChat",
    "SocialMediaMessage"
]
