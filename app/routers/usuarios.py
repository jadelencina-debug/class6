from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
from decimal import Decimal

from app import models
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def _obtener_datos_usuario(usuario: models.Usuario, db: Session):
    pedidos_db = db.query(models.Pedido).filter(models.Pedido.usuario_id == usuario.id).all()
    solicitudes_db = db.query(models.SolicitudRevocacion).filter(models.SolicitudRevocacion.usuario_id == usuario.id).all()
    
    pedidos = []
    for p in pedidos_db:
        pedidos.append({
            "id": p.id,
            "estado": p.estado,
            "total": str(p.total),
            "creado_en": p.creado_en.isoformat() if p.creado_en else None,
            "items": [{"producto_id": i.producto_id, "cantidad": i.cantidad, "precio_unitario": str(i.precio_unitario)} for i in p.items]
        })
        
    solicitudes = []
    for s in solicitudes_db:
        solicitudes.append({
            "codigo": s.codigo,
            "pedido_id": s.pedido_id,
            "creada_en": s.creada_en.isoformat() if s.creada_en else None
        })

    datos = {
        "perfil": {
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
            "fecha_consentimiento": usuario.fecha_consentimiento.isoformat() if usuario.fecha_consentimiento else None,
            "acepto_tratamiento": usuario.acepto_tratamiento,
            "activo": usuario.activo,
            "fecha_baja": usuario.fecha_baja.isoformat() if usuario.fecha_baja else None
        },
        "pedidos": pedidos,
        "solicitudes_revocacion": solicitudes
    }
    return datos


@router.get("/me/datos")
def obtener_mis_datos(
    usuario_actual: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _obtener_datos_usuario(usuario_actual, db)


@router.get("/me/exportar")
def exportar_mis_datos(
    usuario_actual: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    datos = _obtener_datos_usuario(usuario_actual, db)
    json_data = json.dumps(datos, default=_json_serial, indent=2)
    
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=mis_datos.json"}
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def dar_de_baja(
    usuario_actual: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    usuario_actual.nombre = "Usuario Eliminado"
    usuario_actual.email = f"eliminado_{usuario_actual.id}@example.com"
    usuario_actual.hashed_password = ""
    usuario_actual.activo = False
    usuario_actual.fecha_baja = datetime.now(timezone.utc)
    
    db.commit()
