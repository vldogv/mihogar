from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    email: str

class UserResponse(BaseModel):
    id: str
    email: str