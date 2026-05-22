import openai
import anthropic
import google.generativeai as genai
from app.core.security import encrypt_data, decrypt_data
from app.repositories.api_key_repository import api_key_repository

class KeyService:
    def test_provider_connection(self, provider: str, api_key: str) -> bool:
        """Pings the provider to check if the key is valid."""
        try:
            if provider == 'openai':
                client = openai.OpenAI(api_key=api_key)
                client.models.list()
                return True
            elif provider == 'claude':
                client = anthropic.Anthropic(api_key=api_key)
                # Claude doesn't have a simple ping, so we try a tiny completion or list models
                # List models is available in newer anthropic versions, or we can just assume valid if it doesn't immediately throw on init
                # But actual validation requires an API call. Let's do a tiny generation.
                client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "ping"}]
                )
                return True
            elif provider == 'gemini':
                genai.configure(api_key=api_key)
                # Simple list models to verify
                list(genai.list_models())
                return True
            return False
        except Exception as e:
            print(f"Provider connection test failed for {provider}: {e}")
            return False

    def save_api_key(self, user_id: int, provider: str, raw_api_key: str):
        """Validates, encrypts and saves an API key."""
        if not self.test_provider_connection(provider, raw_api_key):
            raise ValueError(f"Invalid API Key for provider: {provider}")

        encrypted_key = encrypt_data(raw_api_key)
        # Store prefix like 'sk-...1234'
        if provider == 'openai' and raw_api_key.startswith('sk-'):
            prefix = raw_api_key[:7] + '...' + raw_api_key[-4:]
        else:
            prefix = raw_api_key[:4] + '...' + raw_api_key[-4:]

        return api_key_repository.save_key(user_id, provider, encrypted_key, prefix)

    def get_user_keys(self, user_id: int):
        """Returns all keys for a user, masked."""
        keys = api_key_repository.get_keys(user_id)
        if not keys:
            return []
        
        return [{
            "id": k['id'],
            "provider": k['provider'],
            "key_prefix": k['key_prefix'],
            "is_valid": k['is_valid'],
            "created_at": k['created_at'],
            "updated_at": k['updated_at']
        } for k in keys]

    def delete_key(self, user_id: int, provider: str):
        return api_key_repository.delete_key(user_id, provider)

    def get_decrypted_key(self, user_id: int, provider: str) -> str:
        """Returns the plaintext key for internal system use ONLY."""
        key_record = api_key_repository.get_key_by_provider(user_id, provider)
        if not key_record or not key_record['is_valid']:
            return None
        return decrypt_data(key_record['encrypted_key'])

key_service = KeyService()
