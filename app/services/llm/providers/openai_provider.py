import time
import openai
from ..base import BaseLLMProvider
from ..exceptions import ProviderAuthenticationError, ProviderTimeoutError, ProviderRateLimitError

class OpenAIProvider(BaseLLMProvider):
    PRICING = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
    }

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, model: str = "gpt-4o", **kwargs):
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
                timeout=kwargs.get("timeout", 30)
            )
            
            latency = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content.strip()
            
            tokens_in = response.usage.prompt_tokens if response.usage else self.count_tokens(prompt)
            tokens_out = response.usage.completion_tokens if response.usage else self.count_tokens(content)
            
            return {
                "content": content,
                "provider": "openai",
                "model": model,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "estimated_cost": self.estimate_cost(model, tokens_in, tokens_out),
                "latency_ms": latency
            }
            
        except openai.AuthenticationError:
            raise ProviderAuthenticationError("Invalid OpenAI API Key")
        except openai.APITimeoutError:
            raise ProviderTimeoutError("OpenAI request timed out")
        except openai.RateLimitError:
            raise ProviderRateLimitError("OpenAI rate limit exceeded")
        except Exception as e:
            raise Exception(f"OpenAI error: {str(e)}")

    def stream(self, prompt: str, model: str = "gpt-4o", **kwargs):
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def validate_key(self) -> bool:
        try:
            self.client.models.list()
            return True
        except:
            return False

    def count_tokens(self, text: str) -> int:
        # Simple approximation, production uses tiktoken
        return len(text) // 4

    def estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        rates = self.PRICING.get(model, self.PRICING["gpt-4o"])
        return (tokens_input * rates["input"] / 1000.0) + (tokens_output * rates["output"] / 1000.0)
