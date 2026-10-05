from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    acepto_tratamiento: bool

    @field_validator("acepto_tratamiento")
    @classmethod
    def debe_aceptar_tratamiento(cls, v: bool) -> bool:
        """
        Ley 25.326 — el usuario DEBE aceptar el tratamiento de datos.
        Si viene en False, se rechaza el registro con 422.
        """
        if not v:
            raise ValueError(
                "Debés aceptar el tratamiento de datos personales (Ley 25.326) "
                "para poder registrarte."
            )
        return v


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    acepto_tratamiento: bool
    fecha_consentimiento: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
