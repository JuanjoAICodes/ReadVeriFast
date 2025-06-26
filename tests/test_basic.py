from app.models import User, Article
from app import db

def test_landing_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response status code is 200 OK
    AND that the content contains "Explore Articles".
    """
    response = client.get('/')
    assert response.status_code == 200
    # Asumiendo que "Explore Articles" es parte del contenido visible en la landing page.
    # Si este texto no está directamente en el HTML, esta aserción fallará.
    assert b"Explore Articles" in response.data


def test_unauthenticated_profile(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/profile' page is requested (GET) by an unauthenticated user
    THEN check that the response is a 302 Found (redirection to login).
    """
    response = client.get('/profile')
    # Flask-Login redirige a la página de login para usuarios no autenticados,
    # lo que resulta en un código de estado 302.
    assert response.status_code == 302