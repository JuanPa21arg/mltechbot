from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
import subprocess
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

def tiene_sesion(user_id):
    return os.path.exists(f"./.wwebjs_auth/client_{user_id}")


app = Flask(__name__)
app.secret_key = 'clave-secreta-mltech'

# Cargar variables de entorno PostgreSQL
user = os.getenv("PGUSER")
raw_password = os.getenv("PGPASSWORD")
host = os.getenv("PGHOST")
port = os.getenv("PGPORT")
db = os.getenv("PGDATABASE")

# Validar que todas existan
if not all([user, raw_password, host, port, db]):
    raise RuntimeError("❌ Faltan variables de entorno para PostgreSQL")

# Codificar contraseña si tiene caracteres especiales
import urllib.parse
password = urllib.parse.quote_plus(raw_password)

# Configurar SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user}:{password}@{host}:{port}/{db}'


app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user}:{password}@{host}:{port}/{db}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Cargar la API Key desde variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------- MODELOS ----------
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    correo = db.Column(db.String(100), unique=True)
    contraseña = db.Column(db.String(512), nullable=False)
    tiene_ia = db.Column(db.Boolean, default=False)
    es_admin = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)

class PerfilNegocio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), unique=True)
    nombre = db.Column(db.String(100))
    servicios = db.Column(db.String(300))
    horarios = db.Column(db.String(100))
    ubicacion = db.Column(db.String(100))
    estilo = db.Column(db.String(100))

class Respuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.String(100), nullable=False)
    respuesta = db.Column(db.String(300), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

# ---------- LOGIN ----------
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ---------- RUTAS ----------
@app.route('/')
@login_required
def inicio():
    return render_template('panel.html', usuario=current_user)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = generate_password_hash(request.form['contraseña'])

        if Usuario.query.filter_by(nombre=nombre).first():
            return "El nombre ya está en uso"
        if Usuario.query.filter_by(correo=correo).first():
            return "El correo ya está en uso"

        nuevo = Usuario(nombre=nombre, correo=correo, contraseña=contraseña, activo=False)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/iniciar_bot/<int:user_id>', methods=['POST'])
@login_required
def iniciar_bot(user_id):
    try:
        subprocess.Popen(["node", "index.js", str(user_id)])
        flash(f"✅ Bot del usuario {user_id} iniciado correctamente.", "success")
    except Exception as e:
        flash(f"❌ Error al iniciar el bot: {str(e)}", "error")
    return redirect(url_for('admin'))  # o donde quieras volver

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contraseña = request.form['contraseña']
        user = Usuario.query.filter_by(nombre=nombre).first()
        if user and check_password_hash(user.contraseña, contraseña):
            if not user.activo:
                return "Tu cuenta está inactiva. Contactanos para activarla.", 403
            login_user(user)
            return redirect(url_for('inicio'))
        return "Credenciales incorrectas"
    return render_template('login.html')

@app.route('/admin/eliminar_usuario/<int:user_id>', methods=['POST'])
@login_required
def eliminar_usuario(user_id):
    if not current_user.es_admin:
        return "⛔ Acceso denegado", 403

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return "❌ Usuario no encontrado", 404

    # Eliminar perfil y respuestas si existen
    PerfilNegocio.query.filter_by(usuario_id=user_id).delete()
    Respuesta.query.filter_by(usuario_id=user_id).delete()
    db.session.delete(usuario)
    db.session.commit()

    flash("🗑️ Usuario eliminado correctamente", "success")
    return redirect(url_for('admin'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    print("🔍 Entrando a perfil con método:", request.method)
    perfil = PerfilNegocio.query.filter_by(usuario_id=current_user.id).first()

    if request.method == 'POST':
        print("📝 request.form:", request.form)

        if not perfil:
            print("➕ Creando nuevo perfil para usuario:", current_user.id)
            perfil = PerfilNegocio(usuario_id=current_user.id)
            db.session.add(perfil)
        else:
            print("🔄 Editando perfil existente:", perfil.id)

        # Asignar datos
        perfil.nombre = request.form.get('nombre', '')
        perfil.servicios = request.form.get('servicios', '')
        perfil.horarios = request.form.get('horarios', '')
        perfil.ubicacion = request.form.get('ubicacion', '')
        perfil.estilo = request.form.get('estilo', '')

        print("💾 Datos asignados:")
        print("  Nombre:", perfil.nombre)
        print("  Servicios:", perfil.servicios)
        print("  Horarios:", perfil.horarios)
        print("  Ubicación:", perfil.ubicacion)
        print("  Estilo:", perfil.estilo)

        db.session.commit()
        print("✅ Perfil guardado en la base de datos.")

        flash("Perfil actualizado correctamente ✅", "success")
        return redirect(url_for('perfil'))

    return render_template('perfil.html', perfil=perfil)


@app.route('/respuestas', methods=['GET', 'POST'])
@login_required
def respuestas():
    if request.method == 'POST':
        mensaje = request.form['mensaje']
        respuesta = request.form['respuesta']
        nueva = Respuesta(mensaje=mensaje, respuesta=respuesta, usuario_id=current_user.id)
        db.session.add(nueva)
        db.session.commit()
    reglas = Respuesta.query.filter_by(usuario_id=current_user.id).all()
    return render_template('respuestas.html', reglas=reglas, usuario=current_user, tiene_sesion=tiene_sesion)


@app.route('/admin/toggle_admin/<int:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.es_admin:
        return "⛔ Acceso denegado", 403

    user = Usuario.query.get(user_id)
    if not user:
        return "❌ Usuario no encontrado", 404

    user.es_admin = not user.es_admin
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin')
@login_required
def admin():
    if not current_user.es_admin:
        return "Acceso denegado"
    usuarios = Usuario.query.all()
    return render_template('admin.html', usuarios=usuarios)

@app.route('/respuestas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_respuesta(id):
    regla = Respuesta.query.get_or_404(id)
    if request.method == 'POST':
        regla.mensaje = request.form['mensaje']
        regla.respuesta = request.form['respuesta']
        db.session.commit()
        return redirect(url_for('respuestas'))
    return render_template('editar_respuesta.html', regla=regla)

@app.route('/respuestas/eliminar/<int:id>')
@login_required
def eliminar_respuesta(id):
    regla = Respuesta.query.get_or_404(id)
    db.session.delete(regla)
    db.session.commit()
    return redirect(url_for('respuestas'))

@app.route('/admin/toggle/<int:user_id>')
@login_required
def toggle_usuario(user_id):
    if not current_user.es_admin:
        return "Acceso denegado"
    user = Usuario.query.get(user_id)
    user.activo = not user.activo
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/hacer_admin')
def hacer_admin():
    usuario = Usuario.query.filter_by(nombre="Dueño").first()
    if usuario:
        usuario.es_admin = True
        db.session.commit()
        return "El usuario 'Dueño' ahora es administrador."
    return "Usuario no encontrado." 

@app.route('/api/responder', methods=['POST'])
def api_responder():
    data = request.get_json()
    mensaje = data.get('mensaje', '').strip().lower()
    numero = data.get('numero')
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"respuesta": "❌ Falta user_id"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario or not usuario.activo:
        return jsonify({"respuesta": "Este bot está inactivo. Contacte a soporte."})

    # 1. Buscar coincidencia parcial con sensibilidad reducida
    reglas = Respuesta.query.filter_by(usuario_id=usuario.id).all()
    for r in reglas:
        if r.mensaje.lower() in mensaje:
            return jsonify({"respuesta": r.respuesta})

    # 2. Generar con IA si no hay coincidencia
    perfil = PerfilNegocio.query.filter_by(usuario_id=usuario.id).first()
    contexto = f"Negocio: {perfil.nombre}, Servicios: {perfil.servicios}, Ubicación: {perfil.ubicacion}, Horarios: {perfil.horarios}, Estilo: {perfil.estilo}" if perfil else "Negocio local"

    prompt = f"""
Actuá como asistente del siguiente negocio:

{contexto}

Cliente: {mensaje}
Respuesta:"""

    try:
        respuesta_ia = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        texto_ia = respuesta_ia.choices[0].message.content.strip()
        return jsonify({"respuesta": texto_ia})
    except Exception as e:
        print("❌ Error con OpenAI:", str(e))
        return jsonify({"respuesta": "Lo siento, no puedo responder ahora."})
    
"""with app.app_context():
    usuario = Usuario.query.filter_by(nombre="Dueño").first()
    if usuario and not usuario.activo:
        usuario.activo = True
        db.session.commit()
        print("✅ Usuario activado desde código")"""


# ---------- INICIALIZAR ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
