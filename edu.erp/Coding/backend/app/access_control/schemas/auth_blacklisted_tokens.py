from pydantic import BaseModel


class BlackListedData(BaseModel):
    id: int
    token: str
    blacklisted_at: str