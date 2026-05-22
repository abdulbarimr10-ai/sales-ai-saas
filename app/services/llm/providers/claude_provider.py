import time
import anthropic
from ..base import BaseLLMProvider
from ..exceptions import ProviderAuthenticationError, ProviderTimeoutError, ProviderRateLimitError

class ClaudeProvider(BaseLLMProvider):
    PRICING = {
        "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
    }

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self, prompt: str, model: str = "claude-3-5-sonnet-20240620", **kwargs):
        start_time = time.time()
        try:
            response = self.client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1024),
                temperature=kwargs.get("temperature", 0.7),
                timeout=kwargs.get("timeout", 30)
            )
            
            latency = int((time.time() - start_time) * 1000)
            content = response.content[0].text.strip()
            
            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens
            
            return {
                "content": content,
                "provider": "claude",
                "model": model,
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "estimated_cost": self.estimate_cost(model, tokens_in, tokens_out),
                "latency_ms": latency
            }
            
        except anthropic.AuthenticationError:
            raise ProviderAuthenticationError("Invalid Claude API Key")
        except anthropic.APITimeoutError:
            raise ProviderTimeoutError("Claude request timed out")
        except anthropic.RateLimitError:
            raise ProviderRateLimitError("Claude rate limit exceeded")
        except Exception as e:
            raise Exception(f"Claude error: {str(e)}")

    def stream(self, prompt: str, model: str = "claude-3-5-sonnet-20240620", **kwargs):
        stream = self.client.messages.stream(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 1024)
        )
        for event in stream:
            if event.type == "content_block_delta":
                yield event.delta.text

    def validate_key(self) -> bool:
        try:
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        rates = self.PRICING.get(model, self.PRICING["claude-3-5-sonnet-20240620"])
        return (tokens_input * rates["input"] / 1000.0) + (tokens_output * rates["output"] / 1000.0)
