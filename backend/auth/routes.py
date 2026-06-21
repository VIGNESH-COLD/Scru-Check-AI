"""
Authentication and Authorization API Routes
Handles login, register, user management, and external access
"""

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from auth.jwt_handler import (
    hash_password, 
    verify_password, 
    create_user_token, 
    verify_token,
    get_current_user
)
from auth.rbac import Role, Permission, has_permission, get_permissions, ROLE_DISPLAY_NAMES
from auth.external_access import external_access_manager
from middleware.audit_logger import AuditLogger


# Router for auth endpoints
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
external_router = APIRouter(prefix="/api/external", tags=["External Access"])

# Audit logger
audit_logger = AuditLogger()

# In-memory user store (for development - use database in production)
# Using plain text passwords here - will hash on first access
USERS_STORE = {}

def _init_demo_users():
    """Initialize demo users with hashed passwords (called lazily)."""
    global USERS_STORE
    if USERS_STORE:
        return  # Already initialized
    
    USERS_STORE = {
        "admin": {
            "username": "admin",
            "email": "admin@scrucheck.edu",
            "password_hash": hash_password("admin123"),
            "full_name": "System Administrator",
            "role": "coe",
            "department": "all",
            "is_active": True
        },
        "faculty_demo": {
            "username": "faculty_demo",
            "email": "faculty@scrucheck.edu",
            "password_hash": hash_password("faculty123"),
            "full_name": "Demo Faculty",
            "role": "faculty",
            "department": "CSE",
            "is_active": True
        },
        "hod_demo": {
            "username": "hod_demo",
            "email": "hod@scrucheck.edu",
            "password_hash": hash_password("hod123"),
            "full_name": "Demo HOD",
            "role": "hod",
            "department": "CSE",
            "is_active": True
        }
    }
    print("✅ Demo users initialized")


# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    department: str
    role: Optional[str] = "faculty"


class UserResponse(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    department: str
    permissions: List[str]


class ExternalLinkRequest(BaseModel):
    paper_ids: List[str]
    expires_hours: Optional[int] = 48


class ExternalLinkResponse(BaseModel):
    token: str
    access_url: str
    expires_at: str
    expires_in_hours: int
    paper_count: int


# Authentication endpoints
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Demo accounts:
    - admin / admin123 (COE - full access)
    - hod_demo / hod123 (HOD - department access)
    - faculty_demo / faculty123 (Faculty - basic access)
    """
    # Initialize demo users on first login attempt
    _init_demo_users()
    
    user = USERS_STORE.get(request.username)
    
    if not user:
        await audit_logger.log_login(request.username, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(request.password, user["password_hash"]):
        await audit_logger.log_login(request.username, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Create token
    token = create_user_token(
        username=user["username"],
        role=user["role"],
        department=user["department"],
        full_name=user["full_name"]
    )
    
    await audit_logger.log_login(request.username, success=True)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "role_display": ROLE_DISPLAY_NAMES.get(Role(user["role"]), user["role"]),
            "department": user["department"],
            "permissions": get_permissions(user["role"])
        }
    }


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest, authorization: Optional[str] = Header(None)):
    """
    Register a new user.
    Only COE can create accounts with roles other than faculty.
    """
    # Ensure demo users are initialized before checking for duplicates
    _init_demo_users()

    # Check if user already exists
    if request.username in USERS_STORE:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Verify current user permission for non-faculty roles
    if request.role != "faculty":
        if not authorization:
            raise HTTPException(status_code=401, detail="Admin authentication required for this role")
        
        current_user = await get_current_user(authorization.replace("Bearer ", ""))
        if not current_user or not has_permission(current_user.get("role"), Permission.MANAGE_USERS):
            raise HTTPException(status_code=403, detail="Only COE can create non-faculty accounts")
    
    # Create user
    USERS_STORE[request.username] = {
        "username": request.username,
        "email": request.email,
        "password_hash": hash_password(request.password),
        "full_name": request.full_name,
        "role": request.role,
        "department": request.department,
        "is_active": True
    }
    
    return {
        "username": request.username,
        "email": request.email,
        "full_name": request.full_name,
        "role": request.role,
        "department": request.department,
        "permissions": get_permissions(request.role)
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """Get current authenticated user info."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    current_user = await get_current_user(token)
    
    if not current_user or not current_user.get("authenticated"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "username": current_user["user"],
        "email": USERS_STORE.get(current_user["user"], {}).get("email", ""),
        "full_name": current_user.get("full_name", ""),
        "role": current_user["role"],
        "department": current_user["department"],
        "permissions": get_permissions(current_user["role"])
    }


@router.get("/users", response_model=List[UserResponse])
async def list_users(authorization: Optional[str] = Header(None)):
    """
    List all users (COE only) or department users (HOD).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    current_user = await get_current_user(token)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_role = current_user.get("role", "faculty")
    user_dept = current_user.get("department")
    
    users = []
    for username, user in USERS_STORE.items():
        # COE sees all
        if has_permission(user_role, Permission.MANAGE_USERS):
            users.append({
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "department": user["department"],
                "permissions": get_permissions(user["role"])
            })
        # HOD sees department
        elif has_permission(user_role, Permission.MANAGE_DEPT_USERS) and user["department"] == user_dept:
            users.append({
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "department": user["department"],
                "permissions": get_permissions(user["role"])
            })
    
    return users


# External Access endpoints
@external_router.post("/generate", response_model=ExternalLinkResponse)
async def generate_external_link(
    request: ExternalLinkRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate a temporary access link for external examiners.
    Only HOD and COE can generate links.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    current_user = await get_current_user(token)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not has_permission(current_user.get("role"), Permission.GENERATE_EXTERNAL_LINK):
        raise HTTPException(status_code=403, detail="Only HOD/COE can generate external links")
    
    result = await external_access_manager.create_access_link(
        paper_ids=request.paper_ids,
        created_by=current_user["user"],
        expires_hours=request.expires_hours
    )
    
    return {
        "token": result["token"],
        "access_url": f"/external/view/{result['token']}",
        "expires_at": result["expires_at"],
        "expires_in_hours": result["expires_in_hours"],
        "paper_count": result["paper_count"]
    }


@external_router.get("/verify/{token}")
async def verify_external_token(token: str):
    """Verify an external access token is valid."""
    token_data = await external_access_manager.verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "paper_count": len(token_data.get("paper_ids", [])),
        "expires_at": token_data.get("expires_at")
    }


@external_router.get("/view/{token}")
async def view_external_papers(token: str):
    """
    View papers using external access token.
    Returns read-only paper information and analysis results.
    """
    token_data = await external_access_manager.verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Record access
    await external_access_manager.record_access(token)
    
    # Import RESULTS_STORE dynamically from main to avoid circular import
    from main import RESULTS_STORE
    
    paper_ids = token_data.get("paper_ids", [])
    results = {}
    
    # Identify target papers based on token permissions
    if "all" in paper_ids:
        target_papers = list(RESULTS_STORE.keys())
    else:
        target_papers = [pid for pid in paper_ids if pid in RESULTS_STORE]
        
    for pid in target_papers:
        store_entry = RESULTS_STORE[pid]
        results[pid] = {
            "paper_id": pid,
            "timestamp": store_entry.get("timestamp", datetime.utcnow().isoformat()),
            "overall_status": store_entry["overall_status"],
            "findings": store_entry["criteria"],
            "blooms_distribution": store_entry["blooms"],
            "syllabus_coverage": store_entry["syllabus_coverage"],
            "co_mapping": store_entry["co_mapping"],
            "score": store_entry["score"]
        }
    
    return {
        "papers": paper_ids,
        "access_level": "read_only",
        "expires_at": token_data.get("expires_at"),
        "results": results
    }


@external_router.get("/tokens")
async def list_external_tokens(authorization: Optional[str] = Header(None)):
    """List active external access tokens (HOD/COE only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    current_user = await get_current_user(token)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not has_permission(current_user.get("role"), Permission.GENERATE_EXTERNAL_LINK):
        raise HTTPException(status_code=403, detail="Access denied")
    
    tokens = await external_access_manager.list_active_tokens(
        created_by=current_user["user"] if current_user.get("role") == "hod" else None
    )
    
    return {"tokens": tokens}


@external_router.delete("/revoke/{token}")
async def revoke_external_token(token: str, authorization: Optional[str] = Header(None)):
    """Revoke an external access token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    auth_token = authorization.replace("Bearer ", "")
    current_user = await get_current_user(auth_token)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not has_permission(current_user.get("role"), Permission.GENERATE_EXTERNAL_LINK):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await external_access_manager.revoke_token(token)
    
    return {"revoked": success}
