"""
Auth Module
JWT authentication, RBAC, and external access management
"""

from .jwt_handler import (
    create_access_token,
    verify_token,
    get_current_user,
    hash_password,
    verify_password,
    create_user_token
)

from .rbac import (
    Role,
    Permission,
    ROLE_PERMISSIONS,
    has_permission,
    get_permissions,
    can_access_paper,
    require_permission
)

from .external_access import external_access_manager
