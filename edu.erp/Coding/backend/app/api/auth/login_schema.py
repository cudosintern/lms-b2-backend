from pydantic import BaseModel
from typing import Optional

#null data checking as None
class LoginDataRequest(BaseModel):
    username: Optional[str] 
    password: Optional[str] 
    role: Optional[str]=None
    
