from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import hash_password, verificar_password, crear_token
from app.database import get_db
from app import models
from app.schemas.usuario import UsuarioCreate, UsuarioOut, Token
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
def register(datos: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario.
    - Rechaza el registro si **acepto_tratamiento** es false (Ley 25.326).
    - Almacena la contraseña como hash bcrypt (nunca en texto plano).
    """
    # Verificar email único
    existente = db.query(models.Usuario).filter(
        models.Usuario.email == datos.email
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email.",
        )

    nuevo = models.Usuario(
        nombre=datos.nombre,
        email=datos.email,
        hashed_password=hash_password(datos.password),
        acepto_tratamiento=datos.acepto_tratamiento,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión (OAuth2 form)",
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Autentica un usuario con email + contraseña.
    - El campo **username** del formulario debe contener el **email**.
    - Devuelve access_token (30 min) y refresh_token (7 días).
    - El error 401 nunca revela si falló el email o la contraseña.
    """
    usuario = db.query(models.Usuario).filter(
        models.Usuario.email == form.username
    ).first()

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not usuario or not verificar_password(form.password, usuario.hashed_password):
        raise credenciales_invalidas

    payload_base = {"sub": usuario.email, "rol": usuario.rol}

    access_token = crear_token(
        data=payload_base,
        tipo="access",
        expires_delta=timedelta(minutes=settings.ACCESS_MIN),
    )
    refresh_token = crear_token(
        data=payload_base,
        tipo="refresh",
        expires_delta=timedelta(minutes=settings.REFRESH_MIN),
    )

    return Token(access_token=access_token, refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# GET /auth/me  (requiere token de acceso)
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UsuarioOut,
    summary="Datos del usuario autenticado",
)
def me(current_user: models.Usuario = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado.
    Requiere header: Authorization: Bearer <access_token>
    """
    return current_user


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar access_token con refresh_token",
)
def refresh(body: dict, db: Session = Depends(get_db)):
    """
    Emite un nuevo access_token a partir de un refresh_token válido.
    Rechaza cualquier token cuyo campo **tipo** no sea "refresh".
    """
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Falta el campo refresh_token.")

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise credenciales_invalidas

    if payload.get("tipo") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Este endpoint solo acepta refresh tokens.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub")
    if not email:
        raise credenciales_invalidas

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        raise credenciales_invalidas

    payload_base = {"sub": usuario.email, "rol": usuario.rol}
    nuevo_access = crear_token(
        data=payload_base,
        tipo="access",
        expires_delta=timedelta(minutes=settings.ACCESS_MIN),
    )
    nuevo_refresh = crear_token(
        data=payload_base,
        tipo="refresh",
        expires_delta=timedelta(minutes=settings.REFRESH_MIN),
    )

    return Token(access_token=nuevo_access, refresh_token=nuevo_refresh)
