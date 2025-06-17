from servidor import app
from database import db
from models import Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    nuevo_admin = Usuario(
        primer_nombre='Admin',
        segundo_nombre='Principal',
        primer_apellido='Sistema',
        segundo_apellido='',
        tipo_documento='CC',
        numero_documento='123456789',
        usuario='admin',
        password=generate_password_hash('admin123'),  # 👈 cifrada
        correo='admin@ejemplo.com',
        telefono='3000000000',
        direccion='Calle Principal',
        rol='Administrador',
        activo=True,
        afiliado=True
    )
    
    db.session.add(nuevo_admin)
    db.session.commit()
    print("✅ Administrador creado con éxito.")
