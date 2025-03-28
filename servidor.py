from functools import wraps
import logging
import os
import secrets
from sqlite3 import IntegrityError
import time
import traceback
from urllib.parse import urljoin, urlparse
from sqlalchemy import text
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from database import db
from models import Cita, Medicamento, solicitudes_afiliacion, Usuario, Paciente
from flask_wtf import FlaskForm
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from datetime import datetime





app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3307/eps_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


# 🔹 Inicializar la base de datos con la aplicación
db.init_app(app)
migrate = Migrate(app, db)

# 🔹 Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_admin"  # Redirección si el usuario no está autenticado
login_manager.session_protection = "strong" 


# 🔹 Verificar conexión a la base de datos
with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print("✅ Conexión exitosa a la base de datos")
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
@app.route('/')
def home():
    return render_template('index.html')

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
            "Subadministrador": url_for('sudadmin'),
            "Farmacia": url_for('dashboard_farmacia')
        }

    if request.method == 'GET':
        return render_template('login_admin.html')

    # Asegurar que la solicitud tiene JSON válido
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
    flash('Inicio de sesión exitoso', 'success')

    rutas = {
        "Administrador": url_for('admin'),
        "Subadministrador": url_for('sudadmin'),
        "Farmacia": url_for('dashboard_farmacia')
    }

    return jsonify({"status": "success", "redirect_url": rutas.get(user.rol, url_for('login_admin')), "clear_fields": False})


   

@app.route('/admin')
@login_required
def admin():
    
    return render_template('admin/admin_dashboard.html', usuario=current_user)

@app.route('/admin/perfil', methods=['GET'])
@login_required
def perfil():
    # Si el usuario NO tiene rol permitido, lo rediriges a home
    if current_user.rol not in ['Administrador', 'Subadministrador', 'Farmacia']:
        return redirect(url_for('home'))
    
    # 🔹 Si el usuario es de Farmacia, lo mandamos a su perfil específico
    if current_user.rol == 'Farmacia':
        return redirect(url_for('perfil_far'))  # Asegúrate de tener esta ruta

    # Obtener todas las solicitudes si es admin o subadmin
    solicitudes = solicitudes_afiliacion.query.order_by(
        solicitudes_afiliacion.estado != 'Rechazada',
        solicitudes_afiliacion.fecha_solicitud.desc()
    ).all()

    return render_template('admin/perfil_dashboard.html', solicitudes=solicitudes, usuario=current_user)



@app.route('/admin/solicitudes', methods=['GET'])
@login_required
def ver_solicitudes():
    if current_user.rol != 'Administrador':
        return redirect(url_for('home'))
    
    # Obtener todas las solicitudes desde la base de datos
    solicitudes = solicitudes_afiliacion.query.all()
    
    solicitudes_json = [{
        'id': s.id,
        'primer_nombre': s.primer_nombre,
        'primer_apellido': s.primer_apellido,
        'tipo_documento': s.tipo_documento,
        'numero_documento': s.numero_documento,
        'zona': s.zona,
        'estado': s.estado
    } for s in solicitudes]
    
    # Obtener el timestamp de la última modificación
    ultimo_timestamp = round(time.time() * 1000)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'solicitudes': solicitudes_json,
            'timestamp': ultimo_timestamp
        })
    
    # Si no es AJAX, renderizar el template normalmente
    return render_template('admin/solicitud_admin.html', solicitudes=solicitudes_json, usuario=current_user, timestamp=ultimo_timestamp)

@app.route('/admin/solicitudes/aceptar/<int:solicitud_id>', methods=['POST'])
@login_required
def aceptar_solicitud(solicitud_id):
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
            afiliado=True
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
    if current_user.rol != 'Administrador':
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
    paciente = Paciente.query.get(id)  # Obtener paciente por ID

    if not paciente:
        return redirect(url_for('lista_pacientes'))  # Redirige si no existe

    return render_template('admin/ver_detalles.html', paciente=paciente ,usuario=current_user)

@app.route('/admin/paciente/editar/<int:id>', methods=['GET'])
@login_required
def editar_paciente(id):
    if current_user.rol != 'Administrador':
        return redirect(url_for('home'))

    paciente = Paciente.query.get_or_404(id)
    usuario = Usuario.query.filter_by(numero_documento=paciente.numero_documento).first()
    
    return render_template('admin/editar_paciente.html', paciente=paciente, usuario=usuario)

@app.route('/admin/paciente/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_paciente(id):
    if current_user.rol != 'Administrador':
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

    try:
        if usuario:
            db.session.delete(usuario)

        db.session.delete(paciente)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Paciente eliminado correctamente'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error al eliminar paciente: {str(e)}'}), 500


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

MEDICAMENTOS_UPLOAD_FOLDER = 'static/medicamentos/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['MEDICAMENTOS_UPLOAD_FOLDER'] = MEDICAMENTOS_UPLOAD_FOLDER

# Asegurar que la carpeta exista
os.makedirs(MEDICAMENTOS_UPLOAD_FOLDER, exist_ok=True)

# Función para validar archivos permitidos
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/dashboard_farmacia/medicamentos/add_medicamento', methods=['GET', 'POST'])
@login_required
def agregar_medicamento():
    if request.method == 'GET':
        return render_template('farmacia/agregar_medicamento.html')

    if request.method == 'POST':
        try:
            usuario_actual = db.session.query(Usuario).filter_by(id=current_user.id).first()
            if not usuario_actual:
                flash('❌ Usuario no encontrado', 'danger')
                return redirect(url_for('agregar_medicamento'))

            # Obtener datos del formulario
            nombre_medicamento = request.form['nombre']
            descripcion = request.form['descripcion']
            tipo = request.form['tipo']
            concentracion = request.form['concentracion']
            presentacion = request.form['presentacion']
            laboratorio = request.form['laboratorio']
            fecha_vencimiento = request.form['fecha_vencimiento']
            stock = int(request.form['stock'])

            # Verificar si el medicamento ya existe con el mismo tipo y concentración
            medicamento_existente = db.session.query(Medicamento).filter_by(tipo=tipo, concentracion=concentracion).first()
            if medicamento_existente:
                flash('⚠️ Ya existe un medicamento con el mismo tipo y concentración.', 'warning')
                return redirect(url_for('agregar_medicamento'))

            # Manejo de la imagen
            imagen = request.files.get('imagen')
            imagen_filename = None

            if imagen and allowed_file(imagen.filename):
                imagen_filename = secure_filename(imagen.filename)
                imagen_path = os.path.join(app.config['MEDICAMENTOS_UPLOAD_FOLDER'], imagen_filename)
                os.makedirs(app.config['MEDICAMENTOS_UPLOAD_FOLDER'], exist_ok=True)
                imagen.save(imagen_path)

            # Crear el objeto Medicamento
            nuevo_medicamento = Medicamento(
                nombre=nombre_medicamento,
                descripcion=descripcion,
                tipo=tipo,
                concentracion=concentracion,
                presentacion=presentacion,
                laboratorio=laboratorio,
                fecha_vencimiento=datetime.strptime(fecha_vencimiento, '%Y-%m-%d') if fecha_vencimiento else None,
                stock=stock,
                imagen_url=f"medicamentos/{imagen_filename}" if imagen_filename else None
            )

            db.session.add(nuevo_medicamento)
            db.session.commit()  # ✅ Guardar en la base de datos

            flash('✅ Medicamento agregado con éxito', 'success')
            return redirect(url_for('agregar_medicamento'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al agregar medicamento: {str(e)}', 'danger')
            return redirect(url_for('agregar_medicamento'))
        
        finally:
            db.session.close()  # Cierra la sesión correctamente

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
        Medicamento.fecha_vencimiento,
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
        'fecha_vencimiento': m.fecha_vencimiento.strftime('%Y-%m-%d') if m.fecha_vencimiento else "N/A",
        'estado': m.estado,
        'stock': m.stock,
        'fecha_ingreso': m.fecha_ingreso.strftime('%Y-%m-%d'),
       'imagen_url': url_for('static', filename=m.imagen_url)


    } for m in medicamentos]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'medicamentos': medicamentos_json,
            'timestamp': round(time.time() * 1000)
        })
    
    return render_template('ver_medicamentos.html', medicamentos=medicamentos_json, usuario=current_user, timestamp=time.time())



@app.route('/sudadmin')
@login_required
def sudadmin():
    return render_template('sudabmin_dashboard.html', usuario=current_user)


















@app.route('/consulta_general')
def consulta_general():
    return render_template('consulta_general.html')

@app.route('/contacto')
def contacto():
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

        # Verificar contraseña encriptada
        if usuario.password != password:
          return jsonify({"status": "error", "message": "Contraseña incorrecta"}), 401

        # Iniciar sesión
        login_user(usuario,remember=True)

        # Marcar la sesión como permanente
        session.permanent = True

        print(f"✅ Usuario logueado: {usuario.numero_documento}, Rol: {usuario.rol}, Sesión permanente: {session.permanent}")
        
        return jsonify({"status": "success", "redirect_url": "/portal_paciente"})

    except Exception as e:
        print(f"❌ Error en el login: {str(e)}")
        return jsonify({"status": "error", "message": f"Error interno: {str(e)}"}), 500


@app.before_request
def renovar_sesion():
    session.modified = True

def paciente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión.", "danger")
            return redirect(url_for("login_usuarios"))

        print(f"Usuario autenticado: {current_user.numero_documento}, Rol: {current_user.rol}")  # 🔍 Verifica el rol

        if current_user.rol.strip().lower() != "paciente":
            flash("Acceso denegado.", "danger")
            return redirect(url_for("login_usuarios"))

        return f(*args, **kwargs)

    return decorated_function



@app.route('/portal_paciente')
@paciente_required
def portal_paciente():
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    return render_template('usuario_dasword.html' ,paciente=paciente)


@app.route('/portal_paciente/inicio')
@paciente_required
def Inicio():
    paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
    return render_template('usuario_dasword.html' ,paciente=paciente)


@app.route('/portal_paciente/agendar')
@paciente_required
def agendar():
    
     paciente = Paciente.query.filter_by(usuario_id=current_user.id).first()
     return render_template('citas.html' ,paciente=paciente )


@app.route('/api/guardar_cita', methods=['POST'])
def guardar_cita():
    data = request.json
    print("📩 Datos recibidos:", data)  # 🔍 Depuración: Verificar datos entrantes

    try:
        # 🔍 Obtener ID del paciente desde la sesión o buscar por número de documento
        paciente_id = session.get('paciente_id')
        print("📌 Paciente ID en sesión:", paciente_id)

        if not paciente_id:
            paciente = Paciente.query.filter_by(numero_documento=data.get('numero_documento')).first()
            if not paciente:
                print("🚨 Paciente no encontrado en la base de datos.")
                return jsonify({'success': False, 'message': 'Paciente no encontrado'}), 404
            paciente_id = getattr(paciente, 'usuario_id', paciente.id)  # Verifica si tiene `usuario_id`
            print("✅ Paciente encontrado, ID:", paciente_id)

        # 📌 Verificar si el usuario realmente existe en la tabla `Usuario`
        usuario = Usuario.query.get(paciente_id)
        if not usuario:
            print(f"🚨 No existe un usuario con ID {paciente_id}")
            return jsonify({'success': False, 'message': f'No existe un usuario con ID {paciente_id}'}), 400

        # 📅 Convertir fecha correctamente
        fecha_cita = datetime.strptime(data.get('fecha'), '%Y-%m-%d').date()
        print("✅ Fecha de la cita convertida correctamente:", fecha_cita)

        # 🕒 Convertir hora correctamente
        hora_cita_str = data.get('hora')
        hora_cita = None
        if hora_cita_str:
            try:
                if "AM" in hora_cita_str or "PM" in hora_cita_str:
                    hora_cita = datetime.strptime(hora_cita_str, "%I:%M %p").time()  # Formato 12H AM/PM
                else:
                    hora_cita = datetime.strptime(hora_cita_str, "%H:%M").time()  # Formato 24H
                print("✅ Hora de la cita convertida correctamente:", hora_cita)
            except ValueError:
                print("🚨 Error: Formato de hora inválido:", hora_cita_str)
                return jsonify({'success': False, 'message': 'Formato de hora inválido'}), 400

        # 🔎 Verificar si ya existe una cita en la misma fecha y hora para **cualquier paciente**
        cita_existente = Cita.query.filter_by(fecha=fecha_cita, hora=hora_cita).first()
        if cita_existente:
            print("🚨 Ya existe una cita en la misma fecha y hora para otro paciente.")
            return jsonify({'success': False, 'message': 'Ya existe una cita en esa fecha y hora. Por favor, elija otra hora.'}), 400

        # 🔐 Generar código de confirmación
        codigo_confirmacion = secrets.token_hex(3).upper()
        print("✅ Código de confirmación generado:", codigo_confirmacion)

        # 🏥 Crear nueva cita
        nueva_cita = Cita(
            paciente_id=paciente_id,
            tipo_servicio=data.get('tipo_servicio'),
            especialidad=data.get('especialidad'),
            tipo_examen=data.get('tipo_examen'),
            motivo=data.get('motivo'),
            fecha=fecha_cita,
            hora=hora_cita,  # 🔥 Asegurando que sea `time`
            codigo_confirmacion=codigo_confirmacion,
            estado='Programada'
        )

        print("📌 Objeto Cita creado:", nueva_cita.__dict__)  # 🔍 Ver el objeto antes de guardar

        db.session.add(nueva_cita)
        db.session.commit()
        print("✅ Cita guardada en la base de datos con ID:", nueva_cita.id)

        # 💾 Formatear hora correctamente para la respuesta
        hora_correcta = (datetime.min + nueva_cita.hora).time()
        formatted_hora = hora_correcta.strftime('%H:%M')

        return jsonify({
            'success': True,
            'message': 'Cita guardada correctamente',
            'cita': {
                'id': nueva_cita.id,
                'paciente_id': nueva_cita.paciente_id,
                'tipo_servicio': nueva_cita.tipo_servicio,
                'especialidad': nueva_cita.especialidad,
                'tipo_examen': nueva_cita.tipo_examen,
                'motivo': nueva_cita.motivo,
                'fecha': nueva_cita.fecha.strftime('%Y-%m-%d'),
                'hora': formatted_hora,  # Formatear correctamente la hora
                'codigo_confirmacion': nueva_cita.codigo_confirmacion,
                'estado': nueva_cita.estado
            },
            'codigo_confirmacion': codigo_confirmacion
        })

    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        print("🚨 Error al guardar la cita:", e)
        print(error_trace)
        return jsonify({'success': False, 'message': 'Error al guardar la cita', 'error': str(e), 'trace': error_trace}), 500

@app.route('/api/verificar_citas', methods=['POST'])
def verificar_citas():
    data = request.json
    print(f"🔍 Buscando citas para {data.get('tipo_documento')} - {data.get('numero_documento')}")

    try:
        # Buscar el usuario (paciente) en la base de datos
        usuario = Usuario.query.filter_by(numero_documento=data.get('numero_documento')).first()
        if not usuario:
            print("🚨 Usuario no encontrado.")
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        print(f"✅ Usuario encontrado con ID: {usuario.id}")

        # Buscar citas asociadas al paciente
        citas = Cita.query.filter_by(paciente_id=usuario.id).order_by(Cita.fecha, Cita.hora).all()

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


@app.route('/api/citas_paciente')
def citas_paciente():
    paciente_id = session.get('paciente_id')
    if not paciente_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    citas = Cita.query.filter_by(paciente_id=paciente_id).order_by(Cita.fecha, Cita.hora).all()
    return jsonify({
        'success': True,
        'citas': [cita.to_dict() for cita in citas]
    })

@app.route('/api/cancelar_cita/<int:cita_id>', methods=['POST'])
def cancelar_cita(cita_id):
    paciente_id = session.get('paciente_id')
    if not paciente_id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    cita = Cita.query.filter_by(id=cita_id, paciente_id=paciente_id).first()
    if not cita:
        return jsonify({'success': False, 'message': 'Cita no encontrada'}), 404
    
    cita.estado = 'Cancelada'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Cita cancelada correctamente'
    })



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

