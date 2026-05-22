# email_sender.py
from app.services.email_service import email_service

def send_email(to_email, subject, body, settings, user_id=None):
    """
    Proxies to the new secure email service. 
    user_id is required now, we fetch it dynamically if passed or we assume it's available in context.
    For legacy compatibility where user_id might not be passed explicitly to this lowest level tool,
    we'll need to ensure the caller passes it.
    """
    if not user_id:
        print("❌ user_id is required to send emails securely via BYOK infrastructure.")
        return False
        
    return email_service.send_user_email(user_id, to_email, subject, body)