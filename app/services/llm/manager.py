from app.services.llm.factory import LLMFactory
from app.services.llm.exceptions import ProviderTimeoutError, ProviderRateLimitError
from database.models import supabase
from app.core.logging import logger
import database.queries as db
import datetime

class LLMManager:
    def _track_usage(self, user_id: int, response: dict, request_type: str = 'generation'):
        if not supabase:
            return
            
        try:
            # Insert generation log
            supabase.table('ai_generations').insert({
                'user_id': user_id,
                'provider': response['provider'],
                'model': response['model'],
                'prompt_tokens': response['tokens_input'],
                'completion_tokens': response['tokens_output'],
                'total_tokens': response['tokens_input'] + response['tokens_output'],
                'estimated_cost': response['estimated_cost'],
                'latency_ms': response['latency_ms'],
                'request_type': request_type
            }).execute()
            
            # Upsert usage tracking
            provider = response['provider']
            existing = supabase.table('usage_tracking').select('*').eq('user_id', user_id).eq('provider', provider).execute()
            
            if existing.data:
                record = existing.data[0]
                supabase.table('usage_tracking').update({
                    'total_requests': record['total_requests'] + 1,
                    'total_tokens': record['total_tokens'] + response['tokens_input'] + response['tokens_output'],
                    'total_cost': float(record['total_cost']) + response['estimated_cost'],
                    'last_used_at': datetime.datetime.utcnow().isoformat()
                }).eq('id', record['id']).execute()
            else:
                supabase.table('usage_tracking').insert({
                    'user_id': user_id,
                    'provider': provider,
                    'total_requests': 1,
                    'total_tokens': response['tokens_input'] + response['tokens_output'],
                    'total_cost': response['estimated_cost']
                }).execute()
        except Exception as e:
            logger.error(f"Failed to track AI usage: {e}")

    def generate(self, prompt: str, user_id: int, provider_override: str = None, request_type: str = 'generation', **kwargs) -> str:
        settings = db.get_user_settings(user_id)
        if not settings:
            logger.error(f"Could not fetch user settings for {user_id}")
            return None

        primary_provider = provider_override or settings.get('preferred_model', 'ollama')
        
        # Build smart failover list: try all providers the user might have keys for
        all_providers = ['openai', 'gemini', 'claude', 'ollama']
        fallback_providers = [p for p in all_providers if p != primary_provider]
            
        providers_to_try = [primary_provider] + fallback_providers

        for current_provider in providers_to_try:
            try:
                logger.info(f"Attempting generation with {current_provider}")
                
                # Fetch model based on provider defaults or kwargs
                model = kwargs.get('model')
                if not model:
                    if current_provider == 'openai': model = 'gpt-4o'
                    elif current_provider == 'claude': model = 'claude-3-5-sonnet-20240620'
                    elif current_provider == 'gemini': model = 'gemini-1.5-pro'
                    else: model = 'mistral'
                
                provider_instance = LLMFactory.get_provider(current_provider, user_id)
                response = provider_instance.generate(prompt, model=model, **kwargs)
                
                self._track_usage(user_id, response, request_type)
                
                # Destroy provider instance to clean up memory/keys
                del provider_instance
                
                return response['content']

            except (ProviderTimeoutError, ProviderRateLimitError) as e:
                logger.warning(f"{current_provider} transient failure: {e}. Trying next provider...")
                continue
            except Exception as e:
                logger.error(f"{current_provider} hard failure: {e}")
                continue
                
        logger.error("All AI providers failed.")
        return None

llm_manager = LLMManager()
