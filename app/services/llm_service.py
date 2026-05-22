import ollama
import openai
import anthropic
import google.generativeai as genai
from app.services.key_service import key_service
from app.core.logging import logger
import database.queries as db

class LLMService:
    def get_user_provider_key(self, user_id: int, provider: str) -> str:
        """Fetches and decrypts the API key for runtime use."""
        return key_service.get_decrypted_key(user_id, provider)

    def generate_response(self, prompt: str, user_id: int, provider_override: str = None) -> str:
        # 1. Fetch user settings to determine preferred model
        settings = db.get_user_settings(user_id)
        if not settings:
            logger.error(f"Could not fetch user settings for {user_id}")
            return None

        provider = provider_override or settings.get('preferred_model', 'ollama')
        raw_text = ""
        
        logger.info(f"Generating LLM response using provider: {provider} for user: {user_id}")

        try:
            if provider == 'openai':
                key = self.get_user_provider_key(user_id, 'openai')
                if not key:
                    raise ValueError("OpenAI key missing or invalid")
                
                client = openai.OpenAI(api_key=key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                raw_text = response.choices[0].message.content.strip()
                del key # Destroy reference
                del client

            elif provider == 'claude':
                key = self.get_user_provider_key(user_id, 'claude')
                if not key:
                    raise ValueError("Claude key missing or invalid")
                
                client = anthropic.Anthropic(api_key=key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                raw_text = response.content[0].text.strip()
                del key
                del client

            elif provider == 'gemini':
                key = self.get_user_provider_key(user_id, 'gemini')
                if not key:
                    raise ValueError("Gemini key missing or invalid")
                
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                response = model.generate_content(prompt)
                raw_text = response.text.strip()
                del key
                
            else:
                # Local Ollama fallback
                response = ollama.generate(model='mistral', prompt=prompt)
                raw_text = response['response'].strip()

            clean_text = raw_text.replace('```', '').replace('"', '')
            return clean_text

        except Exception as e:
            logger.error(f"{provider.capitalize()} generation failed: {str(e)}")
            # Simple Failover Logic
            if provider != 'ollama':
                logger.info("Falling back to local Ollama model")
                return self.generate_response(prompt, user_id, provider_override='ollama')
            return None

llm_service = LLMService()
