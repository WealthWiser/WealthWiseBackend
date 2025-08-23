from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    dob: str | None
    age: int | None
