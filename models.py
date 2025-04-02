from enum import Enum
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Column, Date, Integer, String, Text, func
from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    primer_nombre = db.Column(db.String(50), nullable=True)
    segundo_nombre = db.Column(db.String(50))
    primer_apellido = db.Column(db.String(50), nullable=True)
    segundo_apellido = db.Column(db.String(50))
    tipo_documento = db.Column(db.Enum('CC', 'TI', 'CE', 'Pasaporte'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=False)  # Contraseña sin cifrar
    correo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(255))
    rol = db.Column(db.Enum('Administrador', 'Subadministrador', 'Farmacia', 'paciente'), nullable=False)
    activo = db.Column(db.Boolean, default=False)
    afiliado = db.Column(db.Boolean, default=False)
  

def __init__(self, primer_nombre=None, segundo_nombre=None, primer_apellido=None, segundo_apellido=None, 
             tipo_documento=None, numero_documento=None, usuario=None, password=None, correo=None, telefono=None, 
             direccion=None, rol=None, activo=False, afiliado=False):  # <-- Asegurar que tiene un valor por defecto
    self.primer_nombre = primer_nombre
    self.segundo_nombre = segundo_nombre
    self.primer_apellido = primer_apellido
    self.segundo_apellido = segundo_apellido
    self.tipo_documento = tipo_documento
    self.numero_documento = numero_documento
    self.usuario = usuario
    self.password = password
    self.correo = correo
    self.telefono = telefono
    self.direccion = direccion
    self.rol = rol
    self.activo = activo
    self.afiliado = afiliado

    def is_active(self):
        return self.activo  # Devuelve el estado de la cuenta




class solicitudes_afiliacion(db.Model):
    __tablename__ = 'Solicitudes_Afiliacion'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    primer_nombre = db.Column(db.String(50), nullable=True)
    segundo_nombre = db.Column(db.String(50))
    primer_apellido = db.Column(db.String(50), nullable=True)
    segundo_apellido = db.Column(db.String(50))
    tipo_documento = db.Column(db.Enum('CC', 'TI', 'CE', 'Pasaporte'), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    fecha_expedicion = db.Column(db.Date, nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    correo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(255))
    departamento = db.Column(db.String(100))
    zona = db.Column(db.Enum('Rural', 'Urbana'), nullable=False)
    sexo = db.Column(db.Enum('Femenino', 'Masculino'), nullable=False)
    ficha_sisben = db.Column(db.Enum('Grupo A', 'Grupo B', 'Grupo C', name='sisben_groups'), nullable=False)
    estado = db.Column(db.Enum('Pendiente', 'Aprobado', 'Rechazado'), default='Pendiente')
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)


    
class Cita(db.Model):
    __tablename__ = 'cita'
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)  # Referencia correcta
    tipo_servicio = db.Column(db.String(50), nullable=False)
    especialidad = db.Column(db.String(50))
    tipo_examen = db.Column(db.String(50))
    motivo = db.Column(db.Text)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(20), nullable=False)
    codigo_confirmacion = db.Column(db.String(20), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.Enum('Pendiente', 'Programada','Confirmada', 'Cancelada', 'Atendida'), default='Programada')

    # Relación con Paciente
    paciente = db.relationship('Paciente', backref='citas')

    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'tipo_servicio': self.tipo_servicio,
            'especialidad': self.especialidad,
            'tipo_examen': self.tipo_examen,
            'motivo': self.motivo,
            'fecha': self.fecha.strftime('%Y-%m-%d') if self.fecha else None,
            'hora': self.hora,
            'codigo_confirmacion': self.codigo_confirmacion,
            'estado': self.estado
        }
        
class HistorialCita(db.Model):
    __tablename__ = 'historial_cita'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)  # Corregir la referencia
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    tipo_servicio = db.Column(db.String(255), nullable=False)
    especialidad = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), nullable=False)

        
class AtencionCita(db.Model):
    __tablename__ = 'atencion_cita'
    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('cita.id'))   # clave foránea
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamento.id'), nullable=False)
    recomendacion = db.Column(db.Text)
    indicacion = db.Column(db.String(255), nullable=False)  # Nuevo campo para la indicación
    fecha_atencion = db.Column(db.Date, nullable=False, default=func.current_date())
    cantidad_recetada = db.Column(db.Integer, default=1)
     
    cita = db.relationship('Cita', backref='atenciones')  # Relación con la tabla Cita
   



class Medicamento(db.Model):
    __tablename__ = 'medicamento'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.Enum('Analgésico', 'Antibiótico', 'Antiinflamatorio', 'Otro', name='tipo_medicamento'), nullable=True)
    concentracion = db.Column(db.String(50), nullable=True)
    presentacion = db.Column(db.Enum('Tableta', 'Jarabe', 'Inyectable', 'Crema', 'Otro', name='presentacion_medicamento'), nullable=True)
    laboratorio = db.Column(db.String(100), nullable=True)
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    estado = db.Column(db.Enum('Disponible', 'Agotado', 'Vencido', name='estado_medicamento'), nullable=False, default='Disponible')
    stock = db.Column(db.Integer, nullable=False)
    fecha_ingreso = db.Column(db.Date, server_default=func.current_date())
    imagen_url = db.Column(db.String(255), nullable=True)  
    farmacia_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    

    def to_dict(self):
        return {
            'id_medicamento': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'tipo': self.tipo.value if self.tipo else None,  
            'concentracion': self.concentracion,
            'presentacion': self.presentacion.value if self.presentacion else None,
            'laboratorio': self.laboratorio,
            'fecha_vencimiento': str(self.fecha_vencimiento) if self.fecha_vencimiento else None,
            'estado': self.estado.value if self.estado else None,  
            'stock': self.stock,
            'fecha_ingreso': str(self.fecha_ingreso),
            'imagen_url': self.imagen_url  
        }

class RegistroRetiroMedicamento(db.Model):
    __tablename__ = 'registro_retiro_medicamento'
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)  # Nombre correcto de la tabla
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamento.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    fecha_retiro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    paciente = db.relationship("Paciente", back_populates="retiros")
    medicamento = db.relationship('Medicamento', backref='retiros')

    def __repr__(self):
        return f'<RegistroRetiroMedicamento {self.id}>'


class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    fecha_notificacion = db.Column(db.DateTime, default=datetime.utcnow)

class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.Text)
    resultado = db.Column(db.Text)

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    primer_nombre = db.Column(db.String(100), nullable=True)
    segundo_nombre = db.Column(db.String(100), nullable=True)
    primer_apellido = db.Column(db.String(100), nullable=False)
    segundo_apellido = db.Column(db.String(100), nullable=True)
    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False, unique=True)
    fecha_expedicion = db.Column(db.Date)  
    fecha_nacimiento = db.Column(db.Date)
    correo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    zona = db.Column(db.String(50), nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    ficha_sisben = db.Column(db.String(50), nullable=True)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    imagen_usuario = db.Column(db.String(100), nullable=True)
    
    # Relaciones
    retiros = db.relationship("RegistroRetiroMedicamento", back_populates="paciente")
    usuario = db.relationship('Usuario', backref='pacientes', lazy=True)
    historial_citas = db.relationship('HistorialCita', backref='paciente', lazy=True)

    def __init__(self, usuario_id, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido,
                 tipo_documento, numero_documento, fecha_expedicion, fecha_nacimiento, correo, telefono, direccion, departamento,
                 zona, sexo, ficha_sisben, imagen_usuario=None):  # imagen_usuario ahora es opcional
        self.usuario_id = usuario_id
        self.primer_nombre = primer_nombre
        self.segundo_nombre = segundo_nombre
        self.primer_apellido = primer_apellido
        self.segundo_apellido = segundo_apellido
        self.tipo_documento = tipo_documento
        self.numero_documento = numero_documento
        self.fecha_expedicion = fecha_expedicion
        self.fecha_nacimiento = fecha_nacimiento
        self.correo = correo
        self.telefono = telefono
        self.direccion = direccion
        self.departamento = departamento
        self.zona = zona
        self.sexo = sexo
        self.ficha_sisben = ficha_sisben
        self.imagen_usuario = imagen_usuario 

    def __repr__(self):
        return f'<Paciente {self.primer_nombre} {self.primer_apellido}>'


class RecetaMedica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subadministrador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    paciente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamento.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    indicaciones = db.Column(db.Text, nullable=False)
    fecha_prescripcion = db.Column(db.DateTime, default=datetime.utcnow)
    


