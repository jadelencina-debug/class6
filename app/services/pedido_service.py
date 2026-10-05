"""
Servicio transaccional de pedidos.

Toda la lógica de negocio del checkout vive aquí:
  1. Verificar existencia de cada producto (404 si no existe).
  2. Verificar stock suficiente (409 con detalle claro si no alcanza).
  3. Descontar stock y congelar precio al momento de la compra.
  4. Crear el Pedido y sus ItemPedido dentro de una transacción.
  5. Rollback completo si cualquier paso falla — la base nunca queda a medias.
"""
from decimal import Decimal
from datetime import datetime, timezone
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.schemas.pedido import PedidoCreate


def crear_pedido(
    db: Session,
    usuario: models.Usuario,
    datos: PedidoCreate,
) -> models.Pedido:
    """
    Crea un pedido completo de forma atómica.

    Raises:
        404 si algún producto no existe.
        409 si algún producto no tiene stock suficiente,
            con el nombre del producto y cuántas unidades quedan.
    """
    try:
        total = Decimal("0.00")
        items_a_guardar: list[models.ItemPedido] = []

        for item_in in datos.items:
            # 1. Existencia del producto
            producto = (
                db.query(models.Producto)
                .filter(models.Producto.id == item_in.producto_id)
                .with_for_update()
                .first()
            )
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con id {item_in.producto_id} no encontrado.",
                )

            # 2. Stock suficiente — el mensaje dice exactamente qué falta
            if producto.stock < item_in.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Stock insuficiente para '{producto.nombre}': "
                        f"pedís {item_in.cantidad}, quedan {producto.stock} unidades."
                    ),
                )

            # 3. Descontar stock
            producto.stock -= item_in.cantidad

            # 4. Congelar precio — nunca viene del cliente
            precio_congelado = Decimal(str(producto.precio_final))
            total += precio_congelado * item_in.cantidad

            items_a_guardar.append(
                models.ItemPedido(
                    producto_id=producto.id,
                    cantidad=item_in.cantidad,
                    precio_unitario=precio_congelado,
                )
            )

        # 5. Crear el pedido con sus ítems
        pedido = models.Pedido(
            usuario_id=usuario.id,
            estado="pendiente",
            total=total,
            items=items_a_guardar,
        )
        db.add(pedido)
        db.commit()
        db.refresh(pedido)
        return pedido

    except HTTPException:
        # Las HTTPException propias no necesitan rollback de negocio
        # pero lo hacemos para no dejar la sesión sucia.
        db.rollback()
        raise
    except Exception as exc:
        # Error inesperado: rollback y re-lanzar como 500
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar el pedido.",
        ) from exc


def generar_codigo() -> str:
    fecha = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ARR-{fecha}-{secrets.token_hex(3).upper()}"


def revocar(db: Session, usuario: models.Usuario, pedido_id: int) -> models.SolicitudRevocacion:
    # 1. Es tuyo (404)
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido or pedido.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado."
        )
    
    # 2. No está cancelado (409)
    if pedido.estado == "cancelado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El pedido ya está cancelado."
        )

    # 3. Estás dentro de los 10 días (409)
    # creado_en viene de la base (con o sin timezone), lo comparamos correctamente.
    # sqlite datetime is usually naive, treating it as utc.
    creado_en = pedido.creado_en
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)
    
    diferencia = datetime.now(timezone.utc) - creado_en
    if diferencia.days > 10:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pasaron más de 10 días desde la compra ({diferencia.days} días)."
        )

    # 4. Transacción
    try:
        # Devolver el stock
        for item in pedido.items:
            producto = db.query(models.Producto).filter(models.Producto.id == item.producto_id).with_for_update().first()
            if producto:
                producto.stock += item.cantidad
        
        # Cambiar el estado a cancelado
        pedido.estado = "cancelado"
        
        # Crear la solicitud
        solicitud = models.SolicitudRevocacion(
            codigo=generar_codigo(),
            pedido_id=pedido.id,
            usuario_id=usuario.id
        )
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
        return solicitud
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la revocación."
        ) from exc
