"""
Schemas para pedidos y sus ítems.

Regla de oro: el cliente nunca manda precio, total, ni usuario_id.
Todo lo que sea dinero se calcula en el servidor.
"""
from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


# ── Input ─────────────────────────────────────────────────────────────────────

class ItemIn(BaseModel):
    """Un ítem dentro del cuerpo del pedido que llega del cliente."""
    producto_id: int
    # Field(gt=0): nadie compra cero ni cantidades negativas
    cantidad: int = Field(gt=0)


class PedidoCreate(BaseModel):
    """Cuerpo completo del POST /pedidos/. Sin precio, total ni usuario_id."""
    items: List[ItemIn] = Field(min_length=1)  # al menos un producto


# ── Output ────────────────────────────────────────────────────────────────────

class ItemOut(BaseModel):
    """Ítem de pedido serializado para la respuesta."""
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal

    model_config = {"from_attributes": True}


class PedidoOut(BaseModel):
    """Pedido serializado para la respuesta."""
    id: int
    estado: str
    total: Decimal
    creado_en: datetime
    items: List[ItemOut]

    model_config = {"from_attributes": True}
