from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_user, current_user, login_required, logout_user
from . import auth_bp # Assuming auth_bp is defined in app/auth/__init__.py
from urllib.parse import urlparse
from app.auth.forms import RegistrationForm, LoginForm
from app.extensions import db
from app.models import User

# Esta es una función de registro hipotética, ya que no estaba en el contexto proporcionado.
# Deberías integrarla en tu estructura de autenticación existente.
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)

        # 1. Comprueba si existen datos de invitado en la sesión
        if 'guest_xp' in session:
            # 2. Si existen, transfiere los valores
            user.total_xp = session.get('guest_xp', 0)
            # Usamos los mismos valores por defecto que en submit_quiz para consistencia
            user.current_wpm = session.get('guest_current_wpm', 200)
            user.max_wpm = session.get('guest_max_wpm', 300)

            # 3. Limpia los datos de la sesión de invitado
            session.pop('guest_xp', None)
            session.pop('guest_current_wpm', None)
            session.pop('guest_max_wpm', None)

            # 4. Mensaje flash para notificar al usuario
            flash('¡Tu progreso de invitado ha sido transferido a tu nueva cuenta!', 'success')

        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, ya eres un usuario registrado!', 'success')
        login_user(user) # Inicia sesión automáticamente al nuevo usuario
        return redirect(url_for('core.index'))
    return render_template('auth/register.html', title='Registrarse', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email o contraseña inválidos', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirigir al usuario a la página que intentaba acceder
        next_page = request.args.get('next') # type: ignore
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('core.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('core.index'))