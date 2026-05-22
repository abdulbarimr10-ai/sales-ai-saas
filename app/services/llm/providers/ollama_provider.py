import time
import os
import ollama
from httpx import ReadTimeout, ConnectError
from ..base import BaseLLMProvider
from ..exceptions import ProviderTimeoutError

class OllamaProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        # Use OLLAMA_HOST env var (set by Docker) or default to localhost
        host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.client = ollama.Client(host=host)

    def generate(self, prompt: str, model: str = "mistral", **kwargs):
        start_time = time.time()
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": kwargs.get("temperature", 0.7)
                }
            )
            
            latency = int((time.time() - start_time) * 1000)
            content = response['response'].strip()
            
            # Use provided token counts if available
            tokens_in = response.get('prompt_eval_count', self.count_tokens(prompt))
            tokens_out = response.get('eval_count', self.count_tokens(content))
            
            return {
                "content": content,
                "provider": "ollama",
                "model": model,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "estimated_cost": 0.0, # Local = Free
                "latency_ms": latency
            }
            
        except ReadTimeout:
            raise ProviderTimeoutError("Ollama request timed out")
        except ConnectError:
            raise Exception("Cannot connect to local Ollama instance")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")

    def stream(self, prompt: str, model: str = "mistral", **kwargs):
        response = self.client.generate(model=model, prompt=prompt, stream=True)
        for chunk in response:
            if 'response' in chunk:
                yield chunk['response']

    def validate_key(self) -> bool:
        try:
            self.client.list()
            return True
        except:
            return False

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        return 0.0
