from database.models import supabase
import datetime

class ApiKeyRepository:
    def _check_client(self):
        if not supabase:
            raise Exception("Supabase client is not initialized.")

    def save_key(self, user_id: int, provider: str, encrypted_key: str, key_prefix: str):
        self._check_client()
        # Upsert logic based on user_id and provider
        existing = self.get_key_by_provider(user_id, provider)
        now = datetime.datetime.now().isoformat()
        
        if existing:
            response = supabase.table('user_api_keys').update({
                'encrypted_key': encrypted_key,
                'key_prefix': key_prefix,
                'is_valid': True,
                'updated_at': now
            }).eq('user_id', user_id).eq('provider', provider).execute()
            return response.data[0] if response.data else None
        else:
            response = supabase.table('user_api_keys').insert({
                'user_id': user_id,
                'provider': provider,
                'encrypted_key': encrypted_key,
                'key_prefix': key_prefix,
                'is_valid': True
            }).execute()
            return response.data[0] if response.data else None

    def get_keys(self, user_id: int):
        self._check_client()
        response = supabase.table('user_api_keys').select('*').eq('user_id', user_id).execute()
        return response.data

    def get_key_by_provider(self, user_id: int, provider: str):
        self._check_client()
        response = supabase.table('user_api_keys').select('*').eq('user_id', user_id).eq('provider', provider).execute()
        return response.data[0] if response.data else None

    def delete_key(self, user_id: int, provider: str):
        self._check_client()
        supabase.table('user_api_keys').delete().eq('user_id', user_id).eq('provider', provider).execute()
        return True

    def mark_invalid(self, user_id: int, provider: str):
        self._check_client()
        supabase.table('user_api_keys').update({'is_valid': False}).eq('user_id', user_id).eq('provider', provider).execute()

api_key_repository = ApiKeyRepository()
