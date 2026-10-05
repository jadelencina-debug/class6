"""
Router de pedidos.

Endpoints:
  POST /pedidos/         — checkout (requiere login)
  GET  /pedidos/mios     — historial del usuario autenticado (DEBE ir antes que /{id})
  GET  /pedidos/{id}     — detalle de un pedido propio (o admin ve cualquiera)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.pedido import PedidoCreate, PedidoOut
from app.services import pedido_service

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


# ── POST /pedidos/ ─────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=PedidoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pedido (checkout)",
)
def crear_pedido(
    datos: PedidoCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_current_user),
):
    """
    Convierte el carrito en un pedido guardado en la base.

    - El precio **nunca** viene del cliente; se toma del servidor.
    - El stock se descuenta en la misma transacción.
    - Si algún producto no tiene stock suficiente → **409** con detalle claro.
    - Si la transacción falla a la mitad → rollback completo.
    """
    return pedido_service.crear_pedido(db=db, usuario=usuario_actual, datos=datos)


# ── GET /pedidos/mios ─────────────────────────────────────────────────────────
# ⚠️  DEBE estar declarado ANTES que /{pedido_id}, o FastAPI intenta parsear
#     "mios" como un entero y devuelve 422.
@router.get(
    "/mios",
    response_model=List[PedidoOut],
    summary="Historial de pedidos del usuario autenticado",
)
def mis_pedidos(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_current_user),
):
    """Devuelve los pedidos del usuario del token, del más nuevo al más viejo."""
    return (
        db.query(models.Pedido)
        .filter(models.Pedido.usuario_id == usuario_actual.id)
        .order_by(models.Pedido.creado_en.desc())
        .all()
    )


# ── GET /pedidos/{pedido_id} ───────────────────────────────────────────────────
@router.get(
    "/{pedido_id}",
    response_model=PedidoOut,
    summary="Detalle de un pedido (propio o admin)",
)
def obtener_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_current_user),
):
    """
    Devuelve un pedido por ID.

    - Si el pedido no existe → **404**.
    - Si el pedido existe pero pertenece a otro usuario (y no es admin) → **404**.
      (Un 403 revelaría que el pedido existe; un 404 no filtra información.)
    """
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    # 404 tanto si no existe como si es de otro (no revelamos que existe)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")

    if pedido.usuario_id != usuario_actual.id and usuario_actual.rol != "admin":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")

    return pedido


# ── POST /pedidos/{pedido_id}/revocacion ──────────────────────────────────────
@router.post(
    "/{pedido_id}/revocacion",
    status_code=status.HTTP_201_CREATED,
    summary="Revocar un pedido (Botón de Arrepentimiento)",
)
def revocar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(get_current_user),
):
    solicitud = pedido_service.revocar(db=db, usuario=usuario_actual, pedido_id=pedido_id)
    return {
        "codigo": solicitud.codigo,
        "pedido_id": solicitud.pedido_id,
        "creada_en": solicitud.creada_en
    }
