from functools import wraps
import logging
import os
import secrets
from sqlite3 import IntegrityError
import time
import traceback
from urllib.parse import urljoin, urlparse
from sqlalchemy import text
from flask import Flask, json, jsonify, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from database import db
from models import AtencionCita, Cita, HistorialCita, Medicamento, RegistroRetiroMedicamento, Slide, contacto, solicitudes_afiliacion, Usuario, Paciente
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.orm import joinedload
from datetime import datetime
import datetime 

app = Flask(__name__)

app.config['SECRET_KEY'] = 'tu_clave_secreta_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3307/eps_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_PERMANENT'] = True

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login_admin"
login_manager.init_app(app)


# 🔹 Verificar conexión a la base de datos
with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print("✅ Conexión exitosa a la base de datos")
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        
    
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# Modulo admistracion
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if current_user.is_authenticated:
        rutas = {
            "Administrador": url_for('admin'),
            "Subadministrador": url_for('admin'),
            "Farmacia": url_for('dashboard_farmacia')
        }

        destino = rutas.get(current_user.rol)
        if destino:
            return redirect(destino)
        else:
            logout_user()  # Cerrar sesión si el rol es inválido
            flash("⚠️ Error: Rol no válido, contacte al administrador.", "error")
            return redirect(url_for('login_admin'))  # Evitar bucle

    if request.method == 'GET':
        return render_template('login_admin.html')

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Se esperaba JSON"}), 400

    usuario = data.get('usuario')
    password = data.get('password')

    user = Usuario.query.filter_by(usuario=usuario).first()
    if not user:
        return jsonify({"status": "error", "message": "Usuario no encontrado", "clear_fields": True}), 404

    if user.password != password:
        return jsonify({"status": "error", "message": "Contraseña incorrecta", "clear_fields": True}), 401

    login_user(user)
    session.permanent = True

    print(f"✅ Usuario logueado: {user.usuario}, Rol: {user.rol}, Sesión permanente: {session.permanent}")
    flash('Inicio de sesión exitoso', 'success')

    rutas = {
        "Administrador": url_for('admin'),
        "Subadministrador": url_for('admin'),
        "Farmacia": url_for('dashboard_farmacia')
    }

    destino = rutas.get(user.rol)

    if destino:
        return jsonify({"status": "success", "redirect_url": destino, "clear_fields": False})
    else:
        logout_user() 
        return jsonify({"status": "error", "message": "Rol no válido, contacte al administrador", "clear_fields": True}), 403

# Ruta principal
@app.route('/')
def home():
    return render_template('index.html')



    

# Ruta Administradores
@app.route('/admin')
@login_required 
def admin():
    if current_user.rol not in ['Administrador', 'Subadministrador', 'Farmacia']:
        return redirect(url_for('home'))
    
    total_afiliado = Paciente.query.count()
    total_cita = Cita.query.filter_by(estado='Programada').count()
    total_solicitude = solicitudes_afiliacion.query.count()
    total_medicamento = Medicamento.query.count()
    
    solicitudes_pendientes = solicitudes_afiliacion.query.filter_by(estado='Pendiente').limit(5).all()
    contactos = contacto.query.all()
    
    return render_template('admin/admin_dashboard.html', usuario=current_user,total_afiliado=total_afiliado,total_cita=total_cita,total_solicitude=total_solicitude,total_medicamento=total_medicamento,solicitudes_pendientes=solicitudes_pendientes,contactos=contactos)

@app.route('/admin/farmacia', methods=['GET'])
@login_required
def admin_farmacia():
    if current_user.rol not in ['Administrador', 'Subadministrador', 'Farmacia']:
        return redirect(url_for('login_admin'))
    
    medicame = Medicamento.query.all()
    
    return render_template('admin/gestio_farmaci.html', usuario=current_user,medicame=medicame)

@app.route('/admin/slides', methods=['GET'])
@login_required
def admin_slides():
    if current_user.rol not in ['Administrador', 'Subadministrador', 'Farmacia']:
        return redirect(url_for('login_admin'))
    
    slides = Slide.query.order_by(Slide.orden).all()
    return render_template('admin/slides/listar_slaider.html', slides=slides,usuario=current_user)

@app.route('/admin/slides/crear', methods=['GET', 'POST'])
def crear_slide():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        url_boton = request.form['url_boton']
        texto_boton = request.form['texto_boton'] or "VER RECOMENDACIONES"
        activo = 'activo' in request.form
        orden = request.form['orden']
        
        # Manejar la subida de la imagen
        imagen_file = request.files.get('imagen')
        imagen_path = None
        
        if imagen_file and imagen_file.filename:
            filename = secure_filename(imagen_file.filename)
            # Generar nombre único con timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(filepath)
            imagen_path = f"uploads/{filename}"
        
        nuevo_slide = Slide(
            titulo=titulo,
            descripcion=descripcion,
            imagen=imagen_path,
            url_boton=url_boton,
            texto_boton=texto_boton,
            activo=activo,
            orden=orden
        )
        
        try:
            db.session.add(nuevo_slide)
            db.session.commit()
            flash('Slide creado exitosamente', 'success')
            return redirect(url_for('admin_slides'))
        except Exception as e:
            flash(f'Error al crear el slide: {str(e)}', 'danger')
            
    return render_template('admin/slides/crear_slaider.html')

@app.route('/admin/slides/editar/<int:id>', methods=['GET', 'POST'])
def editar_slide(id):
    slide = Slide.query.get_or_404(id)
    
    if request.method == 'POST':
        slide.titulo = request.form['titulo']
        slide.descripcion = request.form['descripcion']
        slide.url_boton = request.form['url_boton']
        slide.texto_boton = request.form['texto_boton'] or "VER RECOMENDACIONES"
        slide.activo = 'activo' in request.form
        slide.orden = request.form['orden']
        
        # Manejar la subida de la imagen
        imagen_file = request.files.get('imagen')
        
        if imagen_file and imagen_file.filename:
            # Eliminar imagen anterior si existe
            if slide.imagen:
                try:
                    old_path = os.path.join(app.root_path, 'static', slide.imagen)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    flash(f'Error al eliminar imagen anterior: {str(e)}', 'warning')
            
            filename = secure_filename(imagen_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(filepath)
            slide.imagen = f"uploads/{filename}"
        
        try:
            db.session.commit()
            flash('Slide actualizado exitosamente', 'success')
            return redirect(url_for('admin_slides'))
        except Exception as e:
            flash(f'Error al actualizar el slide: {str(e)}', 'danger')
            
    return render_template('admin/slides/editar_slaider.html', slide=slide)

@app.route('/admin/slides/eliminar/<int:id>')
def eliminar_slide(id):
    slide = Slide.query.get_or_404(id)
    
    # Eliminar la imagen asociada
    if slide.imagen:
        try:
            image_path = os.path.join(app.root_path, 'static', slide.imagen)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            flash(f'Error al eliminar la imagen: {str(e)}', 'warning')
    
    try:
        db.session.delete(slide)
        db.session.commit()
        flash('Slide eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar el slide: {str(e)}', 'danger')
        
    return redirect(url_for('admin_slides'))

@app.route('/admin/slides/cambiar-orden', methods=['POST'])
def cambiar_orden_slides():
    # Esta ruta recibiría datos AJAX para cambiar el orden de los slides
    if request.method == 'POST':
        slide_ids = request.form.getlist('slide_ids[]')
        
        for i, slide_id in enumerate(slide_ids):
            slide = Slide.query.get(int(slide_id))
            if slide:
                slide.orden = i
        
        try:
            db.session.commit()
            return {'status': 'success'}
        except:
            db.session.rollback()
            return {'status': 'error'}, 500
    
    return {'status': 'error', 'message': 'Método no permitido'}, 405



# Ruta para la página de recomendaciones COVID-19
@app.route('/covid-recomendaciones')
def covid_recomendaciones():
    return render_template('public/covid_recomendaciones.html')


@app.route('/admin/perfil', methods=['GET'])
@login_required
def perfil():
    # Si el usuario NO tiene rol permitido, lo rediriges a home
    if current_user.rol not in ['Administrador', 'Subadministrador','Farmacia']:
        return redirect(url_for('home'))
    
    # 🔹 Si el usuario es de Farmacia, lo mandamos a su perfil específico
    if current_user.rol == 'Farmacia':
        return redirect(url_for('perfil_far'))
    # Asegúrate de tener esta ruta

    # Obtener todas las solicitudes si es admin o subadmin
    solicitudes = solicitudes_afiliacion.query.order_by(
        solicitudes_afiliacion.estado != 'Rechazada',
        solicitudes_afiliacion.fecha_solicitud.desc()
    ).all()

    return render_template('admin/perfil_dashboard.html', solicitudes=solicitudes, usuario=current_user)

@app.route('/admin/solicitudes', methods=['GET'])
@login_required
def ver_solicitudes():
    if current_user.rol not in ['Administrador', 'Subadministrador']:
        return redirect(url_for('home'))
    
    solicitudes = solicitudes_afiliacion.query.filter_by(estado='Pendiente').all()
    
    solicitudes_json = [{
        'id': s.id,
        'primer_nombre': s.primer_nombre,
        'primer_apellido': s.primer_apellido,
        'tipo_documento': s.tipo_documento,
        'numero_documento': s.numero_documento,
        'zona': s.zona,
        'estado': s.estado
    } for s in solicitudes]
    
    ultimo_timestamp = round(time.time() * 1000)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'solicitudes': solicitudes_json,
            'timestamp': ultimo_timestamp
        })
    
   
    return render_template('admin/solicitud_admin.html', solicitudes=solicitudes_json, usuario=current_user, timestamp=ultimo_timestamp)

@app.route('/admin/solicitudes/aceptar/<int:solicitud_id>', methods=['POST'])
@login_required

def aceptar_solicitud(solicitud_id):
    if current_user.rol not in ['Administrador', 'subadministrador']:
        return redirect(url_for('login_admin'))
        
    print(f"🔍 Inicio de la función aceptar_solicitud con solicitud_id: {solicitud_id}")
    
    try:
        # Verificar si la solicitud existe
        solicitud = solicitudes_afiliacion.query.get_or_404(solicitud_id)
        print(f"✅ Solicitud encontrada: {solicitud}")

        # 🔹 **Verificar si el usuario ya existe antes de crearlo**
        usuario_existente = Usuario.query.filter_by(numero_documento=solicitud.numero_documento).first()
        if usuario_existente:
            print(f"⚠️ El usuario con documento {solicitud.numero_documento} ya está registrado en la base de datos.")
            return jsonify({'status': 'error', 'message': 'El usuario ya está registrado'}), 400

        # 🔹 **Hacer rollback antes de cualquier operación para limpiar transacciones pendientes**
        db.session.rollback()

        # 🔹 **Crear el nuevo usuario**
        nuevo_usuario = Usuario(
            numero_documento=solicitud.numero_documento,
            tipo_documento=solicitud.tipo_documento,
            usuario=solicitud.numero_documento,
            password=solicitud.numero_documento,
            correo=solicitud.correo or "",
            telefono=solicitud.telefono or "",
            direccion=solicitud.direccion or "",
            rol='Paciente',
            activo=True,
            afiliado=True,
            debe_cambiar_clave=True 
        )

        db.session.add(nuevo_usuario)
        db.session.commit()  # 🔹 Guardar usuario en la base de datos
        print(f"✅ Usuario creado con ID: {nuevo_usuario.id}")

        # 🔹 **Convertir fechas si existen**
        fecha_expedicion = solicitud.fecha_expedicion
        fecha_nacimiento = solicitud.fecha_nacimiento

        if isinstance(fecha_expedicion, str):
            fecha_expedicion = datetime.strptime(fecha_expedicion, "%Y-%m-%d").date()
        if isinstance(fecha_nacimiento, str):
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()

        # 🔹 **Crear el paciente**
        paciente = Paciente(
            usuario_id=nuevo_usuario.id,
            primer_nombre=solicitud.primer_nombre,
            segundo_nombre=solicitud.segundo_nombre,
            primer_apellido=solicitud.primer_apellido,
            segundo_apellido=solicitud.segundo_apellido,
            tipo_documento=solicitud.tipo_documento,
            numero_documento=solicitud.numero_documento,
            fecha_expedicion=fecha_expedicion, 
            fecha_nacimiento=fecha_nacimiento,  
            correo=solicitud.correo,
            telefono=solicitud.telefono,
            direccion=solicitud.direccion,
            departamento=solicitud.departamento,
            zona=solicitud.zona,
            sexo=solicitud.sexo,
            ficha_sisben=solicitud.ficha_sisben
        )

        db.session.add(paciente)
        db.session.commit()  # 🔹 Guardar el paciente en la base de datos
        print(f"✅ Paciente creado con ID: {paciente.id}")

        # 🔹 **Actualizar el estado de la solicitud a 'Aprobada'**
        solicitud.estado = 'Aprobada'
        db.session.commit()
        print(f"🔹 Estado de la solicitud cambiado a: {solicitud.estado}")

        # 🔹 **Verificar si la solicitud sigue existiendo antes de eliminarla**
        solicitud_existente = solicitudes_afiliacion.query.get(solicitud_id)
        if solicitud_existente:
            print(f"🗑 Eliminando solicitud con ID: {solicitud_id}")
            db.session.delete(solicitud_existente)
            db.session.commit()
            print(f"✅ Solicitud con ID {solicitud_id} eliminada correctamente.")

        # 🔹 **Respuesta exitosa**
        return jsonify({
            'status': 'success',
            'message': 'Solicitud aprobada, paciente registrado y solicitud eliminada.',
        })

    except IntegrityError as e:
        db.session.rollback()
        print(f"❌ Error de integridad: {repr(e)}")
        return jsonify({'status': 'error', 'message': 'Error: usuario duplicado'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error inesperado: {repr(e)}")
        return jsonify({'status': 'error', 'message': f'Error al procesar la solicitud: {str(e)}'}), 500


@app.route('/admin/solicitudes/rechazar/<int:solicitud_id>', methods=['POST'])
@login_required
def rechazar_solicitud(solicitud_id):
    if current_user.rol not in ['Administrador', 'Subadministrador']:
            return redirect(url_for('home'))
    solicitud = 	solicitudes_afiliacion.query.get_or_404(solicitud_id)

    try:
        # Cambiar estado a "Rechazada"
        solicitud.estado = 'Rechazada'
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Solicitud rechazada correctamente', 'solicitud_id': solicitud_id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/admin/solicitudes/restaurar/<int:solicitud_id>', methods=['POST'])
@login_required
def restaurar_solicitud(solicitud_id):
    solicitud = 	solicitudes_afiliacion.query.get_or_404(solicitud_id)

    try:
        # Restaurar a estado "Pendiente" (o el que prefieras)
        solicitud.estado = 'Pendiente'
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Solicitud restaurada.', 'solicitud_id': solicitud_id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/admin/pacientes', methods=['GET'])
@login_required
def ver_pacientes():
    if current_user.rol not in ['Administrador', 'Subadministrador', 'Farmacia']:
        return redirect(url_for('home'))

    # Obtener todos los pacientes con su estado de usuario
    pacientes = db.session.query(
        Paciente.id,
        Paciente.primer_nombre,
        Paciente.primer_apellido,
        Paciente.tipo_documento,
        Paciente.numero_documento,
        Paciente.zona,
        Usuario.activo  # Tomamos el estado del usuario
    ).join(Usuario, Paciente.numero_documento == Usuario.numero_documento).all()

    pacientes_json = [{
        'id': p.id,
        'primer_nombre': p.primer_nombre,
        'primer_apellido': p.primer_apellido,
        'tipo_documento': p.tipo_documento,
        'numero_documento': p.numero_documento,
        'zona': p.zona,
        'activo': "Activo" if p.activo else "Inactivo"  # Convertimos el booleano en texto
    } for p in pacientes]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'pacientes': pacientes_json,
            'timestamp': round(time.time() * 1000)
        })
    
    return render_template('admin/paciente.html', pacientes=pacientes_json, usuario=current_user, timestamp=time.time())

@app.route('/admin/paciente/ver/<int:id>')
@login_required
def ver_paciente(id):
    if current_user.rol not in ['Administrador', 'Subadministrador']:
            return redirect(url_for('home'))
    paciente = Paciente.query.get(id)  # Obtener paciente por ID

    if not paciente:
        return redirect(url_for('lista_pacientes'))  # Redirige si no existe

    return render_template('admin/ver_detalles.html', paciente=paciente ,usuario=current_user)

@app.route('/admin/paciente/editar/<int:id>', methods=['GET'])
@login_required
def editar_paciente(id):
    if current_user.rol not in ['Administrador', 'Subadministrador']:
            return redirect(url_for('home'))


    paciente = Paciente.query.get_or_404(id)
    usuario = Usuario.query.filter_by(numero_documento=paciente.numero_documento).first()
    
    return render_template('admin/editar_paciente.html', paciente=paciente, usuario=usuario)

@app.route('/admin/paciente/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_paciente(id):
    if current_user.rol not in ['Administrador', 'Subadministrador']:
            return redirect(url_for('home'))

    # Busca al paciente por id
    paciente = Paciente.query.get_or_404(id)
    usuario = Usuario.query.filter_by(numero_documento=paciente.numero_documento).first()

    # Aquí actualizamos los campos del paciente
    paciente.primer_nombre = request.json.get('primer_nombre')
    paciente.segundo_nombre = request.json.get('segundo_nombre')
    paciente.primer_apellido = request.json.get('primer_apellido')
    paciente.segundo_apellido = request.json.get('segundo_apellido')
    paciente.tipo_documento = request.json.get('tipo_documento')
    paciente.numero_documento = request.json.get('numero_documento')
    paciente.correo = request.json.get('correo')
    paciente.telefono = request.json.get('telefono')
    paciente.direccion = request.json.get('direccion')
    paciente.zona = request.json.get('zona')
    paciente.departamento = request.json.get('departamento')
    paciente.sexo = request.json.get('sexo')
    paciente.ficha_sisben = request.json.get('ficha_sisben')

    # Actualizamos los datos del usuario
    usuario.tipo_documento = request.json.get('tipo_documento', usuario.tipo_documento)
    usuario.numero_documento = request.json.get('numero_documento', usuario.numero_documento)
    usuario.correo = request.json.get('correo', usuario.correo)
    usuario.telefono = request.json.get('telefono', usuario.telefono)
    usuario.direccion = request.json.get('direccion', usuario.direccion)

    # Actualizamos la contraseña solo en la tabla Usuario
    nueva_contraseña = request.json.get('contraseña')
    if nueva_contraseña:
        usuario.contraseña = nueva_contraseña

    # Actualizar estado del usuario
    activo = request.json.get('activo')
    if activo == '1':
        usuario.activo = True
    elif activo == '0':
        usuario.activo = False
    else:
        usuario.activo = False

    db.session.commit()

    return jsonify({'status': 'success'}), 200

@app.route('/admin/paciente/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_paciente(id):
    if current_user.rol != 'Administrador':
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 403

    paciente = Paciente.query.get(id)
    if not paciente:
        return jsonify({'status': 'error', 'message': 'Paciente no encontrado'}), 404

    usuario = Usuario.query.filter_by(numero_documento=paciente.numero_documento).first()

    # Verificar si el paciente tiene citas asociadas
    citas_asociadas = Cita.query.filter_by(paciente_id=paciente.id).first()
    if citas_asociadas:
        return jsonify({
            'status': 'error',
            'message': 'No se puede eliminar el paciente porque tiene citas asociadas. Por favor, revise las citas antes de eliminar.'
        }), 400

    medicamentos = RegistroRetiroMedicamento.query.filter_by(paciente_id=paciente.id).first()
    if medicamentos:
        return jsonify({
            'status': 'error',
            'message': 'No se puede eliminar el paciente porque tiene medicamentos recetados. Por favor, revise los medicamentos antes de eliminar.'
        }), 400

    try:
        if usuario:
            db.session.delete(usuario)

        db.session.delete(paciente)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Paciente eliminado correctamente'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error al eliminar paciente: {str(e)}'}), 500

from datetime import datetime

@app.route('/admin/cita', methods=['GET'])
def citas_admi():
    citas = Cita.query.options(joinedload(Cita.paciente)).filter(Cita.estado == 'Programada').all()

    # Verificar si se están obteniendo citas
    print(f'Citas obtenidas: {len(citas)}')  # Muestra cuántas citas se han recuperado

    # Crear un diccionario de citas, asegurándose de convertir los valores de fecha y hora
    citas_json = [{
        'id':cita.id,
        'nombre_paciente': cita.paciente.primer_nombre,
        'tipo_servicio': cita.tipo_servicio,
        'especialidad': cita.especialidad,
        'fecha': cita.fecha.strftime('%Y-%m-%d'),  # Convertir la fecha a una cadena
        'hora': str(cita.hora),  # Si la hora es un objeto timedelta, conviértelo a cadena
        'estado': cita.estado
    } for cita in citas]

    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(citas_json)

    return render_template('admin/cargar_citas.html', citas=citas_json)


from datetime import datetime

from datetime import datetime, timedelta

@app.route('/atender_cita/<int:cita_id>', methods=['GET', 'POST'])
def atender_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    medicamentos = Medicamento.query.all()

    if request.method == 'POST':
        recomendacion = request.form.get('recomendacion', '').strip()
        medicamentos_seleccionados = request.form.getlist('medicamentos[]')
        indicaciones = request.form.getlist('indicaciones[]')
        duraciones = request.form.getlist('duraciones[]')
        cantidad = request.form.getlist('cantidad[]')

        if not (medicamentos_seleccionados and indicaciones and duraciones) or \
           not (len(medicamentos_seleccionados) == len(indicaciones) == len(duraciones)):
            flash('⚠️ Error: Complete todos los campos de medicamentos.', 'danger')
            return redirect(request.url)

        for i in range(len(medicamentos_seleccionados)):
            medicamento_id = int(medicamentos_seleccionados[i])
            indicacion = indicaciones[i].strip()
            duracion_dias = int(duraciones[i])
            fecha_tratamiento_fin = datetime.utcnow() + timedelta(days=duracion_dias)
            cantidad_medicamento = int(cantidad[i]) if cantidad[i].isdigit() else 0

            # Guardar atención médica
            atencion = AtencionCita(
                cita_id=cita.id,
                medicamento_id=medicamento_id,
                recomendacion=recomendacion,
                indicacion=indicacion,
                cantidad_recetada=cantidad_medicamento,
            )
            db.session.add(atencion)

            # Guardar seguimiento del paciente
            estado = RegistroRetiroMedicamento(
                paciente_id=cita.paciente_id,
                medicamento_id=medicamento_id,
                indicacion=indicacion,
                cantidad=cantidad_medicamento,
                fecha_tratamiento_fin=fecha_tratamiento_fin,
                fecha_registro=datetime.utcnow()
            )
            db.session.add(estado)

        cita.estado = 'Atendida'
        db.session.commit()

        flash('✅ Cita atendida y medicamentos registrados correctamente.', 'success')
        return redirect(url_for('citas_admi'))

    return render_template('admin/atender_cita.html', cita=cita, medicamentos=medicamentos)




@app.route('/historial_atencion', methods=['GET'])
def historial_citas():
    try:
        # Obtener todas las citas del historial
        citas = Cita.query.filter_by(estado='Atendida').all()

        if not citas:
            return render_template('admin/historial_citas.html', citas=[])  # Si no hay citas, mostrar una lista vacía

        # Pasar las citas a la plantilla
        return render_template('admin/historial_citas.html', citas=citas)

    except Exception as e:
        return render_template('admin/historial_citas.html', error="Error al obtener el historial")


@app.route('/dashboard_farmacia')
@login_required
def dashboard_farmacia():
    # Código de la vista
    return render_template('dashboard_farmacia.html')

@app.route('/dashboard_farmacia/perfil_farmacia')
@login_required
def perfil_far():
    
    solicitudes = solicitudes_afiliacion.query.order_by(
        solicitudes_afiliacion.estado != 'Rechazada',
        solicitudes_afiliacion.fecha_solicitud.desc()
    ).all()
    return render_template('perfil_farmacia.html' ,solicitudes=solicitudes, usuario=current_user )


# Configuración de subida de imágenes
MEDICAMENTOS_UPLOAD_FOLDER = os.path.join(app.static_folder, 'medicamentos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MEDICAMENTOS_UPLOAD_FOLDER'] = MEDICAMENTOS_UPLOAD_FOLDER

# Asegurar que la carpeta de imágenes exista
os.makedirs(MEDICAMENTOS_UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """ Verifica si el archivo tiene una extensión permitida. """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/dashboard_farmacia/medicamentos/add_medicamento', methods=['GET', 'POST'])
@login_required
def agregar_medicamento():
    if request.method == 'GET':
        return render_template('farmacia/agregar_medicamento.html')

    if request.method == 'POST':
        try:
            usuario_actual = Usuario.query.get(current_user.id)
            if not usuario_actual:
                flash('❌ Usuario no encontrado', 'danger')
                return redirect(url_for('agregar_medicamento'))
            
            # Obtener datos del formulario
            nombre_medicamento = request.form.get('nombre', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            tipo = request.form.get('tipo', '').strip()
            concentracion = request.form.get('concentracion', '').strip()
            presentacion = request.form.get('presentacion', '').strip()
            laboratorio = request.form.get('laboratorio', '').strip()
            stock = request.form.get('stock', '0').strip()

            # Validación de stock
            try:
                stock = int(stock)
                if stock < 0:
                    flash('⚠️ El stock no puede ser negativo.', 'warning')
                    return redirect(url_for('agregar_medicamento'))
            except ValueError:
                flash('⚠️ El stock debe ser un número entero válido.', 'warning')
                return redirect(url_for('agregar_medicamento'))

            # Verificar si el medicamento ya existe con el mismo tipo y concentración
            medicamento_existente = Medicamento.query.filter_by(tipo=tipo, concentracion=concentracion).first()
            if medicamento_existente:
                flash('⚠️ Ya existe un medicamento con el mismo tipo y concentración.', 'warning')
                return redirect(url_for('agregar_medicamento'))

            # Manejo de la imagen
            imagen = request.files.get('imagen')
            imagen_filename = 'default.jpg'  # Imagen por defecto
            
            if imagen and allowed_file(imagen.filename):
                imagen_filename = secure_filename(imagen.filename)
                imagen_path = os.path.join(app.config['MEDICAMENTOS_UPLOAD_FOLDER'], imagen_filename)

                try:
                    imagen.save(imagen_path)
                    print(f"✅ Imagen guardada en: {imagen_path}")  # Depuración
                except Exception as e:
                    flash(f'⚠️ Error al guardar la imagen: {str(e)}', 'warning')
                    return redirect(url_for('agregar_medicamento'))

            # Crear el objeto Medicamento y guardar en BD
            nuevo_medicamento = Medicamento(
                nombre=nombre_medicamento,
                descripcion=descripcion,
                tipo=tipo,
                concentracion=concentracion,
                presentacion=presentacion,
                laboratorio=laboratorio,
                stock=stock,
                imagen_url=f"medicamentos/{imagen_filename}"  # Se guarda la ruta
            )

            db.session.add(nuevo_medicamento)
            db.session.commit()  # ✅ Guardar en la base de datos

            flash('✅ Medicamento agregado con éxito', 'success')
            return redirect(url_for('agregar_medicamento'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al agregar medicamento: {str(e)}', 'danger')
            return redirect(url_for('agregar_medicamento'))
      

    return render_template('farmacia/agregar_medicamento.html')

@app.route('/dashboard_farmacia/medicamentos', methods=['GET'])
@login_required
def ver_medicamentos():
    if current_user.rol != 'Farmacia':
        return redirect(url_for('home'))

    # Obtener todos los medicamentos con sus detalles
    medicamentos = db.session.query(
        Medicamento.id,
        Medicamento.nombre,
        Medicamento.descripcion,
        Medicamento.tipo,
        Medicamento.concentracion,
        Medicamento.laboratorio,
        Medicamento.estado,
        Medicamento.stock,
        Medicamento.fecha_ingreso,
        Medicamento.imagen_url
    ).all()

    medicamentos_json = [{
        'id': m.id,
        'nombre': m.nombre,
        'descripcion': m.descripcion,
        'tipo': m.tipo,
        'laboratorio': m.laboratorio,
        'concentracion' : m.concentracion,
        'estado': m.estado,
        'stock': m.stock,
        'fecha_ingreso': m.fecha_ingreso.strftime('%Y-%m-%d'),
       'imagen_url': url_for('static', filename=m.imagen_url) if m.imagen_url else '/static/default.png'




    } for m in medicamentos]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'medicamentos': medicamentos_json,
            'timestamp': round(time.time() * 1000)
        })
    
    return render_template('ver_medicamentos.html', medicamentos=medicamentos_json, usuario=current_user, timestamp=time.time())

@app.route('/editar_medicamento/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_medicamento(id):
    medicamento = Medicamento.query.get(id)
    if not medicamento:
        return "Medicamento no encontrado", 404

    if request.method == 'POST':
        medicamento.nombre = request.form['nombre']
        medicamento.descripcion = request.form['descripcion']
        medicamento.tipo = request.form['tipo']
        medicamento.concentracion = request.form['concentracion']
        medicamento.presentacion = request.form['presentacion']
        medicamento.laboratorio = request.form['laboratorio']
        medicamento.stock = int(request.form['stock'])

        # Manejo de la imagen
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Crear la carpeta si no existe
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                file.save(filepath)
                medicamento.imagen_url = f'/medicamentos/{filename}'  # Guardar ruta en la base de datos

        db.session.commit()
        return redirect(url_for('ver_medicamentos'))

    return render_template('farmacia/editar_medicamento.html', medicamento=medicamento)

@app.route('/eliminar_medicamento/<int:id>', methods=['GET','POST'])
@login_required
def eliminar_medicamento(id):
    medicamento = Medicamento.query.get(id)
    if not medicamento:
        return "Medicamento no encontrado", 404

    # Eliminar la imagen asociada si existe
    if medicamento.imagen_url:
        ruta_imagen = os.path.join(app.config['UPLOAD_FOLDER'], medicamento.imagen_url)
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

    # Eliminar el medicamento de la base de datos
    db.session.delete(medicamento)
    db.session.commit()

    return redirect(url_for('ver_medicamentos'))



@app.route('/consulta_general')
def consulta_general():
    return render_template('consulta_general.html')

@app.route('/contacto', methods=['GET', 'POST'])
def Contacto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        numero_documento = request.form['document']
        correo = request.form['email']
        tipo_solicitud = request.form['type']
        mensaje = request.form['message']

        nuevo_contacto = contacto(
            nombre=nombre,
            numero_documento=numero_documento,
            correo=correo,
            tipo_solicitud=tipo_solicitud,
            mensaje=mensaje
        )

        db.session.add(nuevo_contacto)
        db.session.commit()

        # Usar una categoría específica para mensajes de contacto
        flash('Tu mensaje ha sido enviado exitosamente. ¡Gracias por contactarnos!', 'contacto_success')
        return redirect(url_for('Contacto'))

    return render_template('contacto.html')


@app.route('/farmacia')
def farmacia():
    return render_template('Farmacia.html')

@app.route('/portal')
def portal():
    return render_template('login_usuarios.html')

@app.route('/nosotros') 
def nosotros():
    return render_template('Nosotros.html')  

@app.route('/portal_usuarios', methods=['GET', 'POST'])
def portal_usuarios():
    if request.method == 'GET':
        return render_template('portal_usuarios.html')

    if request.method == 'POST':
        if not request.is_json:
            return jsonify({"error": "Se esperaba una solicitud JSON"}), 400

        data = request.get_json()

        # Asignamos un usuario_id fijo para el administrador 
        usuario_id = 1

        # Verificación de campos obligatorios
        required_fields = ["primer_nombre", "primer_apellido", "tipo_documento", "documentNumber", "email", "zona", "sexo"]
        missing_fields = [field for field in required_fields if field not in data]

        valid_sisben_values = ['Grupo A', 'Grupo B', 'Grupo C']
        ficha_sisben = data.get('sisben', '')
        if ficha_sisben not in valid_sisben_values:
            return jsonify({"error": "El valor de 'sisben' no es válido. Debe ser uno de: 'Grupo A', 'Grupo B', 'Grupo C'."}), 400

        if missing_fields:
            return jsonify({"error": f"Faltan los siguientes campos: {', '.join(missing_fields)}"}), 400

        try:
            nueva_solicitud = 	solicitudes_afiliacion(
                usuario_id=usuario_id, 
                primer_nombre=data['primer_nombre'],
                segundo_nombre=data.get('segundo_nombre', ''),
                primer_apellido=data['primer_apellido'],
                segundo_apellido=data.get('segundo_apellido', ''),
                tipo_documento=data['tipo_documento'],
                numero_documento=data['documentNumber'],
                fecha_nacimiento=data['fecha_nacimiento'],
                fecha_expedicion=data['fecha_expedicion'],
                correo=data['email'],
                telefono=data.get('telefono', ''),
                direccion=data.get('direccion', ''),
                departamento=data.get('departamento', ''),
                zona=data['zona'],
                sexo=data['sexo'],
                ficha_sisben=data.get('sisben', ''),
                estado='Pendiente'
            )

            print(f"Inserting: {nueva_solicitud}")
            db.session.add(nueva_solicitud)
            db.session.commit()

            return jsonify({"mensaje": "Solicitud procesada correctamente"}), 201

        except IntegrityError as e:
            db.session.rollback()
            logging.error(f"IntegrityError: {str(e)}")
            return jsonify({"error": "El número de documento ya existe en la base de datos"}), 409

        except Exception as e:
            db.session.rollback()
            logging.error(f"Exception: {str(e)}")
            return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

@app.route('/urgencia')
def urgencia():
    return render_template('urgencia.html')


@app.route('/login_usuarios', methods=['GET', 'POST'])
def login_usuarios():
    if request.method == 'GET':
        return render_template('login_usuarios.html')

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        tipo_documento = data.get('tipo_documento', '').strip()
        numero_documento = data.get('numero_documento', '').strip()
        password = data.get('password', '').strip()

        if not tipo_documento or not numero_documento or not password:
            return jsonify({"status": "error", "message": "Todos los campos son obligatorios"}), 400

        usuario = Usuario.query.filter_by(tipo_documento=tipo_documento, numero_documento=numero_documento).first()

        if not usuario:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

        if usuario.rol.strip().lower() != "paciente":
            return jsonify({"status": "error", "message": "Acceso restringido. Solo los pacientes pueden iniciar sesión"}), 403

        # Verificar contraseña (aquí puedes encriptar con hash si usas)
        if not check_password_hash(usuario.password, password) and usuario.password != password:
            return jsonify({"status": "error", "message": "Contraseña incorrecta"}), 401
        # Verificar si el usuario está activo
          
        

        # Iniciar sesión
        login_user(usuario, remember=True)
        session.permanent = True

        print(f"✅ Usuario logueado: {usuario.numero_documento}, Rol: {usuario.rol}, Sesión permanente: {session.permanent}")

        # Validar si debe cambiar la contraseña
        if usuario.debe_cambiar_clave:
           session['mostrar_modal'] = True
           return jsonify({
             "status": "success",
             "redirect_url": "/portal_paciente",
             "debe_cambiar_clave": True
        }), 200


        return jsonify({
            "status": "success",
            "redirect_url": "/portal_paciente",
            "mostrar_modal": False  # bandera para el modal
        }), 200

    except Exception as e:
        print(f"❌ Error en el login: {str(e)}")
        return jsonify({"status": "error", "message": f"Error interno: {str(e)}"}), 500

def paciente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión.", "danger")
            return redirect(url_for("login_usuarios"))

        if current_user.rol.strip().lower() != "paciente":
            flash("Acceso denegado.", "danger")
            return redirect(url_for("login_usuarios"))

        return f(*args, **kwargs)

    return decorated_function


@app.route('/portal_paciente')
@paciente_required
def portal_paciente():
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    totalcitas = Cita.query.filter_by(paciente_id=paciente.id,estado='Programada').count()
    totalcitas_atendidas = Cita.query.filter_by(paciente_id=paciente.id,estado='Atendida').count()
    totalmedicamentos = RegistroRetiroMedicamento.query.filter_by(paciente_id=paciente.id).count()                                              
    todas_citas = Cita.query.filter_by(paciente_id=paciente.id).all()
    # Obtener citas programadas como recordatorio para el paciente
    citas = Cita.query.filter(
    Cita.paciente_id == paciente.id,
    Cita.estado == 'Programada',
    Cita.fecha.between(datetime.now(), datetime.now() + timedelta(days=10))
   ).all()
    
    medicamentos_asignados = RegistroRetiroMedicamento.query.filter_by(paciente_id=paciente.id).all()

    
    # Obtener los slides activos y ordenados para mostrar en el slider
    slides = Slide.query.filter_by(activo=True).order_by(Slide.orden).all()
    
    return render_template('usuario_dasword.html' ,paciente=paciente ,totalcitas=totalcitas,
                           totalmedicamentos=totalmedicamentos,
                           totalcitas_atendidas=totalcitas_atendidas,
                           citas=citas,todas_citas=todas_citas,
                           slides=slides,medicamentos_asignados=medicamentos_asignados,debe_cambiar_clave=current_user.debe_cambiar_clave)

from werkzeug.security import generate_password_hash, check_password_hash
@app.route('/cambiar_clave', methods=['POST'])
@paciente_required
def cambiar_clave():
    try:
        data = request.get_json()

        nueva_clave = data.get("nueva_clave", "").strip()

        if not nueva_clave:
            return jsonify({"status": "error", "message": "La nueva contraseña es obligatoria"}), 400

        # Encriptar nueva contraseña
        hashed_password = generate_password_hash(nueva_clave)

        # Actualizar en la base de datos
        current_user.password = hashed_password
        current_user.debe_cambiar_clave = False  # Ya no necesita cambiarla
        db.session.commit()

        flash("Contraseña actualizada correctamente", "success")
        return jsonify({"status": "success", "message": "Contraseña actualizada correctamente"})

    except Exception as e:
        print(f"❌ Error al cambiar la contraseña: {str(e)}")
        return jsonify({"status": "error", "message": "Error interno al cambiar la contraseña"}), 500

@app.route('/portal_paciente/agendar')
@paciente_required
def agendar():
    
     paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
     return render_template('citas.html' ,paciente=paciente )

@app.route('/api/guardar_cita', methods=['POST'])
def guardar_cita():
    data = request.json
    print("📩 Datos recibidos:", data)

    
    try:
        # Buscar paciente en la tabla Paciente usando el número de documento
        paciente = Paciente.query.filter_by(numero_documento=data.get('numero_documento')).first()
        
        # Verificar si el paciente existe
        if not paciente:
            print("🚨 Paciente no encontrado en la base de datos.")
            return jsonify({'success': False, 'message': 'Paciente no encontrado'}), 404

        # Mostrar la información del paciente encontrado para depurar
        print("📌 Paciente encontrado:", paciente.__dict__)

        # Obtener solo el ID del paciente (evitar usuario_id)
        paciente_id = paciente.id  # Tomar solo el ID principal del paciente
        print("✅ ID de paciente obtenido:", paciente_id)

        # Convertir la fecha de la cita correctamente
        fecha_cita = datetime.strptime(data.get('fecha'), '%Y-%m-%d').date()
        print("✅ Fecha de la cita convertida correctamente:", fecha_cita)

        # Convertir la hora de la cita
        hora_cita_str = data.get('hora')
        if hora_cita_str:
            try:
                # Verificar si la hora está en formato AM/PM o 24 horas
                if "AM" in hora_cita_str or "PM" in hora_cita_str:
                    hora_cita = datetime.strptime(hora_cita_str, "%I:%M %p").time()
                else:
                    hora_cita = datetime.strptime(hora_cita_str, "%H:%M").time()
                print("✅ Hora de la cita convertida correctamente:", hora_cita)
            except ValueError:
                print("🚨 Error: Formato de hora inválido:", hora_cita_str)
                return jsonify({'success': False, 'message': 'Formato de hora inválido'}), 400
        else:
            print("🚨 Error: No se proporcionó una hora válida")
            return jsonify({'success': False, 'message': 'Debe proporcionar una hora válida'}), 400

        # Verificar si ya existe una cita en la misma fecha y hora
        cita_existente = Cita.query.filter_by(fecha=fecha_cita, hora=hora_cita).first()
        if cita_existente:
            print("🚨 Ya existe una cita en la misma fecha y hora.")
            return jsonify({'success': False, 'message': 'Ya existe una cita en esa fecha y hora. Por favor, elija otra hora.'}), 400

        # Generar código de confirmación
        codigo_confirmacion = secrets.token_hex(3).upper()
        print("✅ Código de confirmación generado:", codigo_confirmacion)

        # Crear nueva cita
        nueva_cita = Cita(
            paciente_id=paciente_id,  # Usar solo el ID del paciente
            tipo_servicio=data.get('tipo_servicio'),
            especialidad=data.get('especialidad'),
            tipo_examen=data.get('tipo_examen'),
            motivo=data.get('motivo'),
            fecha=fecha_cita,
            hora=hora_cita,
            codigo_confirmacion=codigo_confirmacion,
            estado='Programada'
        )

        print("📌 Objeto Cita creado:", nueva_cita.__dict__)

        # Guardar la cita en la base de datos
        db.session.add(nueva_cita)
        db.session.commit()
        print("✅ Cita guardada en la base de datos con ID:", nueva_cita.id)

        # Formato seguro para la hora
        try:
            if hasattr(nueva_cita.hora, 'strftime'):  # Verifica si tiene el método strftime
                hora_formateada = nueva_cita.hora.strftime('%H:%M')
            else:
                hora_formateada = str(nueva_cita.hora)
        except Exception as e:
            print(f"Error al formatear la hora: {e}")
            hora_formateada = str(nueva_cita.hora)

        # Responder con éxito
        return jsonify({
            'success': True,
            'message': 'Cita guardada correctamente',
            'cita': {
                'id': nueva_cita.id,
                'paciente_id': nueva_cita.paciente_id,  # Mostrar solo el ID del paciente
                'tipo_servicio': nueva_cita.tipo_servicio,
                'especialidad': nueva_cita.especialidad,
                'tipo_examen': nueva_cita.tipo_examen,
                'motivo': nueva_cita.motivo,
                'fecha': nueva_cita.fecha.strftime('%Y-%m-%d'),
                'hora': hora_formateada,
                'codigo_confirmacion': nueva_cita.codigo_confirmacion,
                'estado': nueva_cita.estado
            }
        })

    except Exception as e:
        # Manejo de errores
        db.session.rollback()
        error_trace = traceback.format_exc()
        print("🚨 Error al guardar la cita:", e)
        print(error_trace)
        return jsonify({'success': False, 'message': 'Error al guardar la cita', 'error': str(e), 'trace': error_trace}), 500
    
    
@app.route('/api/verificar_citas', methods=['POST'])
@paciente_required
def verificar_citas():
    data = request.json
    print(f"🔍 Buscando citas para {data.get('tipo_documento')} - {data.get('numero_documento')}")

    try:
        # Buscar el paciente en la base de datos
        paciente = Paciente.query.filter_by(numero_documento=data.get('numero_documento')).first()
        if not paciente:
            print("🚨 Paciente no encontrado.")
            return jsonify({'success': False, 'message': 'Paciente no encontrado'}), 404

        print(f"✅ Paciente encontrado con ID: {paciente.id}")

        # Buscar citas asociadas al paciente
        citas = Cita.query.filter_by(paciente_id=paciente.id).order_by(Cita.fecha, Cita.hora).all()

        if not citas:
            print("📭 No hay citas registradas para este paciente")
            return jsonify({'success': True, 'message': 'No hay citas registradas', 'citas': []}), 200

        # Convertir las citas a formato JSON
        citas_json = [{
            'id': c.id,
            'fecha': c.fecha.strftime('%Y-%m-%d'),
            'hora': (datetime.min + c.hora).time().strftime('%H:%M') if isinstance(c.hora, timedelta) else c.hora.strftime('%H:%M'),
            'tipo_servicio': c.tipo_servicio,
            'especialidad': c.especialidad,
            'estado': c.estado
        } for c in citas]

        print(f"✅ {len(citas)} citas encontradas.")
        return jsonify({'success': True, 'citas': citas_json}), 200

    except Exception as e:
        print(f"🚨 Error en la verificación de citas: {str(e)}")
        return jsonify({'success': False, 'message': 'Error en la verificación de citas', 'error': str(e)}), 500

@app.route('/paciente/citas', methods=['GET'])
@paciente_required
def ver_citas_paciente():
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    if not paciente:
        flash('No se encontró un paciente asociado a su cuenta.')
        return redirect(url_for('login_usuarios'))
    
    # Filtrar solo las citas programadas
    citas_programadas = Cita.query.filter_by(paciente_id=paciente.id, estado='Programada').all()
    
    return render_template('ver_citaspacientes.html', paciente=paciente, citas=citas_programadas)

@app.route('/api/citas_paciente')
@paciente_required
def citas_paciente():
    
    print("======= INICIO DE API CITAS_PACIENTE =======")
    print("IP de solicitud:", request.remote_addr)
    
    # Verificar autenticación
    if not current_user.is_authenticated:
        print("ERROR: Usuario no autenticado")
        return jsonify({
            'success': False, 
            'message': 'Usuario no autenticado. Por favor inicie sesión.', 
            'citas': []
        })
    
    print("Usuario autenticado ID:", current_user.id)
    print("Tipo de usuario:", type(current_user).__name__)
    
    # Buscar el paciente asociado al usuario
    try:
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente:
            print(f"ERROR: No se encontró paciente para usuario_id={current_user.id}")
            return jsonify({
                'success': False, 
                'message': 'No se encontró un paciente asociado a su cuenta.', 
                'citas': []
            })
        
        print(f"Paciente encontrado ID: {paciente.id}, Nombre: {paciente.nombre if hasattr(paciente, 'nombre') else 'N/A'}")
        
        # Buscar citas asociadas al paciente
        citas = Cita.query.filter_by(paciente_id=paciente.id, estado='Programada').order_by(Cita.fecha, Cita.hora).all()
        print(f"Cantidad de citas encontradas: {len(citas)}")
        
        # Convertir citas a formato JSON
        citas_json = []
        for i, cita in enumerate(citas):
            print(f"\nProcesando cita #{i+1}, ID: {cita.id}")
            
            # Formatear la hora correctamente según el tipo de dato
            hora_str = None
            print(f"Tipo de dato de hora: {type(cita.hora).__name__}")
            
            try:
                if isinstance(cita.hora, timedelta):
                    hora_str = (datetime.min + cita.hora).time().strftime('%H:%M')
                elif hasattr(cita.hora, 'strftime'):
                    hora_str = cita.hora.strftime('%H:%M')
                else:
                    hora_str = str(cita.hora)
                
                print(f"Hora formateada: {hora_str}")
            except Exception as e:
                print(f"ERROR al formatear hora: {str(e)}")
                hora_str = "Error: " + str(e)
            
            try:
                fecha_str = cita.fecha.strftime('%Y-%m-%d')
                print(f"Fecha formateada: {fecha_str}")
            except Exception as e:
                print(f"ERROR al formatear fecha: {str(e)}")
                fecha_str = "Error: " + str(e)
            
            cita_dict = {
                'id': cita.id,
                'paciente_id': cita.paciente_id,
                'tipo_servicio': getattr(cita, 'tipo_servicio', 'No especificado'),
                'especialidad': getattr(cita, 'especialidad', None),
                'tipo_examen': getattr(cita, 'tipo_examen', None),
                'motivo': getattr(cita, 'motivo', None),
                'fecha': fecha_str,
                'hora': hora_str,
                'codigo_confirmacion': getattr(cita, 'codigo_confirmacion', None),
                'estado': getattr(cita, 'estado', 'Desconocido')
            }
            
            print(f"Cita formateada: {json.dumps(cita_dict)}")
            citas_json.append(cita_dict)
        
        # Devolver JSON en lugar de renderizar una plantilla
        return jsonify({
            'success': True,
            'message': 'Citas obtenidas exitosamente',
            'citas': citas_json
        })
    
    except Exception as e:
        print(f"EXCEPCIÓN INESPERADA: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Error interno: {str(e)}', 
            'citas': []
        }), 500
        
        
@app.route('/api/cancelar_cita/<int:cita_id>', methods=['DELETE'])
@paciente_required
def cancelar_cita(cita_id):
    try:
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente:
            return jsonify({'success': False, 'message': 'No se encontró un paciente asociado.'}), 404

        cita = Cita.query.filter_by(id=cita_id, paciente_id=paciente.id).first()
        if not cita:
            return jsonify({'success': False, 'message': 'Cita no encontrada o no autorizada para cancelar.'}), 404

        db.session.delete(cita)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Cita cancelada exitosamente.'}), 204  # No Content

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500


@app.route('/api/hitorial_cita')
@paciente_required
def historial_cita():
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    if not paciente:
        flash('No se encontró un paciente asociado a su cuenta.')
        return redirect(url_for('login_usuarios'))
    
    citas = Cita.query.filter_by(paciente_id=paciente.id, estado='Atendida').all()
    
    # Convertir las citas a formato JSON para enviarlas al frontend
    citas_json = []
    for i, cita in enumerate(citas):
        print(f"\nProcesando cita #{i+1}, ID: {cita.id}")
        
        # Formatear la hora correctamente según el tipo de dato
        hora_str = None
        print(f"Tipo de dato de hora: {type(cita.hora).__name__}")
        
        try:
            if isinstance(cita.hora, timedelta):
                hora_str = (datetime.min + cita.hora).time().strftime('%H:%M')
            elif hasattr(cita.hora, 'strftime'):
                hora_str = cita.hora.strftime('%H:%M')
            else:
                hora_str = str(cita.hora)
            
            print(f"Hora formateada: {hora_str}")
        except Exception as e:
            print(f"ERROR al formatear hora: {str(e)}")
            hora_str = "Error: " + str(e)
        
        try:
            fecha_str = cita.fecha.strftime('%Y-%m-%d')
            print(f"Fecha formateada: {fecha_str}")
        except Exception as e:
            print(f"ERROR al formatear fecha: {str(e)}")
            fecha_str = "Error: " + str(e)
        
        cita_dict = {
            'id': cita.id,
            'paciente_id': cita.paciente_id,
            'tipo_servicio': getattr(cita, 'tipo_servicio', 'No especificado'),
            'especialidad': getattr(cita, 'especialidad', None),
            'tipo_examen': getattr(cita, 'tipo_examen', None),
            'motivo': getattr(cita, 'motivo', None),
            'fecha': fecha_str,
            'hora': hora_str,
            'codigo_confirmacion': getattr(cita, 'codigo_confirmacion', None),
            'estado': getattr(cita, 'estado', 'Desconocido')
        }
        
        print(f"Cita formateada: {json.dumps(cita_dict)}")
        citas_json.append(cita_dict)
    
    # Devolver JSON en lugar de renderizar una plantilla
    return jsonify({
        'success': True,
        'message': 'Citas obtenidas exitosamente',
        'citas': citas_json
    })

@app.route('/historial_cita')
@paciente_required
def historial_cita_view():
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    if not paciente:
        flash('No se encontró un paciente asociado a su cuenta.')
        return redirect(url_for('login_usuarios'))
    
    citas = Cita.query.filter_by(paciente_id=paciente.id, estado='Atendida').all()
    
    
    return render_template('citas_historial.html', titulo="Historial de Citas", seccion_activa="citas" , citas=citas ,paciente=paciente)


@app.route('/mis-medicamentos')
def mis_medicamentos_view():
    # Consultar al paciente asociado al usuario actual
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    
    if not paciente:
        flash("No se encontró un paciente asociado a su cuenta.", "danger")
        return redirect(url_for('login_usuarios'))
    
    # Consultar al usuario que atendió la cita
    retiros = RegistroRetiroMedicamento.query.filter_by(paciente_id=paciente.id).all()
    usuario = Usuario.query.filter_by(id=current_user.id).first()

    if not usuario:
        flash("No se encontró información del usuario que atendió la cita.", "warning")
    
    return render_template('medicamentos.html', titulo="Mis Medicamentos", seccion_activa="medicamentos",
        paciente=paciente,
        usuario=usuario,
        retiros=retiros
    )

@app.route('/api/medicamentos_recetados')
def medicamentos_recetados():
    print("\n======= INICIO DE API MEDICAMENTOS_RECETADOS =======")
    
    if not current_user.is_authenticated:
        print("Error: Usuario no autenticado")
        return jsonify({'success': False, 'message': 'Usuario no autenticado.', 'medicamentos_recetados': []})
    
    print(f"Usuario autenticado: ID={current_user.id}")
    
    try:
        print("Buscando paciente asociado al usuario...")
        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        
        if not paciente:
            print(f"Error: No se encontró paciente para el usuario_id={current_user.id}")
            return jsonify({'success': False, 'message': 'Paciente no encontrado.', 'medicamentos_recetados': []})
        
        # Corregido: Usamos solo el ID del paciente en el log, sin acceder a "nombre"
        print(f"Paciente encontrado: ID={paciente.id}")
        
        print(f"Buscando registros de retiro de medicamentos para paciente_id={paciente.id}...")
        retiros = RegistroRetiroMedicamento.query.filter_by(paciente_id=paciente.id).all()
        print(f"Registros de retiro encontrados: {len(retiros)}")
        
        
        medicamentos_recetados = []
        
        for idx, retiro in enumerate(retiros):
            print(f"\nProcesando retiro #{idx+1}: ID={retiro.id}, medicamento_id={retiro.medicamento_id}")
            
            medicamento = Medicamento.query.get(retiro.medicamento_id)
            if not medicamento:
                print(f"  Error: No se encontró medicamento con ID={retiro.medicamento_id}")
                continue
            
            print(f"  Medicamento encontrado: {medicamento.nombre}")
            stock = medicamento.stock if medicamento.stock is not None else 0
            disponible = stock > 0
            print(f"  Stock: {stock}, Disponible: {disponible}")
            
            # Verificar otros campos importantes
            
            medicamento_data = {
                'medicamento_id': medicamento.id,
                'nombre': medicamento.nombre,
                'descripcion': medicamento.descripcion,
                'cantidad': retiro.cantidad,
                'indicacion': retiro.indicacion,
                'fecha_registro': retiro.fecha_registro.strftime('%Y-%m-%d') if hasattr(retiro, 'fecha_registro') and retiro.fecha_registro else None,
                'fecha_tratamiento_fin': retiro.fecha_tratamiento_fin.strftime('%Y-%m-%d') if hasattr(retiro, 'fecha_tratamiento_fin') and retiro.fecha_tratamiento_fin else None,
                'disponible': disponible,
                'stock': stock
            }
            
            medicamentos_recetados.append(medicamento_data)
            print(f"  Datos añadidos al resultado: {medicamento_data}")
        
        print(f"\nTotal de medicamentos procesados: {len(medicamentos_recetados)}")
        print("======= FIN DE API MEDICAMENTOS_RECETADOS =======\n")
        
        return jsonify({'success': True, 'medicamentos_recetados': medicamentos_recetados})
    
    except Exception as e:
        print("ERROR DETECTADO:")
        import traceback
        traceback.print_exc()
        print("======= FIN DE API MEDICAMENTOS_RECETADOS (CON ERROR) =======\n")
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}', 'medicamentos_recetados': []})
    
    
    
@app.route('/api/retirar_medicamento', methods=['POST'])
def retirar_medicamento():
    try:
        data = request.json
        medicamento_id = data.get('medicamento_id')
        cantidad = data.get('cantidad', 1)

        paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
        if not paciente:
            return jsonify({'success': False, 'message': 'Paciente no encontrado'})

        medicamento = Medicamento.query.get(medicamento_id)
        if not medicamento:
            return jsonify({'success': False, 'message': 'Medicamento no encontrado'})

        atencion = AtencionCita.query.filter_by(medicamento_id=medicamento.id).join(HistorialCita).filter_by(paciente_id=paciente.id).first()
        if not atencion:
            return jsonify({'success': False, 'message': 'Este medicamento no ha sido recetado al paciente'})

        if medicamento.stock < cantidad:
            return jsonify({'success': False, 'message': 'Stock insuficiente'})

        medicamento.stock -= cantidad
        db.session.add(medicamento)

        retiro = RegistroRetiroMedicamento(
            paciente_id=paciente.id,
            medicamento_id=medicamento.id,
            cantidad=cantidad,
            fecha_retiro=datetime.utcnow()
        )
        db.session.add(retiro)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Medicamento retirado correctamente', 'nuevo_stock': medicamento.stock})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al retirar medicamento: {str(e)}'})
    
@app.route('/cambiar_contrasena')
def cambiar_contrasena():
    return render_template('cambiar_contrasena.html')

@app.route('/portal_paciente/perfil', methods=['GET'])
@paciente_required
def perfil_usuario():

    if current_user.rol.strip().lower() != "paciente":
        return redirect(url_for('home'))
    
    # Buscar al paciente en la tabla "pacientes"
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    
    if not paciente:
        flash("No se encontraron datos del paciente.", "warning")
        return redirect(url_for('home'))
    

    return render_template('perfil_usuario.html', paciente=paciente)


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/actualizar_paciente', methods=['POST'])
def actualizar_usuario():
    data = request.form
    usuario_id = data.get('id')

    print("ID recibido:", usuario_id)

    usuario = Usuario.query.get(usuario_id)
    paciente = Paciente.query.filter_by(usuario_id=usuario_id).first()

    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    usuario.telefono = data.get('telefono', usuario.telefono)
    usuario.direccion = data.get('direccion', usuario.direccion)
    usuario.correo = data.get('correo', usuario.correo)

    if "password" in data and data.get('password'):
        usuario.password = data.get('password')

    # 📌 **Manejo de la imagen**
    filename = None  # Definir filename antes del bloque condicional

    if 'imagen_usuario' in request.files:
        file = request.files['imagen_usuario']
        if file.filename != '':
            filename = secure_filename(f"img_{usuario_id}.png")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # 🔹 Guardar la ruta correctamente con slashes ('/')
            usuario.imagen_usuario = f"uploads/{filename}".replace("\\", "/")
            if paciente:
                paciente.imagen_usuario = f"uploads/{filename}".replace("\\", "/")

    if paciente:
        paciente.telefono = usuario.telefono
        paciente.direccion = usuario.direccion
        paciente.correo = usuario.correo

    db.session.commit()

    # ✅ Evitar usar filename si no se subió ninguna imagen
    if filename:
        return jsonify({"imagen_url": url_for('static', filename=f"uploads/{filename}")})
    else:
        return jsonify({"mensaje": "Usuario actualizado correctamente, sin cambios en la imagen."})

    






@app.route('/logout')
@login_required
def logout():
    logout_user()  # Cierra la sesión del usuario actual
    flash('Has cerrado sesión con éxito', 'success')  # Mensaje de éxito
    return redirect(url_for('login_admin')) 

@app.route('/salir')
@paciente_required
def salir():
    logout_user()  
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('login_usuarios')) 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

