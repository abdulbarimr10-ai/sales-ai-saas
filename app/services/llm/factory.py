from .providers.openai_provider import OpenAIProvider
from .providers.claude_provider import ClaudeProvider
from .providers.gemini_provider import GeminiProvider
from .providers.ollama_provider import OllamaProvider
from app.services.key_service import key_service
import database.queries as db

# Maps provider names to their column in the legacy users table
_LEGACY_KEY_COLUMNS = {
    'openai': 'openai_api_key',
    'gemini': 'gemini_api_key',
    'claude': 'claude_api_key',
    'serper': 'serper_api_key',
}

class LLMFactory:
    @staticmethod
    def get_provider(provider_name: str, user_id: int):
        if provider_name == 'ollama':
            return OllamaProvider()
        
        # 1. Try new encrypted key store first
        key = key_service.get_decrypted_key(user_id, provider_name)
        
        # 2. Fallback: check legacy users table columns
        if not key:
            settings = db.get_user_settings(user_id)
            if settings:
                legacy_col = _LEGACY_KEY_COLUMNS.get(provider_name)
                if legacy_col:
                    key = settings.get(legacy_col)
                    # Filter out empty strings
                    if key and not key.strip():
                        key = None

        if not key:
            raise ValueError(f"No valid API key found for {provider_name}")
            
        if provider_name == 'openai':
            return OpenAIProvider(key)
        elif provider_name == 'claude':
            return ClaudeProvider(key)
        elif provider_name == 'gemini':
            return GeminiProvider(key)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

