from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, Optional

class BaseLLMProvider(ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # Ensure we don't accidentally log or store the key long-term
        
    @abstractmethod
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Must return normalized response:
        {
            "content": str,
            "provider": str,
            "model": str,
            "tokens_input": int,
            "tokens_output": int,
            "estimated_cost": float,
            "latency_ms": int
        }
        """
        pass
        
    @abstractmethod
    def stream(self, prompt: str, model: str, **kwargs) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def validate_key(self) -> bool:
        pass
        
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass
        
    @abstractmethod
    def estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        pass

    def __del__(self):
        """Ensure sensitive credentials are wiped when the provider is garbage collected."""
        self.api_key = None
