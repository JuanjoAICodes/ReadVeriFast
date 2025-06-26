def test_landing_page_status_code(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/')
    assert response.status_code == 200

def test_landing_page_content(client):
    """Test that the landing page contains the expected title."""
    response = client.get('/')
    assert b"Welcome to VeriFast" in response.data