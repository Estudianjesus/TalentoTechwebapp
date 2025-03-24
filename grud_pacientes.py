from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from database import db
from models import Paciente, Usuario

pacientes_bp = Blueprint('pacientes', __name__)


@pacientes_bp.route('/lis')
def index():
      Pacientes = Paciente.query.all()
      return render_template('admin/afiliado_paciente.html', Pacientes = Pacientes , usuario=current_user )
  
@pacientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    usuario = Usuario.query.filter_by(numero_documento=paciente.numero_documento).first()

    if request.method == 'POST':
        # Editar datos de Paciente
        paciente.primer_nombre = request.form['primer_nombre']
        paciente.segundo_nombre = request.form['segundo_nombre']
        paciente.primer_apellido = request.form['primer_apellido']
        paciente.segundo_apellido = request.form['segundo_apellido']
        paciente.tipo_documento = request.form['tipo_documento']
        paciente.numero_documento = request.form['numero_documento']
        paciente.correo = request.form['correo']
        paciente.direccion = request.form['direccion']
        paciente.departamento = request.form['departamento']
        paciente.zona = request.form['zona']
        paciente.sexo = request.form['sexo']
        paciente.ficha_sisben = request.form['ficha_sisben']

        # Actualizar datos de Usuario
        if usuario:
            usuario.tipo_documento = request.form['tipo_documento']
            usuario.numero_documento = request.form['numero_documento']
            usuario.usuario = request.form['numero_documento']  # Usuario es el número de documento
            usuario.correo = request.form['correo']
            usuario.telefono = request.form['telefono']
            usuario.direccion = request.form['direccion']

            # Si el usuario ingresó una nueva contraseña, la cambiamos
            if request.form['password']:
                usuario.password = (request.form['password'])

        # Guardar cambios en la base de datos
        db.session.commit()
        flash('Paciente y usuario actualizados correctamente')
        
        return redirect(url_for('pacientes.index'))

    return render_template('edit.html', paciente=paciente, usuario=usuario)

  
    


