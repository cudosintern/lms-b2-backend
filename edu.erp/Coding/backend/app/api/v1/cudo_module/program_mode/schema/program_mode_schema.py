from pydantic import BaseModel
from typing import Optional

class ProgramModeBase(BaseModel):
    program_mode_name: str
    description: Optional[str] = None

class CreateProgramMode(ProgramModeBase):
    pass

class UpdateProgramMode(BaseModel):
    program_mode_name: Optional[str] = None
    description: Optional[str] = None

class ProgramModeInDB(BaseModel):
    prg_mode_id: int
    prg_mode_name: str
    prg_mode_desc: str
    prg_mode_code: str
    status: int

    class Config:
        from_attributes = True
