from pydantic import BaseModel

class GmailConnectionResponse(BaseModel):
    gmail_address: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
