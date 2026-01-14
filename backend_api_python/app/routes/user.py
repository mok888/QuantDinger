"""
User Management API Routes

Provides endpoints for user CRUD operations, role management, etc.
Only accessible by admin users.
"""
from flask import Blueprint, request, jsonify, g
from app.services.user_service import get_user_service
from app.utils.auth import login_required, admin_required
from app.utils.logger import get_logger

logger = get_logger(__name__)

user_bp = Blueprint('user_manage', __name__)


@user_bp.route('/list', methods=['GET'])
@login_required
@admin_required
def list_users():
    """
    List all users (admin only).
    
    Query params:
        page: int (default 1)
        page_size: int (default 20, max 100)
        search: str (optional, search by username/email/nickname)
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        page_size = min(100, max(1, page_size))
        
        result = get_user_service().list_users(page=page, page_size=page_size, search=search)
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"list_users failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/detail', methods=['GET'])
@login_required
@admin_required
def get_user_detail():
    """Get user detail by ID (admin only)"""
    try:
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user id', 'data': None}), 400
        
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 0, 'msg': 'User not found', 'data': None}), 404
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': user
        })
    except Exception as e:
        logger.error(f"get_user_detail failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    """
    Create a new user (admin only).
    
    Request body:
        username: str (required)
        password: str (required)
        email: str (optional)
        nickname: str (optional)
        role: str (optional, default 'user')
    """
    try:
        data = request.get_json() or {}
        
        user_id = get_user_service().create_user(data)
        
        return jsonify({
            'code': 1,
            'msg': 'User created successfully',
            'data': {'id': user_id}
        })
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"create_user failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/update', methods=['PUT'])
@login_required
@admin_required
def update_user():
    """
    Update user information (admin only).
    
    Query params:
        id: int (required)
    
    Request body:
        email: str (optional)
        nickname: str (optional)
        role: str (optional)
        status: str (optional)
    """
    try:
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user id', 'data': None}), 400
        
        data = request.get_json() or {}
        
        success = get_user_service().update_user(user_id, data)
        
        if success:
            return jsonify({'code': 1, 'msg': 'User updated successfully', 'data': None})
        else:
            return jsonify({'code': 0, 'msg': 'Update failed', 'data': None}), 400
    except Exception as e:
        logger.error(f"update_user failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_user():
    """Delete a user (admin only)"""
    try:
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user id', 'data': None}), 400
        
        # Prevent deleting self
        if hasattr(g, 'user_id') and g.user_id == user_id:
            return jsonify({'code': 0, 'msg': 'Cannot delete yourself', 'data': None}), 400
        
        success = get_user_service().delete_user(user_id)
        
        if success:
            return jsonify({'code': 1, 'msg': 'User deleted successfully', 'data': None})
        else:
            return jsonify({'code': 0, 'msg': 'Delete failed', 'data': None}), 400
    except Exception as e:
        logger.error(f"delete_user failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password():
    """
    Reset a user's password (admin only).
    
    Request body:
        user_id: int (required)
        new_password: str (required)
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        new_password = data.get('new_password', '')
        
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user_id', 'data': None}), 400
        
        if len(new_password) < 6:
            return jsonify({'code': 0, 'msg': 'Password must be at least 6 characters', 'data': None}), 400
        
        success = get_user_service().reset_password(user_id, new_password)
        
        if success:
            return jsonify({'code': 1, 'msg': 'Password reset successfully', 'data': None})
        else:
            return jsonify({'code': 0, 'msg': 'Reset failed', 'data': None}), 400
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"reset_user_password failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/roles', methods=['GET'])
@login_required
@admin_required
def get_roles():
    """Get available roles and their permissions"""
    service = get_user_service()
    
    roles = []
    for role in service.ROLES:
        roles.append({
            'id': role,
            'name': role.capitalize(),
            'permissions': service.get_user_permissions(role)
        })
    
    return jsonify({
        'code': 1,
        'msg': 'success',
        'data': {'roles': roles}
    })


# ==================== Billing Management (Admin) ====================

@user_bp.route('/set-credits', methods=['POST'])
@login_required
@admin_required
def set_user_credits():
    """
    Set user credits (admin only).
    
    Request body:
        user_id: int (required)
        credits: int (required)
        remark: str (optional)
    """
    try:
        from app.services.billing_service import get_billing_service
        
        data = request.get_json() or {}
        user_id = data.get('user_id')
        credits = data.get('credits')
        remark = data.get('remark', '')
        
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user_id', 'data': None}), 400
        
        if credits is None or credits < 0:
            return jsonify({'code': 0, 'msg': 'Credits must be a non-negative number', 'data': None}), 400
        
        operator_id = getattr(g, 'user_id', None)
        success, result = get_billing_service().set_credits(user_id, int(credits), remark, operator_id)
        
        if success:
            return jsonify({'code': 1, 'msg': 'Credits updated successfully', 'data': {'credits': result}})
        else:
            return jsonify({'code': 0, 'msg': result, 'data': None}), 400
    except Exception as e:
        logger.error(f"set_user_credits failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/set-vip', methods=['POST'])
@login_required
@admin_required
def set_user_vip():
    """
    Set user VIP status (admin only).
    
    Request body:
        user_id: int (required)
        vip_days: int (optional, 0 to cancel VIP, positive number to grant VIP for days)
        vip_expires_at: str (optional, ISO format datetime, overrides vip_days if provided)
        remark: str (optional)
    """
    try:
        from datetime import datetime, timedelta, timezone
        from app.services.billing_service import get_billing_service
        
        data = request.get_json() or {}
        user_id = data.get('user_id')
        vip_days = data.get('vip_days')
        vip_expires_at_str = data.get('vip_expires_at')
        remark = data.get('remark', '')
        
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user_id', 'data': None}), 400
        
        # Calculate expires_at
        expires_at = None
        if vip_expires_at_str:
            try:
                expires_at = datetime.fromisoformat(vip_expires_at_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'code': 0, 'msg': 'Invalid vip_expires_at format', 'data': None}), 400
        elif vip_days is not None:
            if vip_days > 0:
                expires_at = datetime.now(timezone.utc) + timedelta(days=vip_days)
            else:
                expires_at = None  # Cancel VIP
        else:
            return jsonify({'code': 0, 'msg': 'Provide vip_days or vip_expires_at', 'data': None}), 400
        
        operator_id = getattr(g, 'user_id', None)
        success, result = get_billing_service().set_vip(user_id, expires_at, remark, operator_id)
        
        if success:
            return jsonify({
                'code': 1, 
                'msg': 'VIP status updated successfully', 
                'data': {'vip_expires_at': expires_at.isoformat() if expires_at else None}
            })
        else:
            return jsonify({'code': 0, 'msg': result, 'data': None}), 400
    except Exception as e:
        logger.error(f"set_user_vip failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/credits-log', methods=['GET'])
@login_required
@admin_required
def get_user_credits_log():
    """
    Get user credits log (admin only).
    
    Query params:
        user_id: int (required)
        page: int (default 1)
        page_size: int (default 20)
    """
    try:
        from app.services.billing_service import get_billing_service
        
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user_id', 'data': None}), 400
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(100, max(1, page_size))
        
        result = get_billing_service().get_credits_log(user_id, page, page_size)
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"get_user_credits_log failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


# Self-service endpoints (accessible by any logged-in user)

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile with billing info"""
    try:
        from app.services.billing_service import get_billing_service
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Not authenticated', 'data': None}), 401
        
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 0, 'msg': 'User not found', 'data': None}), 404
        
        # Add permissions
        user['permissions'] = get_user_service().get_user_permissions(user.get('role', 'user'))
        
        # Add billing info
        billing_info = get_billing_service().get_user_billing_info(user_id)
        user['billing'] = billing_info
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': user
        })
    except Exception as e:
        logger.error(f"get_profile failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/profile/update', methods=['PUT'])
@login_required
def update_profile():
    """
    Update current user's profile (limited fields).
    
    Request body:
        nickname: str (optional)
        avatar: str (optional)
    
    Note: Email cannot be changed after registration (for security).
          Only admin can change user email via User Management.
    """
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Not authenticated', 'data': None}), 401
        
        data = request.get_json() or {}
        
        # Only allow updating certain fields for self-service
        # Email is NOT allowed to be changed (security: bound to account)
        allowed = {}
        for field in ['nickname', 'avatar']:
            if field in data:
                allowed[field] = data[field]
        
        if not allowed:
            return jsonify({'code': 0, 'msg': 'No valid fields to update', 'data': None}), 400
        
        success = get_user_service().update_user(user_id, allowed)
        
        if success:
            return jsonify({'code': 1, 'msg': 'Profile updated successfully', 'data': None})
        else:
            return jsonify({'code': 0, 'msg': 'Update failed', 'data': None}), 400
    except Exception as e:
        logger.error(f"update_profile failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/my-credits-log', methods=['GET'])
@login_required
def get_my_credits_log():
    """
    Get current user's credits log.
    
    Query params:
        page: int (default 1)
        page_size: int (default 20)
    """
    try:
        from app.services.billing_service import get_billing_service
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Not authenticated', 'data': None}), 401
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(100, max(1, page_size))
        
        result = get_billing_service().get_credits_log(user_id, page, page_size)
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"get_my_credits_log failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/my-referrals', methods=['GET'])
@login_required
def get_my_referrals():
    """
    Get list of users referred by current user.
    
    Query params:
        page: int (default 1)
        page_size: int (default 20)
    
    Returns:
        list: Users referred by current user (id, username, nickname, avatar, created_at)
        total: Total count of referrals
        referral_code: Current user's referral code (user ID)
        referral_bonus: Credits earned per referral
        register_bonus: Credits new users get on registration
    """
    try:
        import os
        from app.utils.db import get_db_connection
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Not authenticated', 'data': None}), 401
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(100, max(1, page_size))
        offset = (page - 1) * page_size
        
        with get_db_connection() as db:
            cur = db.cursor()
            
            # Get total count
            cur.execute(
                "SELECT COUNT(*) as cnt FROM qd_users WHERE referred_by = ?",
                (user_id,)
            )
            total = cur.fetchone()['cnt']
            
            # Get referral list
            cur.execute(
                """
                SELECT id, username, nickname, avatar, created_at 
                FROM qd_users 
                WHERE referred_by = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, page_size, offset)
            )
            rows = cur.fetchall()
            cur.close()
            
            referrals = []
            for row in rows:
                referrals.append({
                    'id': row['id'],
                    'username': row['username'],
                    'nickname': row['nickname'],
                    'avatar': row['avatar'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'list': referrals,
                'total': total,
                'page': page,
                'page_size': page_size,
                'referral_code': str(user_id),
                'referral_bonus': int(os.getenv('CREDITS_REFERRAL_BONUS', '0')),
                'register_bonus': int(os.getenv('CREDITS_REGISTER_BONUS', '0'))
            }
        })
    except Exception as e:
        logger.error(f"get_my_referrals failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Change current user's password.
    
    Request body:
        old_password: str (required)
        new_password: str (required)
    """
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Not authenticated', 'data': None}), 401
        
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not new_password:
            return jsonify({'code': 0, 'msg': 'New password required', 'data': None}), 400
        
        if len(new_password) < 6:
            return jsonify({'code': 0, 'msg': 'New password must be at least 6 characters', 'data': None}), 400
        
        # Check if user has a password set
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 0, 'msg': 'User not found', 'data': None}), 404
        
        # Get password_hash to check if user has no password
        from app.utils.db import get_db_connection
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute("SELECT password_hash FROM qd_users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            cur.close()
        
        password_hash = row.get('password_hash', '') if row else ''
        has_password = password_hash and password_hash.strip() != ''
        
        # If user has no password, allow setting password without old password
        if not has_password:
            if not old_password:
                # No old password required for users without password
                success = user_service.reset_password(user_id, new_password)
                if success:
                    return jsonify({'code': 1, 'msg': 'Password set successfully', 'data': None})
                else:
                    return jsonify({'code': 0, 'msg': 'Failed to set password', 'data': None}), 500
            else:
                # If old_password is provided but user has no password, ignore it
                success = user_service.reset_password(user_id, new_password)
                if success:
                    return jsonify({'code': 1, 'msg': 'Password set successfully', 'data': None})
                else:
                    return jsonify({'code': 0, 'msg': 'Failed to set password', 'data': None}), 500
        else:
            # User has existing password, require old password verification
            if not old_password:
                return jsonify({'code': 0, 'msg': 'Old password required', 'data': None}), 400
            
            success = user_service.change_password(user_id, old_password, new_password)
            
            if success:
                return jsonify({'code': 1, 'msg': 'Password changed successfully', 'data': None})
            else:
                return jsonify({'code': 0, 'msg': 'Old password incorrect', 'data': None}), 400
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"change_password failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
