from pydantic import BaseModel

class ProductoBase(BaseModel):
    nombre: str
    precio_final: float
    cuotas_cantidad: int
    cuotas_valor: float
    garantia_meses: int
    stock: int

class ProductoCreate(ProductoBase):
    pass

class ProductoOut(ProductoCreate):
    id: int

    class Config:
        from_attributes = True