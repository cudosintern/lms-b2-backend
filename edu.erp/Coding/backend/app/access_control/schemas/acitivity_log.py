from pydantic import BaseModel


class AcitivityCreate(BaseModel):
    user_id: int
    action: str
    description: str
    ip_address: str
    user_agent: str
    timestamp: str