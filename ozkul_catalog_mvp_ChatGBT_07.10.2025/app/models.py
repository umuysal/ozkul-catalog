from sqlalchemy import Column, String, Float, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base

def uuid_pk():
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=uuid_pk)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(String, primary_key=True, default=uuid_pk)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"))
    path = Column(String, nullable=False)  # local uploads path
    alt = Column(String)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    product = relationship("Product", back_populates="images")
