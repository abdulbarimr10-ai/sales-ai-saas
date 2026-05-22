import secrets
import hashlib
from datetime import datetime, timedelta
from database.models import supabase
from app.core.exceptions import APIError
from app.services.email_service import email_service
from app.core.config import settings

class TokenServiceBase:
    def _check_db(self):
        if not supabase:
            raise APIError("Supabase not initialized", status_code=500)

    def generate_token(self) -> tuple[str, str]:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash

class EmailVerificationService(TokenServiceBase):
    def create_verification(self, user_id: int, email: str):
        self._check_db()
        token, token_hash = self.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        supabase.table('email_verifications').insert({
            'user_id': user_id,
            'token_hash': token_hash,
            'expires_at': expires_at.isoformat()
        }).execute()
        
        # In a real system, we'd send via an admin email sender, not the user's connected Gmail
        # because the user hasn't connected Gmail yet if they just signed up.
        # But for this demo context, we'll log it or assume an admin email service exists.
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}&uid={user_id}"
        print(f"📧 [MOCK EMAIL] To {email}: Please verify your email at {verify_link}")

    def verify_email(self, user_id: int, token: str):
        self._check_db()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        response = supabase.table('email_verifications').select('*').eq('user_id', user_id).eq('token_hash', token_hash).is_('used_at', 'null').execute()
        
        if not response.data:
            raise APIError("Invalid or expired verification link", status_code=400)
            
        record = response.data[0]
        expires_at = datetime.fromisoformat(record['expires_at'].replace('Z', '+00:00'))
        
        if datetime.utcnow() > expires_at:
            raise APIError("Verification link expired", status_code=400)
            
        # Mark used and update user
        supabase.table('email_verifications').update({'used_at': datetime.utcnow().isoformat()}).eq('id', record['id']).execute()
        supabase.table('users').update({'email_verified': True}).eq('id', user_id).execute()

class PasswordResetService(TokenServiceBase):
    def create_reset(self, email: str):
        self._check_db()
        response = supabase.table('users').select('id').eq('email', email).execute()
        if not response.data:
            return # Don't leak whether email exists
            
        user_id = response.data[0]['id']
        token, token_hash = self.generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        supabase.table('password_resets').insert({
            'user_id': user_id,
            'token_hash': token_hash,
            'expires_at': expires_at.isoformat()
        }).execute()
        
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}&uid={user_id}"
        print(f"📧 [MOCK EMAIL] To {email}: Reset your password at {reset_link}")

    def verify_and_reset(self, user_id: int, token: str, new_password: str):
        from app.services.auth_service import auth_service
        self._check_db()
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        response = supabase.table('password_resets').select('*').eq('user_id', user_id).eq('token_hash', token_hash).is_('used_at', 'null').execute()
        
        if not response.data:
            raise APIError("Invalid or expired reset link", status_code=400)
            
        record = response.data[0]
        expires_at = datetime.fromisoformat(record['expires_at'].replace('Z', '+00:00'))
        
        if datetime.utcnow() > expires_at:
            raise APIError("Reset link expired", status_code=400)
            
        # Hash new password
        new_hash = auth_service.hash_password(new_password)
        
        # Update user
        supabase.table('users').update({'password_hash': new_hash}).eq('id', user_id).execute()
        
        # Mark used
        supabase.table('password_resets').update({'used_at': datetime.utcnow().isoformat()}).eq('id', record['id']).execute()
        
        # Invalidate all sessions
        from app.services.session_service import session_service
        session_service.revoke_all_sessions(user_id)

email_verification_service = EmailVerificationService()
password_reset_service = PasswordResetService()
