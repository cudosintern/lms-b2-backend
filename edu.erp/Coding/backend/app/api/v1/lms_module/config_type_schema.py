from pydantic import BaseModel

class ConfigTypeCreate(BaseModel):
    name: str
    status: int = 1
    min_mentees: int | None = None
    max_mentees: int | None = None

class ConfigTypeUpdate(BaseModel):
    name: str | None = None
    status: int | None = None
    min_mentees: int | None = None
    max_mentees: int | None = None
