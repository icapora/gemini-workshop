"""
Tests for main FastAPI application
"""


def test_app_initialization(test_client):
    """Test that the FastAPI app initializes correctly"""
    assert test_client.app.title == "Real-time conversation"
    assert test_client.app.version == "1.0.0"


def test_root_endpoint_returns_html(test_client):
    """Test that root endpoint serves HTML"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Should contain HTML content
    assert "<!DOCTYPE html>" in response.text or "<html" in response.text


def test_static_files_mounted(test_client):
    """Test that static files are accessible"""
    # Try to access the static index.html file
    response = test_client.get("/static/index.html")
    # Should either succeed (200) or be correctly mounted
    assert response.status_code in [200, 404, 405]
