from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    gender: str
    ip_address: str

class PaginatedResponse(BaseModel):
    data: List[User]
    total: int
    page: int
    page_size: int
    next_cursor: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None