import secrets
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory session storage (in production, use Redis or database)
active_sessions: Dict[str, Dict[str, Any]] = {}
refresh_tokens: Dict[str, Dict[str, Any]] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token_legacy(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    # Use longer expiration time to avoid timezone issues
    delta = timedelta(hours=24)  # Token expires in 24 hours
    now = datetime.utcnow()
    expires = now + delta
    
    # Use integer timestamps to avoid timezone issues
    exp = int(expires.timestamp())
    
    encoded_jwt = jwt.encode(
        {"exp": exp, "sub": email}, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        # Allow clock skew of 60 seconds to handle timezone issues
        decoded_token = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm],
            options={"verify_exp": True, "leeway": 60}
        )
        email = decoded_token.get("sub")
        return email
    except JWTError as e:
        print(f"DEBUG: JWT Error: {e}")
        return None


def validate_password_strength(password: str) -> Dict[str, Any]:
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords
    common_passwords = [
        "password", "123456", "admin", "qwerty", "letmein",
        "welcome", "monkey", "1234567890", "password123"
    ]
    
    if password.lower() in common_passwords:
        errors.append("Password is too common, please choose a stronger password")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength": calculate_password_strength(password)
    }


def calculate_password_strength(password: str) -> str:
    score = 0
    
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    if len(password) >= 16:
        score += 1
    
    if score <= 2:
        return "weak"
    elif score <= 4:
        return "medium"
    elif score <= 6:
        return "strong"
    else:
        return "very_strong"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    jti = secrets.token_urlsafe(16)  # JWT ID for session tracking
    to_encode.update({
        "exp": expire, 
        "iat": datetime.utcnow(),
        "jti": jti
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    # Store session info
    active_sessions[jti] = {
        "user_id": data.get("sub"),
        "username": data.get("sub"),
        "role": data.get("role", "investigator"),
        "login_time": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "expires_at": expire,
        "is_active": True
    }
    
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        
        if username is None or jti is None:
            return None
        
        # Check if session is still active
        if jti in active_sessions:
            session = active_sessions[jti]
            if session["is_active"] and session["expires_at"] > datetime.utcnow():
                # Update last activity
                session["last_activity"] = datetime.utcnow()
                return username
            else:
                # Session expired or inactive
                del active_sessions[jti]
                return None
        
        return None
    except JWTError:
        return None


def verify_token_with_error_info(token: str) -> tuple[Optional[str], Optional[str]]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        
        if username is None or jti is None:
            return None, "invalid_token"
        
        # Check if session exists
        if jti not in active_sessions:
            return None, "session_not_found"
        
        session = active_sessions[jti]
        
        # Check if session is active
        if not session["is_active"]:
            del active_sessions[jti]
            return None, "session_inactive"
        
        # Check if session is expired
        if session["expires_at"] <= datetime.utcnow():
            del active_sessions[jti]
            return None, "session_expired"
        
        # Update last activity
        session["last_activity"] = datetime.utcnow()
        return username, None
        
    except JWTError:
        return None, "invalid_token"


def get_session_info(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        jti: str = payload.get("jti")
        
        if jti and jti in active_sessions:
            return active_sessions[jti]
        return None
    except JWTError:
        return None


def revoke_session(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        jti: str = payload.get("jti")
        
        if jti and jti in active_sessions:
            active_sessions[jti]["is_active"] = False
            del active_sessions[jti]
            return True
        return False
    except JWTError:
        return False


def revoke_all_user_sessions(username: str) -> int:
    revoked_count = 0
    sessions_to_remove = []
    
    for session_id, session in active_sessions.items():
        if session["username"] == username:
            sessions_to_remove.append(session_id)
            revoked_count += 1
    
    for session_id in sessions_to_remove:
        del active_sessions[session_id]
    
    return revoked_count


def cleanup_expired_sessions():
    current_time = datetime.utcnow()
    expired_sessions = []
    
    for session_id, session in active_sessions.items():
        if session["expires_at"] < current_time:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del active_sessions[session_id]
    
    return len(expired_sessions)


def get_active_sessions_count() -> int:
    return len(active_sessions)


def hash_file_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def create_refresh_token(username: str, role: str = "investigator") -> str:
    refresh_token_data = {
        "sub": username,
        "role": role,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    }
    
    # Refresh token expires in 7 days
    expires_delta = timedelta(days=7)
    expire = datetime.utcnow() + expires_delta
    
    refresh_token_data.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    refresh_token = jwt.encode(refresh_token_data, settings.secret_key, algorithm=settings.algorithm)
    
    # Store refresh token info
    jti = refresh_token_data["jti"]
    refresh_tokens[jti] = {
        "username": username,
        "role": role,
        "created_at": datetime.utcnow(),
        "expires_at": expire,
        "is_active": True,
        "last_used": datetime.utcnow()
    }
    
    return refresh_token


def verify_refresh_token(token: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        role: str = payload.get("role", "investigator")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")
        
        if username is None or jti is None:
            return None, None, "invalid_token"
        
        if token_type != "refresh":
            return None, None, "invalid_token_type"
        
        # Check if refresh token exists
        if jti not in refresh_tokens:
            return None, None, "refresh_token_not_found"
        
        refresh_info = refresh_tokens[jti]
        
        # Check if refresh token is active
        if not refresh_info["is_active"]:
            del refresh_tokens[jti]
            return None, None, "refresh_token_inactive"
        
        # Check if refresh token is expired
        if refresh_info["expires_at"] <= datetime.utcnow():
            del refresh_tokens[jti]
            return None, None, "refresh_token_expired"
        
        # Update last used
        refresh_info["last_used"] = datetime.utcnow()
        
        return username, role, None
        
    except JWTError:
        return None, None, "invalid_token"


def revoke_refresh_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        jti: str = payload.get("jti")
        
        if jti and jti in refresh_tokens:
            refresh_tokens[jti]["is_active"] = False
            del refresh_tokens[jti]
            return True
        return False
    except JWTError:
        return False


def revoke_all_refresh_tokens(username: str) -> int:
    revoked_count = 0
    tokens_to_remove = []
    
    for token_id, token_info in refresh_tokens.items():
        if token_info["username"] == username:
            tokens_to_remove.append(token_id)
            revoked_count += 1
    
    for token_id in tokens_to_remove:
        del refresh_tokens[token_id]
    
    return revoked_count


def cleanup_expired_refresh_tokens():
    current_time = datetime.utcnow()
    expired_tokens = []
    
    for token_id, token_info in refresh_tokens.items():
        if token_info["expires_at"] < current_time:
            expired_tokens.append(token_id)
    
    for token_id in expired_tokens:
        del refresh_tokens[token_id]
    
    return len(expired_tokens)


def get_refresh_tokens_count() -> int:
    return len(refresh_tokens)


def create_token_pair(username: str, role: str = "investigator") -> tuple[str, str, int]:
    # Create access token (30 minutes)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": username, "role": role}, 
        expires_delta=access_token_expires
    )
    
    # Create refresh token (7 days)
    refresh_token = create_refresh_token(username, role)
    
    # Return tokens and expiration time in seconds
    expires_in = int(access_token_expires.total_seconds())
    
    return access_token, refresh_token, expires_in
