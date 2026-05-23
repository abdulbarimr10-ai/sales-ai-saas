from pydantic import BaseModel, constr, validator
from typing import Optional
from datetime import datetime

class ApiKeyCreateRequest(BaseModel):
    provider: str
    api_key: str

    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['openai', 'gemini', 'claude']
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of: {', '.join(allowed)}")
        return v.lower()

class ApiKeyResponse(BaseModel):
    id: str
    provider: str
    key_prefix: str
    is_valid: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
