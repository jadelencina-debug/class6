from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Devuelve el hash bcrypt de la contraseña en texto plano."""
    return pwd_context.hash(plain)


def verificar_password(plain: str, hashed: str) -> bool:
    """Compara la contraseña en texto plano con el hash almacenado."""
    return pwd_context.verify(plain, hashed)


def crear_token(data: dict, tipo: str, expires_delta: timedelta) -> str:
    """
    Crea un JWT firmado con HS256.

    Payload incluye:
      - sub: identificador del sujeto (email)
      - rol: rol del usuario
      - tipo: "access" | "refresh"
      - exp: timestamp de expiración (UTC)
    """
    payload = data.copy()
    payload.update({
        "tipo": tipo,
        "exp": datetime.now(timezone.utc) + expires_delta,
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
