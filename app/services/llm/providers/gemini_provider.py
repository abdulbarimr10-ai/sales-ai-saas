import time
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted, DeadlineExceeded
from ..base import BaseLLMProvider
from ..exceptions import ProviderAuthenticationError, ProviderTimeoutError, ProviderRateLimitError

class GeminiProvider(BaseLLMProvider):
    PRICING = {
        "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
        "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105}
    }

    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=self.api_key)

    def generate(self, prompt: str, model: str = "gemini-1.5-pro", **kwargs):
        start_time = time.time()
        try:
            gen_model = genai.GenerativeModel(model)
            response = gen_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7)
                )
            )
            
            latency = int((time.time() - start_time) * 1000)
            content = response.text.strip()
            
            # Simple token approximation if metadata not perfectly parsed
            tokens_in = self.count_tokens(prompt)
            tokens_out = self.count_tokens(content)
            
            return {
                "content": content,
                "provider": "gemini",
                "model": model,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "estimated_cost": self.estimate_cost(model, tokens_in, tokens_out),
                "latency_ms": latency
            }
            
        except InvalidArgument:
            raise ProviderAuthenticationError("Invalid Gemini API Key")
        except DeadlineExceeded:
            raise ProviderTimeoutError("Gemini request timed out")
        except ResourceExhausted:
            raise ProviderRateLimitError("Gemini rate limit exceeded")
        except Exception as e:
            raise Exception(f"Gemini error: {str(e)}")

    def stream(self, prompt: str, model: str = "gemini-1.5-pro", **kwargs):
        gen_model = genai.GenerativeModel(model)
        response = gen_model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def validate_key(self) -> bool:
        try:
            list(genai.list_models())
            return True
        except:
            return False

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        rates = self.PRICING.get(model, self.PRICING["gemini-1.5-pro"])
        return (tokens_input * rates["input"] / 1000.0) + (tokens_output * rates["output"] / 1000.0)
