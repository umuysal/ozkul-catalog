from pydantic import BaseModel
from typing import Optional, List

class ProductImageOut(BaseModel):
    id: str
    path: str
    alt: Optional[str] = None
    sort_order: int

class ProductIn(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None

class ProductOut(ProductIn):
    id: str
    images: List[ProductImageOut] = []
