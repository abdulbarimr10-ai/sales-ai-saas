import redis
from datetime import datetime, timedelta
from app.core.config import settings
from database.models import supabase
import json
from user_agents import parse
import uuid

# Initialize Redis client
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class SessionService:
    def _check_db(self):
        if not supabase:
            raise Exception("Supabase not initialized for session storage")

    def create_session(self, user_id: int, user_agent_str: str, ip_address: str) -> str:
        self._check_db()
        session_id = str(uuid.uuid4())
        
        # Parse user agent
        ua = parse(user_agent_str)
        device_name = f"{ua.browser.family} on {ua.os.family}"
        
        expires_at = datetime.utcnow() + timedelta(days=7) # 7 day absolute timeout
        
        # 1. Save to DB
        supabase.table('sessions').insert({
            'user_id': user_id,
            'session_id': session_id,
            'ip_address': ip_address,
            'user_agent': user_agent_str,
            'device_name': device_name,
            'expires_at': expires_at.isoformat()
        }).execute()
        
        # 2. Save to Redis
        session_data = {
            'user_id': user_id,
            'device_name': device_name
        }
        # 24 hour idle timeout in redis
        redis_client.setex(f"session:{session_id}", 86400, json.dumps(session_data))
        
        return session_id

    def validate_session(self, session_id: str):
        if not session_id:
            return None
            
        # Check Redis first
        data = redis_client.get(f"session:{session_id}")
        if data:
            # Refresh idle timeout
            redis_client.expire(f"session:{session_id}", 86400)
            return json.loads(data)
            
        # Fallback to DB if redis evicted it but absolute timeout isn't hit
        self._check_db()
        response = supabase.table('sessions').select('*').eq('session_id', session_id).is_('revoked_at', 'null').execute()
        if not response.data:
            return None
            
        session_record = response.data[0]
        expires_at = datetime.fromisoformat(session_record['expires_at'].replace('Z', '+00:00'))
        
        if datetime.now(expires_at.tzinfo) > expires_at:
            self.revoke_session(session_id)
            return None
            
        # Restore to Redis
        session_data = {
            'user_id': session_record['user_id'],
            'device_name': session_record['device_name']
        }
        redis_client.setex(f"session:{session_id}", 86400, json.dumps(session_data))
        
        # Update last active
        supabase.table('sessions').update({'last_active_at': datetime.utcnow().isoformat()}).eq('session_id', session_id).execute()
        
        return session_data

    def revoke_session(self, session_id: str):
        # Remove from Redis
        redis_client.delete(f"session:{session_id}")
        
        # Mark revoked in DB
        if supabase:
            supabase.table('sessions').update({'revoked_at': datetime.utcnow().isoformat()}).eq('session_id', session_id).execute()

    def revoke_all_sessions(self, user_id: int, except_session_id: str = None):
        if not supabase:
            return
            
        # Get all active sessions from DB
        query = supabase.table('sessions').select('session_id').eq('user_id', user_id).is_('revoked_at', 'null')
        if except_session_id:
            query = query.neq('session_id', except_session_id)
            
        response = query.execute()
        
        # Remove all from Redis
        for record in response.data:
            redis_client.delete(f"session:{record['session_id']}")
            
        # Mark all revoked in DB
        update_query = supabase.table('sessions').update({'revoked_at': datetime.utcnow().isoformat()}).eq('user_id', user_id)
        if except_session_id:
            update_query = update_query.neq('session_id', except_session_id)
        update_query.execute()

    def get_active_sessions(self, user_id: int):
        if not supabase:
            return []
        response = supabase.table('sessions').select('*').eq('user_id', user_id).is_('revoked_at', 'null').execute()
        return response.data

session_service = SessionService()
