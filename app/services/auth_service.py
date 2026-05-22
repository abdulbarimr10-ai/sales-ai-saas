from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.models.auth import UserRegisterRequest, UserLoginRequest, ChangePasswordRequest
from database.models import supabase
from app.core.exceptions import APIError
from app.services.session_service import session_service

ph = PasswordHasher()

class AuthService:
    def _check_db(self):
        if not supabase:
            raise APIError("Supabase not initialized for auth operations", status_code=500)

    def hash_password(self, password: str) -> str:
        return ph.hash(password)

    def verify_password(self, hash: str, password: str) -> bool:
        try:
            return ph.verify(hash, password)
        except VerifyMismatchError:
            return False

    def check_needs_rehash(self, hash: str) -> bool:
        return ph.check_needs_rehash(hash)

    def register_user(self, data: UserRegisterRequest) -> int:
        self._check_db()
        
        # Check existing
        existing = supabase.table('users').select('id').eq('email', data.email).execute()
        if existing.data:
            raise APIError("Email already registered", status_code=400)
            
        hashed = self.hash_password(data.password)
        
        response = supabase.table('users').insert({
            'email': data.email,
            'password_hash': hashed,
            'email_verified': False
            # Name and other fields can be added later or via profile update
        }).execute()
        
        return response.data[0]['id']

    def login_user(self, data: UserLoginRequest, user_agent: str, ip_address: str) -> tuple[int, str]:
        self._check_db()
        
        # Find user
        response = supabase.table('users').select('id, password_hash').eq('email', data.email).execute()
        if not response.data:
            raise APIError("Invalid credentials", status_code=401)
            
        user = response.data[0]
        
        # We need password_hash to exist
        if not user.get('password_hash'):
            # Legacy users with plaintext passwords? We need to migrate them or deny login.
            # Assuming old database uses 'password' instead of 'password_hash'
            response_legacy = supabase.table('users').select('password').eq('id', user['id']).execute()
            if response_legacy.data and response_legacy.data[0].get('password') == data.password:
                # Migrate to Argon2
                new_hash = self.hash_password(data.password)
                supabase.table('users').update({'password_hash': new_hash}).eq('id', user['id']).execute()
            else:
                raise APIError("Invalid credentials", status_code=401)
        elif not self.verify_password(user['password_hash'], data.password):
            raise APIError("Invalid credentials", status_code=401)
            
        # Rehash if necessary
        if user.get('password_hash') and self.check_needs_rehash(user['password_hash']):
            new_hash = self.hash_password(data.password)
            supabase.table('users').update({'password_hash': new_hash}).eq('id', user['id']).execute()
            
        # Create Session
        session_id = session_service.create_session(user['id'], user_agent, ip_address)
        return user['id'], session_id

    def change_password(self, user_id: int, data: ChangePasswordRequest):
        self._check_db()
        
        response = supabase.table('users').select('password_hash').eq('id', user_id).execute()
        if not response.data:
            raise APIError("User not found", status_code=404)
            
        current_hash = response.data[0].get('password_hash')
        if not current_hash or not self.verify_password(current_hash, data.old_password):
            raise APIError("Incorrect current password", status_code=400)
            
        new_hash = self.hash_password(data.new_password)
        supabase.table('users').update({'password_hash': new_hash}).eq('id', user_id).execute()
        
        # Invalidate all sessions to enforce re-login
        session_service.revoke_all_sessions(user_id)
        
auth_service = AuthService()
