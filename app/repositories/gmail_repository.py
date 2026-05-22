from database.models import supabase
import datetime

class GmailRepository:
    def _check_client(self):
        if not supabase:
            raise Exception("Supabase client is not initialized.")

    def save_credentials(self, user_id: int, gmail_address: str, encrypted_credentials: str):
        self._check_client()
        existing = self.get_connection(user_id)
        now = datetime.datetime.now().isoformat()
        
        if existing:
            supabase.table('gmail_connections').update({
                'gmail_address': gmail_address,
                'encrypted_credentials': encrypted_credentials,
                'is_active': True,
                'updated_at': now
            }).eq('user_id', user_id).execute()
        else:
            supabase.table('gmail_connections').insert({
                'user_id': user_id,
                'gmail_address': gmail_address,
                'encrypted_credentials': encrypted_credentials,
                'is_active': True
            }).execute()

    def get_connection(self, user_id: int):
        self._check_client()
        response = supabase.table('gmail_connections').select('*').eq('user_id', user_id).execute()
        return response.data[0] if response.data else None

    def delete_connection(self, user_id: int):
        self._check_client()
        supabase.table('gmail_connections').delete().eq('user_id', user_id).execute()

    def mark_inactive(self, user_id: int):
        self._check_client()
        supabase.table('gmail_connections').update({'is_active': False}).eq('user_id', user_id).execute()

gmail_repository = GmailRepository()
