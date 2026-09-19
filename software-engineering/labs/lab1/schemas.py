from pydantic import BaseModel, Field
from typing import Optional

class BookBase(BaseModel):
    title: str = Field(..., example="The Great Gatsby")
    author: str = Field(..., example="F. Scott Fitzgerald")
    genre: str = Field(..., example="Fiction")
    year: int = Field(..., example=1925)
    price: float = Field(..., example=10.99)
    is_available: bool = True

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None

class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True
