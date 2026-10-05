from app.database import SessionLocal
from app import models
from app.core.security import hash_password
from datetime import datetime

def crear_o_promover_admin():
    db = SessionLocal()
    email_admin = "admin@tienda.com"
    password_admin = "Admin1234!"
    
    try:
        # Verificar si ya existe el usuario con este email
        usuario = db.query(models.Usuario).filter(models.Usuario.email == email_admin).first()
        
        if usuario:
            usuario.rol = "admin"
            usuario.activo = True
            usuario.hashed_password = hash_password(password_admin)
            db.commit()
            print(f"[OK] El usuario existente '{email_admin}' fue actualizado a ROL ADMIN con la contrasenia '{password_admin}'.")
        else:
            nuevo_admin = models.Usuario(
                nombre="Administradora",
                email=email_admin,
                hashed_password=hash_password(password_admin),
                rol="admin",
                acepto_tratamiento=True,
                fecha_consentimiento=datetime.utcnow(),
                activo=True
            )
            db.add(nuevo_admin)
            db.commit()
            print(f"[OK] Se creo exitosamente la cuenta ADMIN:")
            print(f"   - Email: {email_admin}")
            print(f"   - Contrasenia: {password_admin}")
            print(f"   - Rol: admin")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al crear/actualizar el admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_o_promover_admin()
