import pytest
from app import create_app, db


@pytest.fixture()
def app():
    """
    Crea y configura una nueva instancia de la aplicación para cada prueba.
    Esta fixture se encarga de:
    1. Crear la app usando la configuración de prueba (TestConfig).
    2. Crear el contexto de la aplicación.
    3. Crear todas las tablas en la base de datos en memoria.
    4. Entregar (yield) la instancia de la app al test.
    5. Limpiar la base de datos después de que el test se ejecute.
    """
    app = create_app('config.TestConfig')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """
    Fixture que proporciona un cliente de pruebas para la aplicación.
    Permite simular peticiones HTTP (GET, POST, etc.) a las rutas.
    """
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Fixture que proporciona un runner para probar los comandos CLI de Flask."""
    return app.test_cli_runner()