from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """
    Dependencia que extrae y valida el Bearer token.

    - 401 si el token es inválido, expirado, o el usuario no existe.
    - 401 si el token es de tipo 'refresh' (no es un access token).
    """
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise credenciales_invalidas

    # Solo aceptar access tokens
    if payload.get("tipo") != "access":
        raise credenciales_invalidas

    email: str = payload.get("sub")
    if not email:
        raise credenciales_invalidas

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        raise credenciales_invalidas
        
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o dado de baja.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


def require_admin(
    current_user: models.Usuario = Depends(get_current_user),
) -> models.Usuario:
    """
    Dependencia que exige rol 'admin'.

    - 401 si no hay token válido (lo lanza get_current_user).
    - 403 si el usuario existe pero no tiene rol admin.
    """
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permisos para realizar esta acción.",
        )
    return current_user
