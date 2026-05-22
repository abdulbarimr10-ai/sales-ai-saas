class LLMException(Exception):
    """Base exception for LLM operations."""
    pass

class ProviderAuthenticationError(LLMException):
    """Raised when API key is invalid or unauthorized."""
    pass

class ProviderTimeoutError(LLMException):
    """Raised when the provider API times out."""
    pass

class ProviderRateLimitError(LLMException):
    """Raised when hitting provider rate limits."""
    pass

class InvalidModelError(LLMException):
    """Raised when an unsupported model is requested."""
    pass
