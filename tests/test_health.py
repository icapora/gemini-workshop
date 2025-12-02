"""
Tests for health check endpoint
"""


def test_health_check_returns_200(test_client):
    """Test that health endpoint returns 200 OK"""
    response = test_client.get("/health")
    assert response.status_code == 200


def test_health_check_response_structure(test_client):
    """Test health check response has correct structure"""
    response = test_client.get("/health")
    data = response.json()

    assert "status" in data
    assert data["status"] == "ok"
    assert "service" in data
    assert "api_key_configured" in data


def test_health_check_api_key_detection(test_client, mock_gemini_api_key):
    """Test that health check correctly detects API key"""
    response = test_client.get("/health")
    data = response.json()

    assert data["api_key_configured"] is True
