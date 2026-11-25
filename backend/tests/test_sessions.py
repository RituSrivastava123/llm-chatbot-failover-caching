def test_unknown_session_returns_404(client):
    response = client.get("/sessions/nonexistent-session/messages")
    assert response.status_code == 404
    assert response.json() == {"detail": "session not found"}

def test_session_history_after_chat(client):
    session_id = "test-session-hist-1"
    
    # 1. Send first message
    r1 = client.post("/chat", json={
        "session_id": session_id,
        "message": "What is the capital of France?"
    })
    assert r1.status_code == 200
    r1_data = r1.json()
    assert r1_data["session_id"] == session_id
    assert r1_data["reply"] != ""

    # 2. Retrieve history
    r2 = client.get(f"/sessions/{session_id}/messages")
    assert r2.status_code == 200
    hist = r2.json()
    assert hist["session_id"] == session_id
    messages = hist["messages"]
    assert len(messages) == 2

    # First is user
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is the capital of France?"
    assert "metadata" not in messages[0] or messages[0].get("metadata") is None

    # Second is assistant
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == r1_data["reply"]
    assert "metadata" in messages[1]
    assert messages[1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert "input_tokens" in messages[1]["metadata"]
    assert "output_tokens" in messages[1]["metadata"]
