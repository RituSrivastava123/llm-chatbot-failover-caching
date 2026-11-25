def test_failover_single_key_429(client):
    response = client.post(
        "/chat",
        json={"session_id": "failover-sess-1", "message": "Test failover 429"},
        headers={"X-Simulate-Failure": "key_1=429"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["key_id"] == "key_2"
    assert data["metadata"]["fallback_attempts"] == 1
    assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"

def test_failover_single_key_500(client):
    response = client.post(
        "/chat",
        json={"session_id": "failover-sess-2", "message": "Test failover 500"},
        headers={"X-Simulate-Failure": "key_1=500"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["key_id"] == "key_2"
    assert data["metadata"]["fallback_attempts"] == 1

def test_failover_all_keys_unavailable_503(client):
    session_id = "failover-sess-3"
    response = client.post(
        "/chat",
        json={"session_id": session_id, "message": "Test all fail"},
        headers={"X-Simulate-Failure": "*=429"}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "all providers unavailable"}

    # Verify that a request that fails (503) is NOT added to session history!
    hist_resp = client.get(f"/sessions/{session_id}/messages")
    assert hist_resp.status_code == 404
    assert hist_resp.json() == {"detail": "session not found"}
