def test_validation_missing_session_id(client):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_validation_empty_session_id(client):
    response = client.post("/chat", json={"session_id": "   ", "message": "Hello"})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_validation_session_id_too_long(client):
    response = client.post("/chat", json={"session_id": "a" * 129, "message": "Hello"})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_validation_missing_message(client):
    response = client.post("/chat", json={"session_id": "s-123"})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_validation_empty_message(client):
    response = client.post("/chat", json={"session_id": "s-123", "message": "   "})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_validation_message_too_long(client):
    response = client.post("/chat", json={"session_id": "s-123", "message": "a" * 4001})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_validation_malformed_json(client):
    response = client.post(
        "/chat",
        content="not a valid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()
