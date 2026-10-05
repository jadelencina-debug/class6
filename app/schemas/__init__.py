# Re-exporta schemas de productos (desde el módulo original app/schemas.py → ahora app/schemas_producto.py)
# y schemas de usuario, para que todos los imports existentes sigan funcionando.
from pydantic import BaseModel
from typing import Optional


class ProductoBase(BaseModel):
    nombre: str
    precio_final: float
    cuotas_cantidad: int
    cuotas_valor: float
    garantia_meses: int
    stock: int
    imagen_url: Optional[str] = None


class ProductoCreate(ProductoBase):
    pass


class ProductoOut(ProductoCreate):
    id: int

    class Config:
        from_attributes = True


# Schemas de usuario/auth
from app.schemas.usuario import UsuarioCreate, UsuarioOut, Token

__all__ = [
    "ProductoBase",
    "ProductoCreate",
    "ProductoOut",
    "UsuarioCreate",
    "UsuarioOut",
    "Token",
]
