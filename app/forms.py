from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields import URLField # Importamos URLField
from wtforms.validators import DataRequired, Email, EqualTo, URL, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """
    Formulario para el inicio de sesión de usuarios.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    """
    Formulario para el registro de nuevos usuarios.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')]
    )
    submit = SubmitField('Registrarse')

class ArticleSubmitForm(FlaskForm):
    """
    Formulario para que los usuarios envíen una URL de un artículo para procesar.
    """
    url = URLField('URL del Artículo', validators=[DataRequired(), URL(message="Por favor, introduce una URL válida.")])
    submit = SubmitField('Procesar Artículo')

# Formulario vacío para protección CSRF en formularios generados dinámicamente
class EmptyForm(FlaskForm):
    """Un formulario simple sin campos, usado principalmente para protección CSRF."""
    submit = SubmitField('Enviar') # Aunque no se use, es común tener un submit
