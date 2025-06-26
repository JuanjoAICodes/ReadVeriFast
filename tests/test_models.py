from app.models import User


def test_password_hashing():
    """
    GIVEN a User model instance
    WHEN a password is set using set_password()
    THEN check that the password_hash is not the plain text password
    AND check that check_password() validates the correct and incorrect passwords
    """
    # 1. Crear una instancia de User
    u = User(email='test@example.com')
    u.set_password('mysecretpassword')

    # 2. Verificar que el hash no es la contraseña original y que la comprobación funciona
    assert u.password_hash != 'mysecretpassword'
    assert u.check_password('mysecretpassword') is True
    assert u.check_password('anotherpassword') is False