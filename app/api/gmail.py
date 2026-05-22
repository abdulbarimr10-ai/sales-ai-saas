from flask import Blueprint, request, jsonify, session, redirect
from app.services.gmail_service import gmail_service
from app.core.exceptions import APIError, UnauthorizedError
from app.core.config import settings
from app.services.session_service import session_service, redis_client
import json
import logging

logger = logging.getLogger(__name__)

gmail_bp = Blueprint('gmail', __name__, url_prefix='/api/gmail')

def get_current_user():
    """Bridge between cookie-based auth and legacy Flask session."""
    # 1. Try new cookie-based session (used by /api/auth/login)
    session_id = request.cookies.get('session_id')
    if session_id:
        session_data = session_service.validate_session(session_id)
        if session_data:
            return session_data['user_id']
    
    # 2. Fallback to legacy Flask session
    user_id = session.get('user_id')
    if not user_id:
        raise UnauthorizedError("Authentication required")
    return user_id

@gmail_bp.route('/connect', methods=['GET'])
def connect():
    user_id = get_current_user()
    try:
        auth_url, state = gmail_service.generate_auth_url()
        
        # Store OAuth state + user_id in Redis (Flask session cookies don't
        # survive the cross-origin AJAX → Google redirect → callback flow)
        oauth_data = json.dumps({'user_id': str(user_id), 'state': state})
        redis_client.setex(f"oauth_state:{state}", 600, oauth_data)  # 10 min TTL
        
        logger.info(f"[GMAIL] OAuth initiated for user {user_id}, state={state[:8]}...")
        return jsonify({"status": "success", "url": auth_url})
    except Exception as e:
        logger.error(f"[GMAIL] Failed to initiate OAuth: {e}")
        raise APIError(f"Failed to initiate connection: {str(e)}", status_code=500)

@gmail_bp.route('/callback', methods=['GET'])
def callback():
    frontend_url = settings.FRONTEND_URL
    incoming_state = request.args.get('state')
    
    logger.info(f"[GMAIL] Callback hit. state={incoming_state[:8] if incoming_state else 'NONE'}...")
    
    if not incoming_state:
        logger.error("[GMAIL] Callback: no state parameter")
        return redirect(f"{frontend_url}/settings?error=state_missing")
    
    # Retrieve OAuth state + user_id from Redis
    oauth_data_raw = redis_client.get(f"oauth_state:{incoming_state}")
    if not oauth_data_raw:
        logger.error("[GMAIL] Callback: state not found in Redis (expired or invalid)")
        return redirect(f"{frontend_url}/settings?error=state_mismatch")
    
    oauth_data = json.loads(oauth_data_raw)
    user_id = oauth_data['user_id']
    
    # Clean up the state from Redis
    redis_client.delete(f"oauth_state:{incoming_state}")
    
    logger.info(f"[GMAIL] Callback: user_id={user_id}, processing token exchange...")
    
    try:
        gmail_service.handle_callback(user_id, request.url)
        logger.info(f"[GMAIL] Gmail connected successfully for user {user_id}")
        return redirect(f"{frontend_url}/settings?gmail=connected")
    except Exception as e:
        import traceback
        logger.exception(f"[GMAIL] Callback error")
        tb = traceback.format_exc()
        return f"<h1>OAuth Callback Failed</h1><pre>{tb}</pre>", 500

@gmail_bp.route('/status', methods=['GET'])
def get_status():
    user_id = get_current_user()
    status = gmail_service.get_status(user_id)
    return jsonify({"status": "success", "data": status})

@gmail_bp.route('/disconnect', methods=['POST'])
def disconnect():
    user_id = get_current_user()
    gmail_service.disconnect(user_id)
    return jsonify({"status": "success", "message": "Gmail disconnected successfully."})

@gmail_bp.route('/test', methods=['POST'])
def test_connection():
    user_id = get_current_user()
    is_valid = gmail_service.test_connection(user_id)
    if is_valid:
        return jsonify({"status": "success", "message": "Gmail connection verified."})
    else:
        return jsonify({"status": "error", "message": "Gmail connection failed. Please reconnect."}), 400
