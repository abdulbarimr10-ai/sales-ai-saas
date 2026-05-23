import redis
from datetime import datetime, timedelta
from app.core.config import settings
from database.models import supabase
import json
from user_agents import parse
import uuid

import logging
import threading

logger = logging.getLogger(__name__)

class FallbackRedis:
    def __init__(self, redis_url: str):
        self.enabled = False
        self.client = None
        self.lock = threading.Lock()
        self.memory = {}
        
        try:
            if redis_url and not redis_url.startswith("memory://"):
                self.client = redis.Redis.from_url(redis_url, decode_responses=True)
                self.client.ping()
                self.enabled = True
                logger.info("Connected to Redis successfully.")
            else:
                logger.warning("REDIS_URL is empty or memory://. Using in-memory fallback for Redis.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {redis_url}: {e}. Falling back to in-memory dictionary storage.")

    def setex(self, key: str, time: int, value: str):
        if self.enabled and self.client:
            try:
                return self.client.setex(key, time, value)
            except Exception as e:
                logger.warning(f"Redis setex failed: {e}. Falling back to in-memory.")
                
        with self.lock:
            self.memory[key] = value
        return True

    def get(self, key: str):
        if self.enabled and self.client:
            try:
                return self.client.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Falling back to in-memory.")
                
        with self.lock:
            return self.memory.get(key)

    def delete(self, *names):
        if self.enabled and self.client:
            try:
                return self.client.delete(*names)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}. Falling back to in-memory.")
                
        count = 0
        with self.lock:
            for name in names:
                if name in self.memory:
                    self.memory.pop(name, None)
                    count += 1
        return count

    def set(self, name: str, value: str, ex=None, px=None, nx=False, xx=False, keepttl=False):
        if self.enabled and self.client:
            try:
                return self.client.set(name, value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl)
            except Exception as e:
                logger.warning(f"Redis set failed: {e}. Falling back to in-memory.")
                
        with self.lock:
            self.memory[name] = value
        return True

    def expire(self, name: str, time: int):
        if self.enabled and self.client:
            try:
                return self.client.expire(name, time)
            except Exception as e:
                logger.warning(f"Redis expire failed: {e}.")
        return True

# Initialize Redis client
redis_client = FallbackRedis(settings.REDIS_URL)

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
