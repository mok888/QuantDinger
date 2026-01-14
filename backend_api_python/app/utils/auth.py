"""
Authentication Utilities

JWT token generation, verification, and middleware decorators.
Supports multi-user authentication with role-based access control.
"""
import jwt
import datetime
import os
from functools import wraps
from flask import request, jsonify, g
from app.config.settings import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_token(user_id: int, username: str, role: str = 'user') -> str:
    """
    Generate JWT token with user information.
    
    Args:
        user_id: User ID
        username: Username
        role: User role (admin/manager/user/viewer)
    
    Returns:
        JWT token string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow(),
            'sub': username,
            'user_id': user_id,
            'role': role,
        }
        return jwt.encode(
            payload,
            Config.SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        return None


def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload.
    
    Args:
        token: JWT token string
    
    Returns:
        Token payload dict or None if invalid
    """
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token: {e}")
        return None


def get_current_user_id() -> int:
    """Get current user ID from flask.g context"""
    return getattr(g, 'user_id', None)


def get_current_user_role() -> str:
    """Get current user role from flask.g context"""
    return getattr(g, 'user_role', 'user')


def login_required(f):
    """
    Decorator that enforces Bearer token auth.
    
    Sets g.user, g.user_id, g.user_role on successful auth.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Read token from Authorization: Bearer <token>
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'code': 401, 'msg': 'Token missing', 'data': None}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'msg': 'Token invalid or expired', 'data': None}), 401
        
        # Store user info in flask.g
        g.user = payload.get('sub')
        g.user_id = payload.get('user_id')
        g.user_role = payload.get('role', 'user')
        
        return f(*args, **kwargs)
        
    return decorated


def admin_required(f):
    """
    Decorator that requires admin role.
    Must be used after @login_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        role = getattr(g, 'user_role', None)
        if role != 'admin':
            return jsonify({'code': 403, 'msg': 'Admin access required', 'data': None}), 403
        return f(*args, **kwargs)
    return decorated


def manager_required(f):
    """
    Decorator that requires manager or admin role.
    Must be used after @login_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        role = getattr(g, 'user_role', None)
        if role not in ('admin', 'manager'):
            return jsonify({'code': 403, 'msg': 'Manager access required', 'data': None}), 403
        return f(*args, **kwargs)
    return decorated


def permission_required(permission: str):
    """
    Decorator factory that checks for a specific permission.
    Must be used after @login_required.
    
    Usage:
        @login_required
        @permission_required('strategy')
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            role = getattr(g, 'user_role', 'user')
            
            # Import here to avoid circular import
            from app.services.user_service import get_user_service
            permissions = get_user_service().get_user_permissions(role)
            
            if permission not in permissions:
                return jsonify({
                    'code': 403, 
                    'msg': f'Permission denied: {permission}', 
                    'data': None
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# Legacy compatibility: single-user mode fallback
def _is_single_user_mode() -> bool:
    """Check if system is in single-user (legacy) mode"""
    return os.getenv('SINGLE_USER_MODE', 'false').lower() == 'true'


def authenticate_legacy(username: str, password: str) -> dict:
    """
    Legacy single-user authentication (for backward compatibility).
    Uses ADMIN_USER and ADMIN_PASSWORD from environment.
    """
    if username == Config.ADMIN_USER and password == Config.ADMIN_PASSWORD:
        return {
            'user_id': 1,
            'username': username,
            'role': 'admin',
            'nickname': 'Admin',
        }
    return None
