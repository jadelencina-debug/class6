from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Numeric, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
# pyrefly: ignore [missing-import]
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    # --- Campos para Autenticación y Ley 25.326 ---
    hashed_password = Column(String, nullable=False)
    rol = Column(String, default="customer", nullable=False)
    acepto_tratamiento = Column(Boolean, nullable=False)
    fecha_consentimiento = Column(DateTime, default=datetime.utcnow, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_baja = Column(DateTime, nullable=True)

    pedidos = relationship("Pedido", back_populates="usuario")
    solicitudes_revocacion = relationship("SolicitudRevocacion", back_populates="usuario")

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio_final = Column(Float, nullable=False)
    cuotas_cantidad = Column(Integer, nullable=False)
    cuotas_valor = Column(Float, nullable=False)
    garantia_meses = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    imagen_url = Column(String, nullable=True)

    items_pedido = relationship("ItemPedido", back_populates="producto")

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    estado = Column(String, default="pendiente", nullable=False)
    # Numeric(12,2) evita errores de punto flotante en dinero
    total = Column(Numeric(12, 2), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="pedidos")
    # cascade garantiza que al borrar un pedido se borren sus ítems
    items = relationship(
        "ItemPedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )

class ItemPedido(Base):
    __tablename__ = "items_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    # precio congelado al momento de la compra — nunca viene del cliente
    precio_unitario = Column(Numeric(12, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items_pedido")

class SolicitudRevocacion(Base):
    __tablename__ = "solicitudes_revocacion"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    creada_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    pedido = relationship("Pedido")
    usuario = relationship("Usuario", back_populates="solicitudes_revocacion")