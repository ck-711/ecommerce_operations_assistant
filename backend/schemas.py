from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    status: str
    model_config = {'from_attributes': True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserOut
