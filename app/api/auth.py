from flask import Blueprint, request, jsonify, make_response
from app.models.auth import UserRegisterRequest, UserLoginRequest, ChangePasswordRequest, PasswordResetRequest, PasswordResetConfirmRequest
from app.services.auth_service import auth_service
from app.services.session_service import session_service
from app.services.email_verification_service import email_verification_service, password_reset_service
from pydantic import ValidationError
from app.core.exceptions import APIError, UnauthorizedError
from app.core.config import settings
import functools
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Secure cookie settings
COOKIE_NAME = "session_id"
COOKIE_SAMESITE = settings.SESSION_COOKIE_SAMESITE
if COOKIE_SAMESITE and COOKIE_SAMESITE.lower() == "none":
    COOKIE_SECURE = True
else:
    COOKIE_SECURE = settings.SESSION_COOKIE_SECURE if settings.SESSION_COOKIE_SECURE is not None else (settings.ENV == "production")
COOKIE_HTTPONLY = settings.SESSION_COOKIE_HTTPONLY

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        session_id = request.cookies.get(COOKIE_NAME)
        if not session_id:
            raise UnauthorizedError("Authentication required")
            
        session_data = session_service.validate_session(session_id)
        if not session_data:
            raise UnauthorizedError("Session expired or invalid")
            
        request.user_id = session_data['user_id']
        request.session_id = session_id
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    logger.info(f"[AUTH] POST /api/auth/register hit | method={request.method}")
    
    try:
        data = request.get_json(silent=True)
        if not data:
            logger.warning("[AUTH] Register: No JSON body received")
            raise APIError("Request body must be JSON", status_code=400)
        
        logger.info(f"[AUTH] Register payload received for email: {data.get('email', 'MISSING')}")
        
        validated = UserRegisterRequest(**data)
    except ValidationError as e:
        logger.warning(f"[AUTH] Register validation failed: {e}")
        raise APIError(str(e), status_code=400)
        
    user_id = auth_service.register_user(validated)
    email_verification_service.create_verification(user_id, validated.email)
    
    logger.info(f"[AUTH] Register SUCCESS for user_id={user_id}")
    return jsonify({"status": "success", "message": "Registration successful. Please verify your email."})

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    logger.info(f"[AUTH] POST /api/auth/login hit | method={request.method}")
    
    try:
        data = request.get_json(silent=True)
        if not data:
            logger.warning("[AUTH] Login: No JSON body received")
            raise APIError("Request body must be JSON", status_code=400)
        
        logger.info(f"[AUTH] Login attempt for email: {data.get('email', 'MISSING')}")
        
        validated = UserLoginRequest(**data)
    except ValidationError as e:
        logger.warning(f"[AUTH] Login validation failed: {e}")
        raise APIError(str(e), status_code=400)
        
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr
    
    user_id, session_id = auth_service.login_user(validated, user_agent, ip_address)
    
    logger.info(f"[AUTH] Login SUCCESS for user_id={user_id}")
    
    response = make_response(jsonify({"status": "success", "message": "Login successful"}))
    response.set_cookie(
        COOKIE_NAME, 
        session_id, 
        httponly=COOKIE_HTTPONLY, 
        secure=COOKIE_SECURE, 
        samesite=COOKIE_SAMESITE,
        max_age=86400 * 7  # 7 days
    )
    return response

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
@require_auth
def logout():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    logger.info(f"[AUTH] POST /api/auth/logout hit | user_id={request.user_id}")
    session_service.revoke_session(request.session_id)
    response = make_response(jsonify({"status": "success", "message": "Logged out"}))
    response.delete_cookie(COOKIE_NAME)
    return response

@auth_bp.route('/logout-all', methods=['POST', 'OPTIONS'])
@require_auth
def logout_all():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    logger.info(f"[AUTH] POST /api/auth/logout-all hit | user_id={request.user_id}")
    session_service.revoke_all_sessions(request.user_id)
    response = make_response(jsonify({"status": "success", "message": "Logged out of all devices"}))
    response.delete_cookie(COOKIE_NAME)
    return response

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    logger.info(f"[AUTH] GET /api/auth/me hit | user_id={request.user_id}")
    return jsonify({"status": "success", "user_id": request.user_id})

@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_sessions():
    sessions = session_service.get_active_sessions(request.user_id)
    return jsonify({"status": "success", "data": sessions})

@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def revoke_specific_session(session_id):
    # Only allow revoking own sessions
    sessions = session_service.get_active_sessions(request.user_id)
    if any(s['session_id'] == session_id for s in sessions):
        session_service.revoke_session(session_id)
        return jsonify({"status": "success"})
    raise UnauthorizedError("Cannot revoke this session")

@auth_bp.route('/request-password-reset', methods=['POST', 'OPTIONS'])
def request_password_reset():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    logger.info("[AUTH] POST /api/auth/request-password-reset hit")
    try:
        data = request.get_json(silent=True)
        if not data:
            raise APIError("Request body must be JSON", status_code=400)
        validated = PasswordResetRequest(**data)
    except ValidationError as e:
        raise APIError(str(e), status_code=400)
        
    password_reset_service.create_reset(validated.email)
    return jsonify({"status": "success", "message": "If that email exists, a reset link has been sent."})

@auth_bp.route('/reset-password', methods=['POST', 'OPTIONS'])
def reset_password():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    logger.info("[AUTH] POST /api/auth/reset-password hit")
    try:
        data = request.get_json(silent=True)
        if not data:
            raise APIError("Request body must be JSON", status_code=400)
        validated = PasswordResetConfirmRequest(**data)
    except ValidationError as e:
        raise APIError(str(e), status_code=400)
        
    user_id = data.get('uid')
    if not user_id:
        raise APIError("Missing user ID", status_code=400)
        
    password_reset_service.verify_and_reset(int(user_id), validated.token, validated.new_password)
    return jsonify({"status": "success", "message": "Password reset successful."})

@auth_bp.route('/verify-email', methods=['POST', 'OPTIONS'])
def verify_email():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    logger.info("[AUTH] POST /api/auth/verify-email hit")
    data = request.get_json(silent=True)
    if not data:
        raise APIError("Request body must be JSON", status_code=400)
    
    token = data.get('token')
    user_id = data.get('uid')
    
    if not token or not user_id:
        raise APIError("Missing parameters", status_code=400)
        
    email_verification_service.verify_email(int(user_id), token)
    return jsonify({"status": "success", "message": "Email verified."})
