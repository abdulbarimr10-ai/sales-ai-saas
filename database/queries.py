# queries.py
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import supabase

def _check_client():
    if not supabase:
        raise Exception("Supabase client is not initialized.")

def create_user(username, password):
    _check_client()
    hashed_pw = generate_password_hash(password)
    try:
        # Check if user exists
        existing = supabase.table("users").select("id").eq("username", username).execute()
        if existing.data:
            return False
            
        supabase.table("users").insert({
            "username": username,
            "password": hashed_pw
        }).execute()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def verify_user(username, password):
    _check_client()
    try:
        response = supabase.table("users").select("id, password").eq("username", username).execute()
        if response.data:
            user = response.data[0]
            if check_password_hash(user["password"], password):
                return user["id"]
        return None
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None

def get_lead_by_id(lead_id):
    _check_client()
    try:
        response = supabase.table("leads").select("*").eq("id", lead_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting lead by id: {e}")
        return None

def get_user_history(user_id):
    _check_client()
    try:
        response = supabase.table("history").select("intent").eq("user_id", user_id).order("timestamp", desc=False).limit(10).execute()
        return [row["intent"] for row in response.data]
    except Exception as e:
        print(f"Error getting history: {e}")
        return []

def get_user_leads(user_id):
    _check_client()
    try:
        response = supabase.table("leads").select("*").eq("user_id", user_id).order("id", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"Error getting user leads: {e}")
        return []

def add_to_history(user_id, intent):
    _check_client()
    try:
        supabase.table("history").insert({
            "user_id": user_id,
            "intent": intent,
            "command": intent
        }).execute()
    except Exception as e:
        print(f"Error adding to history: {e}")

def save_lead(user_id, lead):
    _check_client()
    try:
        # Check duplicate
        existing = supabase.table("leads").select("id").eq("user_id", user_id).eq("name", lead['name']).execute()
        if existing.data:
            return

        supabase.table("leads").insert({
            "user_id": user_id,
            "name": lead['name'],
            "industry": lead['industry'],
            "website": lead.get('website'),
            "description": lead.get('desc'),
            "analysis": lead.get('analysis'),
            "outreach_email": lead.get('outreach_email'),
            "google_rating": lead.get('google_rating', 0.0),
            "detected_problem": lead.get('detected_problem', "")
        }).execute()
    except Exception as e:
        print(f"Error saving lead: {e}")

def update_lead_field(lead_id, field, value):
    _check_client()
    allowed_fields = [
        "name", "industry", "website", "description", "analysis", 
        "outreach_email", "google_rating", "detected_problem", 
        "email_draft", "email_sent", "send_status", "last_contacted", 
        "roi_data", "linkedin_url"
    ]
    if field not in allowed_fields:
        print(f"❌ Blocked attempt to update invalid field: {field}")
        return

    try:
        supabase.table("leads").update({field: value}).eq("id", lead_id).execute()
    except Exception as e:
        print(f"Error updating lead field: {e}")

def update_user_settings(user_id, serper, openai, apollo, model, gemini=None, claude=None):
    _check_client()
    try:
        update_data = {
            "serper_api_key": serper,
            "openai_api_key": openai,
            "apollo_api_key": apollo,
            "preferred_model": model
        }
        if gemini is not None:
            update_data["gemini_api_key"] = gemini
        if claude is not None:
            update_data["claude_api_key"] = claude
            
        supabase.table("users").update(update_data).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error updating user settings: {e}")

def get_user_settings(user_id):
    _check_client()
    try:
        response = supabase.table("users").select(
            "serper_api_key, openai_api_key, apollo_api_key, gemini_api_key, claude_api_key, preferred_model, gmail_address, gmail_credentials"
        ).eq("id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return None

def get_leads_by_query(user_id, query):
    _check_client()
    try:
        clean_q = query.lower().replace("find", "").replace("search", "").replace("get", "").replace("top", "").strip()
        response = supabase.table("leads").select("*").eq("user_id", user_id).or_(f"industry.ilike.%{clean_q}%,name.ilike.%{clean_q}%").order("id", desc=False).execute()
        return response.data
    except Exception as e:
        print(f"Error getting leads by query: {e}")
        return []

def delete_lead(lead_id):
    _check_client()
    try:
        supabase.table("leads").delete().eq("id", lead_id).execute()
    except Exception as e:
        print(f"Error deleting lead: {e}")

def delete_history_leads(user_id, query):
    _check_client()
    try:
        clean_q = query.lower().replace("find", "").replace("search", "").strip()
        supabase.table("leads").delete().eq("user_id", user_id).ilike("industry", f"%{clean_q}%").execute()
    except Exception as e:
        print(f"Error deleting history leads: {e}")

def delete_history_record(user_id, query):
    _check_client()
    try:
        supabase.table("history").delete().eq("user_id", user_id).eq("command", query).execute()
        
        clean_q = query.lower().replace("find", "").replace("search", "").strip()
        supabase.table("leads").delete().eq("user_id", user_id).ilike("industry", f"%{clean_q}%").execute()
    except Exception as e:
        print(f"Error deleting history record: {e}")

def get_all_saved_urls(user_id):
    _check_client()
    try:
        response = supabase.table("leads").select("website").eq("user_id", user_id).execute()
        return [row["website"] for row in response.data if row["website"]]
    except Exception as e:
        print(f"Error getting saved URLs: {e}")
        return []

def mark_email_sent(lead_id, status):
    _check_client()
    try:
        supabase.table("leads").update({
            "email_sent": 1,
            "send_status": status,
            "last_contacted": datetime.now().strftime("%Y-%m-%d %H:%M")
        }).eq("id", lead_id).execute()
    except Exception as e:
        print(f"Error marking email sent: {e}")

def update_gmail_credentials(user_id, credentials_json, email_address):
    _check_client()
    try:
        supabase.table("users").update({
            "gmail_credentials": credentials_json,
            "gmail_address": email_address
        }).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error updating Gmail credentials: {e}")

def remove_gmail_credentials(user_id):
    _check_client()
    try:
        supabase.table("users").update({
            "gmail_credentials": None,
            "gmail_address": None
        }).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error removing Gmail credentials: {e}")
