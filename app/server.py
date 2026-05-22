#server.py
from flask import Flask, request, jsonify, session, send_file, redirect, url_for
from flask_cors import CORS
import os
import json

import database.queries as db
from database.models import init_db

from pipeline.discovery import run_sales_pipeline
from pipeline.audit_flow import execute_universal_audit
from pipeline.outreach_flow import generate_hyper_personalized_email,calculate_lead_roi
from tools.auto_outreach import generate_and_send_email

import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from flask import Blueprint
from dotenv import load_dotenv

load_dotenv()

legacy_bp = Blueprint('legacy', __name__)


def get_current_user_id():
    """Bridge between new cookie-based auth and legacy Flask session.
    
    The new auth system (/api/auth/login) sets a 'session_id' cookie
    that maps to user data in Redis. Legacy routes used session.get('user_id').
    This helper checks both systems so legacy routes work with either login method.
    """
    # 1. Try new session system (cookie → Redis)
    from app.services.session_service import session_service
    session_id = request.cookies.get('session_id')
    if session_id:
        session_data = session_service.validate_session(session_id)
        if session_data:
            return session_data['user_id']
    
    # 2. Fallback to legacy Flask session
    return session.get('user_id')


@legacy_bp.errorhandler(Exception)
def handle_legacy_error(error):
    """Ensure legacy routes always return JSON, never HTML error pages."""
    print(f"[LEGACY] Unhandled error: {error}")
    status_code = getattr(error, 'code', 500)
    return jsonify({
        "status": "error",
        "message": str(error)
    }), status_code



# OAUTH CONFIGURATION
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/userinfo.email', 'openid']
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

def get_google_flow():
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [REDIRECT_URI]
        }
    }
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    return flow

init_db()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("SECRET_KEY")

@legacy_bp.route('/')
def home():
    return jsonify({
        "status": "ok",
        "service": "Sales AI API",
        "version": "1.0"
    })

@legacy_bp.route('/health')
def health():
    return jsonify({
        "status": "healthy"
    })


@legacy_bp.route('/auth/google/login')
def google_login():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"status": "error", "message": "Login required"}), 401

    try:
        flow = get_google_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        session['state'] = state
        return jsonify({"status": "success", "url": authorization_url})
    except Exception as e:
        print(f"Error initiating OAuth: {e}")
        return jsonify({"status": "error", "message": "Server configuration error"}), 500

@legacy_bp.route('/auth/google/callback')
def google_callback():
    user_id = get_current_user_id()
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    if not user_id:
        return redirect(f"{frontend_url}/settings?error=session_lost")

    state = session.get('state')
    
    if state != request.args.get('state'):
        return redirect(f"{frontend_url}/settings?error=state_mismatch")

    try:
        flow = get_google_flow()
        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        email_address = user_info.get('email')
        
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        db.update_gmail_credentials(user_id, json.dumps(creds_dict), email_address)
        return redirect(f"{frontend_url}/settings?gmail=connected")
    except Exception as e:
        print(f"Error processing OAuth callback: {e}")
        return redirect(f"{frontend_url}/settings?error=callback_failed")

@legacy_bp.route('/auth/google/disconnect', methods=['POST'])
def google_disconnect():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"status": "error"}), 401
    
    db.remove_gmail_credentials(user_id)
    return jsonify({"status": "success"})


@legacy_bp.route('/analyze_one', methods=['POST'])
def analyze_one():
    user_id = get_current_user_id() or 1
    if not user_id:
        return jsonify({"status": "error", "message": "Login required"}), 401
    db_id = request.json.get('db_id')
    result = execute_universal_audit(db_id, user_id) 
    return jsonify(result) if result else (jsonify({"status": "error"}), 404)

@legacy_bp.route('/login', methods=['POST'])
def login_route():
    data = request.json
    user_id = db.verify_user(data.get('user'), data.get('pass'))
    if user_id:
        session['user_id'] = user_id
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid Credentials"}), 401

@legacy_bp.route('/signup', methods=['POST'])
def signup_route():
    data = request.json
    success = db.create_user(data.get('user'), data.get('pass'))
    if success:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Username taken"})

@legacy_bp.route('/process', methods=['POST'])
def process():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error"}), 401
    
    data = request.json
    user_input = data.get('command')

    allowed = ["dental clinic", "skin clinic", "physiotherapy clinic", "diagnostic center"]
    if not any(k in user_input.lower() for k in allowed):
        return jsonify({"status": "success", "data": "❌ Only clinics & diagnostic centers allowed."})

    leads = run_sales_pipeline(user_input, user_id) 
    
    if isinstance(leads, str):
        return jsonify({"status": "success", "data": leads})

    saved = []
    for lead in leads:
        before = len(db.get_all_saved_urls(user_id))
        db.save_lead(user_id, lead)
        after = len(db.get_all_saved_urls(user_id))
        if after > before:
            saved.append(lead)

    if not saved:
        return jsonify({"status": "success", "data": "⚠️ No new leads found."})

    fresh = db.get_leads_by_query(user_id, user_input)
    new_names = set([l["name"] for l in saved])
    final = [l for l in fresh if l["name"] in new_names]
    return jsonify({"status": "success", "data": final})

@legacy_bp.route('/generate_email', methods=['POST'])
def generate_email():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error"}), 401
    
    db_id = request.json.get('db_id')
    lead = db.get_lead_by_id(db_id)

    if lead:
        if not lead.get('analysis'):
            return jsonify({"status": "error", "message": "Lead must be analyzed first."}), 400
        email_content = generate_hyper_personalized_email(lead, user_id)
        db.update_lead_field(db_id, "email_draft", email_content)
        return jsonify({"status": "success", "email": email_content})
    return jsonify({"status": "error"})

@legacy_bp.route('/batch_outreach', methods=['POST'])
def batch_outreach():
    user_id = get_current_user_id()
    lead_ids = request.json.get('ids', [])
    search_query = request.json.get('query')
    
    for lead_id in lead_ids:
        lead = db.get_lead_by_id(lead_id)
        if lead and lead.get('analysis'):
            email_content = generate_hyper_personalized_email(lead, user_id)
            db.update_lead_field(lead_id, "email_draft", email_content)            
    
    updated_leads = db.get_leads_by_query(user_id, search_query)
    return jsonify({"status": "success", "leads": updated_leads})

@legacy_bp.route('/check_session')
def check_session():
    user_id = get_current_user_id()
    if user_id:
        return jsonify({"logged_in": True})
    return jsonify({"logged_in": False})

@legacy_bp.route('/get_initial_data')
def get_initial_data():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error", "message": "No session found"}), 401

    try:
        history = db.get_user_history(user_id)
        leads = db.get_user_leads(user_id)
    except Exception as e:
        print(f"[LEGACY] get_initial_data error: {e}")
        history = []
        leads = []
    
    return jsonify({
        "status": "success",
        "history": history,
        "leads": leads,
        "user_id": user_id
    })

@legacy_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@legacy_bp.route('/save_settings', methods=['POST'])
def save_settings():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.json
    db.update_user_settings(
        user_id, 
        data.get('serper'), 
        data.get('openai'), 
        data.get('apollo'),
        data.get('model'),
        data.get('gemini'),
        data.get('claude')
    )
    return jsonify({"status": "success"})

@legacy_bp.route('/get_settings')
def get_settings():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error"}), 401
    
    try:
        settings = db.get_user_settings(user_id)
        if not settings:
            settings = {}
        return jsonify({
            "status": "success",
            "serper": settings.get('serper_api_key', ''),
            "openai": settings.get('openai_api_key', ''),
            "apollo": settings.get('apollo_api_key', ''),
            "gemini": settings.get('gemini_api_key', ''),
            "claude": settings.get('claude_api_key', ''),
            "model": settings.get('preferred_model', 'openai'),
            "gmail_address": settings.get('gmail_address', '')
        })
    except Exception as e:
        print(f"[LEGACY] get_settings error: {e}")
        return jsonify({
            "status": "success",
            "serper": "", "openai": "", "apollo": "",
            "gemini": "", "claude": "", "model": "openai",
            "gmail_address": ""
        })

@legacy_bp.route('/get_history_leads', methods=['POST'])
def get_history_leads():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error", "message": "Login required"}), 401
    search_query = request.json.get('query') 
    leads = db.get_leads_by_query(user_id, search_query)
    return jsonify({"status": "success", "leads": leads, "query": search_query})

@legacy_bp.route('/delete_lead', methods=['POST'])
def delete_lead_route():
    db_id = request.json.get('db_id')
    db.delete_lead(db_id)
    return jsonify({"status": "success"})

@legacy_bp.route('/delete_history', methods=['POST'])
def delete_history_route():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error"}), 401
    query = request.json.get('query')
    db.delete_history_record(user_id, query)
    return jsonify({"status": "success"})

@legacy_bp.route('/calculate_roi', methods=['POST'])
def calculate_roi():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error", "message": "Login required"}), 401
    db_id = request.json.get('db_id')
    lead = db.get_lead_by_id(db_id)
    
    if lead:
        roi_result = calculate_lead_roi(lead, user_id)
        db.update_lead_field(db_id, "roi_data", roi_result)
        return jsonify({"status": "success", "roi": roi_result})
    return jsonify({"status": "error", "message": "Lead not found"}), 404

@legacy_bp.route('/auto_send', methods=['POST'])
def auto_send():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error"}), 401

    ids = request.json.get('ids', [])
    settings = db.get_user_settings(user_id)

    for db_id in ids:
        lead = db.get_lead_by_id(db_id)
        if lead and lead.get('analysis') and lead.get('email_draft'):
            generate_and_send_email(lead, user_id, settings)

    updated = db.get_user_leads(user_id)
    return jsonify({"status": "success", "leads": updated})

@legacy_bp.route('/export_excel', methods=['GET'])
def export_excel():
    user_id = get_current_user_id()
    if not user_id: return jsonify({"status": "error", "message": "Unauthorized"}), 401
    file_path = os.path.abspath('leads.xlsx')
    if os.path.exists(file_path):
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        return send_file(file_path, as_attachment=True, download_name=f"leads_export_{date_str}.xlsx")
    return jsonify({"status": "error", "message": "Excel file not found"}), 404

app.register_blueprint(legacy_bp)