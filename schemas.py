from pydantic import BaseModel
from typing import Optional

# Auth
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Games
class GameCreate(BaseModel):
    title: str

class GameOut(BaseModel):
    id: int
    title: str
    status: str
    is_booked: bool
    user_id: Optional[int] = None
    model_config = {"from_attributes": True}