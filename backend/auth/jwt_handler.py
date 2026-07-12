"""
JWT Handler and Authentication Service
Handles JWT tokens, password hashing, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import sys

try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False

try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
EXTERNAL_TOKEN_EXPIRE_HOURS = 48

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if PASSLIB_AVAILABLE else None


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    import hashlib
    try:
        if pwd_context:
            return pwd_context.hash(password)
    except Exception as e:
        print(f"⚠️ bcrypt error: {e}, using SHA256 fallback")
    # Fallback (for development)
    return "sha256:" + hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    import hashlib
    
    # Check if it's a SHA256 fallback hash
    if hashed_password.startswith("sha256:"):
        expected = "sha256:" + hashlib.sha256(plain_password.encode()).hexdigest()
        return expected == hashed_password
    
    # Use bcrypt
    try:
        if pwd_context:
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"⚠️ bcrypt verify error: {e}")
    
    return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if not JOSE_AVAILABLE:
        return "jwt-not-available"
    
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    if not JOSE_AVAILABLE:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(token: str = None) -> Optional[Dict[str, Any]]:
    """Get current user from token. Returns None if no token or invalid token."""
    if not token:
        return None

    payload = verify_token(token)
    if payload:
        return {
            "user": payload.get("sub"),
            "role": payload.get("role", "faculty"),
            "department": payload.get("department", "general"),
            "full_name": payload.get("full_name", ""),
            "authenticated": True
        }
    return None


def create_user_token(username: str, role: str, department: str, full_name: str = "") -> str:
    """Create a JWT token for an authenticated user."""
    return create_access_token({
        "sub": username,
        "role": role,
        "department": department,
        "full_name": full_name
    })


def decode_token_data(token: str) -> Optional[Dict[str, Any]]:
    """Decode token and return user data without verification (for display)."""
    if not JOSE_AVAILABLE:
        return None
    
    try:
        # Decode without verification to get claims
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        return {
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "department": payload.get("department"),
            "expires": payload.get("exp"),
            "issued": payload.get("iat")
        }
    except JWTError:
        return None
