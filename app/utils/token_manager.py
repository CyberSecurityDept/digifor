import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.utils.security import (
    verify_token_with_error_info,
    verify_refresh_token,
    create_token_pair,
    revoke_refresh_token,
    revoke_all_refresh_tokens
)
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self, auto_refresh_threshold: int = 300):
        self.auto_refresh_threshold = auto_refresh_threshold
    
    def check_token_status(self, token: str) -> Dict[str, Any]:
        try:
            from jose import jwt, JWTError
            
            # Decode token tanpa verification untuk check expiration
            payload = jwt.get_unverified_claims(token)
            exp_timestamp = payload.get("exp")
            
            if not exp_timestamp:
                return {
                    "valid": False,
                    "reason": "no_expiration",
                    "needs_refresh": False
                }
            
            # Calculate time until expiration
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            time_until_expiry = (exp_datetime - now).total_seconds()
            
            # Check if token is expired
            if time_until_expiry <= 0:
                return {
                    "valid": False,
                    "reason": "expired",
                    "needs_refresh": True,
                    "expired_at": exp_datetime.isoformat()
                }
            
            # Check if token needs refresh
            needs_refresh = time_until_expiry <= self.auto_refresh_threshold
            
            return {
                "valid": True,
                "needs_refresh": needs_refresh,
                "time_until_expiry": time_until_expiry,
                "expires_at": exp_datetime.isoformat(),
                "username": payload.get("sub"),
                "role": payload.get("role")
            }
            
        except Exception as e:
            logger.warning(f"Error checking token status: {e}")
            return {
                "valid": False,
                "reason": "invalid_token",
                "needs_refresh": False,
                "error": str(e)
            }
    
    def attempt_auto_refresh(self, access_token: str, refresh_token: str, db: Session) -> Dict[str, Any]:
        try:
            # Verify refresh token
            username, role, error_type = verify_refresh_token(refresh_token)
            
            if username is None:
                return {
                    "success": False,
                    "error": f"Invalid refresh token: {error_type}",
                    "error_type": error_type
                }
            
            # Verify user still exists and is active
            user = db.query(User).filter(User.username == username).first()
            if not user or not user.is_active:
                return {
                    "success": False,
                    "error": "User not found or inactive",
                    "error_type": "user_inactive"
                }
            
            # Create new token pair
            new_access_token, new_refresh_token, expires_in = create_token_pair(username, role)
            
            # Revoke old refresh token for security (token rotation)
            revoke_refresh_token(refresh_token)
            
            return {
                "success": True,
                "tokens": {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "expires_in": expires_in,
                    "token_type": "bearer"
                },
                "user_info": {
                    "username": username,
                    "role": role
                }
            }
            
        except Exception as e:
            logger.error(f"Error during auto refresh: {e}")
            return {
                "success": False,
                "error": f"Auto refresh failed: {str(e)}",
                "error_type": "refresh_error"
            }
    
    def validate_and_refresh_if_needed(self, access_token: str, refresh_token: Optional[str], db: Session) -> Dict[str, Any]:
        # Check token status
        token_status = self.check_token_status(access_token)
        
        if not token_status["valid"]:
            if token_status["reason"] == "expired" and refresh_token:
                # Token expired, try to refresh
                refresh_result = self.attempt_auto_refresh(access_token, refresh_token, db)
                return {
                    "token_valid": False,
                    "refresh_attempted": True,
                    "refresh_success": refresh_result["success"],
                    "refresh_result": refresh_result
                }
            else:
                # Token invalid and no refresh possible
                return {
                    "token_valid": False,
                    "refresh_attempted": False,
                    "refresh_success": False,
                    "error": token_status.get("reason", "unknown")
                }
        
        if token_status["needs_refresh"] and refresh_token:
            # Token valid but needs refresh
            refresh_result = self.attempt_auto_refresh(access_token, refresh_token, db)
            return {
                "token_valid": True,
                "refresh_attempted": True,
                "refresh_success": refresh_result["success"],
                "refresh_result": refresh_result,
                "token_status": token_status
            }
        
        # Token is valid and doesn't need refresh
        return {
            "token_valid": True,
            "refresh_attempted": False,
            "refresh_success": False,
            "token_status": token_status
        }
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        try:
            from jose import jwt, JWTError
            
            payload = jwt.get_unverified_claims(token)
            
            return {
                "username": payload.get("sub"),
                "role": payload.get("role"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "jti": payload.get("jti"),
                "token_type": payload.get("type", "access")
            }
            
        except Exception as e:
            logger.warning(f"Error getting token info: {e}")
            return {"error": str(e)}


# Global token manager instance
token_manager = TokenManager()


def get_token_manager() -> TokenManager:
    return token_manager


def create_secure_token_response(tokens: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": 200,
        "message": "Tokens refreshed successfully",
        "data": {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"]
        },
        "security_info": {
            "token_rotation": True,
            "refresh_token_revoked": True,
            "user": user_info
        }
    }
