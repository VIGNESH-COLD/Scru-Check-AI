"""
Role-Based Access Control (RBAC)
Defines roles, permissions, and access control checks
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from functools import wraps


class Role(str, Enum):
    """User roles with hierarchical permissions."""
    FACULTY = "faculty"
    HOD = "hod"
    COE = "coe"
    AUDITOR = "auditor"
    EXTERNAL = "external"  # External examiner (read-only)


class Permission(str, Enum):
    """System permissions."""
    # Paper operations
    UPLOAD_PAPER = "upload_paper"
    VIEW_OWN_PAPERS = "view_own_papers"
    VIEW_DEPT_PAPERS = "view_dept_papers"
    VIEW_ALL_PAPERS = "view_all_papers"
    ANALYZE_PAPER = "analyze_paper"
    
    # Override operations
    OVERRIDE_FINDINGS = "override_findings"
    
    # Report operations
    DOWNLOAD_REPORT = "download_report"
    EXPORT_ALL_REPORTS = "export_all_reports"
    
    # Policy operations
    VIEW_POLICIES = "view_policies"
    EDIT_DEPT_POLICIES = "edit_dept_policies"
    EDIT_ALL_POLICIES = "edit_all_policies"
    
    # User management
    MANAGE_USERS = "manage_users"
    MANAGE_DEPT_USERS = "manage_dept_users"
    
    # External access
    GENERATE_EXTERNAL_LINK = "generate_external_link"
    VIEW_EXTERNAL = "view_external"
    
    # Audit
    VIEW_AUDIT_LOG = "view_audit_log"
    VIEW_ALL_AUDIT = "view_all_audit"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.FACULTY: [
        Permission.UPLOAD_PAPER,
        Permission.VIEW_OWN_PAPERS,
        Permission.ANALYZE_PAPER,
        Permission.OVERRIDE_FINDINGS,
        Permission.DOWNLOAD_REPORT,
    ],
    
    Role.HOD: [
        Permission.UPLOAD_PAPER,
        Permission.VIEW_OWN_PAPERS,
        Permission.VIEW_DEPT_PAPERS,
        Permission.ANALYZE_PAPER,
        Permission.OVERRIDE_FINDINGS,
        Permission.DOWNLOAD_REPORT,
        Permission.VIEW_POLICIES,
        Permission.EDIT_DEPT_POLICIES,
        Permission.MANAGE_DEPT_USERS,
        Permission.GENERATE_EXTERNAL_LINK,
        Permission.VIEW_AUDIT_LOG,
    ],
    
    Role.COE: [
        Permission.UPLOAD_PAPER,
        Permission.VIEW_OWN_PAPERS,
        Permission.VIEW_DEPT_PAPERS,
        Permission.VIEW_ALL_PAPERS,
        Permission.ANALYZE_PAPER,
        Permission.OVERRIDE_FINDINGS,
        Permission.DOWNLOAD_REPORT,
        Permission.EXPORT_ALL_REPORTS,
        Permission.VIEW_POLICIES,
        Permission.EDIT_DEPT_POLICIES,
        Permission.EDIT_ALL_POLICIES,
        Permission.MANAGE_USERS,
        Permission.MANAGE_DEPT_USERS,
        Permission.GENERATE_EXTERNAL_LINK,
        Permission.VIEW_AUDIT_LOG,
        Permission.VIEW_ALL_AUDIT,
    ],
    
    Role.AUDITOR: [
        Permission.VIEW_ALL_PAPERS,
        Permission.DOWNLOAD_REPORT,
        Permission.EXPORT_ALL_REPORTS,
        Permission.VIEW_POLICIES,
        Permission.VIEW_ALL_AUDIT,
    ],
    
    Role.EXTERNAL: [
        Permission.VIEW_EXTERNAL,
        Permission.DOWNLOAD_REPORT,
    ],
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    try:
        role_enum = Role(role.lower())
        return permission in ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return False


def get_permissions(role: str) -> List[str]:
    """Get all permissions for a role."""
    try:
        role_enum = Role(role.lower())
        return [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
    except ValueError:
        return []


def can_access_paper(user_role: str, user_dept: str, paper_dept: str, paper_owner: str, username: str) -> bool:
    """
    Check if user can access a specific paper.
    
    Rules:
    - Faculty: own papers only
    - HOD: own department papers
    - COE: all papers
    - Auditor: all papers (read-only)
    - External: only papers in their token scope
    """
    role = Role(user_role.lower())
    
    if role == Role.FACULTY:
        return paper_owner == username
    elif role == Role.HOD:
        return paper_dept == user_dept or paper_owner == username
    elif role in [Role.COE, Role.AUDITOR]:
        return True
    else:
        return False


def require_permission(permission: Permission):
    """Decorator to require a specific permission for an endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from request
            current_user = kwargs.get("current_user")
            if not current_user:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            user_role = current_user.get("role", "faculty")
            if not has_permission(user_role, permission):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied: {permission.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Role hierarchy for UI display
ROLE_HIERARCHY = {
    Role.FACULTY: 1,
    Role.HOD: 2,
    Role.COE: 3,
    Role.AUDITOR: 2,  # Same level as HOD
    Role.EXTERNAL: 0,
}


ROLE_DISPLAY_NAMES = {
    Role.FACULTY: "Faculty",
    Role.HOD: "Head of Department",
    Role.COE: "Controller of Examinations",
    Role.AUDITOR: "Auditor",
    Role.EXTERNAL: "External Examiner",
}
