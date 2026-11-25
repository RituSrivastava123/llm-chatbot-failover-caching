def test_caching_behavior(client):
    msg = "What is the highest mountain in the world?"
    
    # 1. First request in session A -> LIVE_INFERENCE
    r1 = client.post("/chat", json={
        "session_id": "session-a",
        "message": msg
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert d1["metadata"]["key_id"] == "key_1"
    assert d1["metadata"]["fallback_attempts"] == 0
    assert d1["metadata"]["input_tokens"] > 0
    assert d1["metadata"]["output_tokens"] > 0
    reply1 = d1["reply"]

    # 2. Same first message in a new session B -> LLM_CACHE
    r2 = client.post("/chat", json={
        "session_id": "session-b",
        "message": msg
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["metadata"]["resolution_source"] == "LLM_CACHE"
    assert d2["reply"] == reply1
    assert d2["metadata"]["key_id"] is None
    assert d2["metadata"]["fallback_attempts"] == 0
    assert d2["metadata"]["input_tokens"] == d1["metadata"]["input_tokens"]
    assert d2["metadata"]["output_tokens"] == d1["metadata"]["output_tokens"]

    # 3. Different message in session C -> LIVE_INFERENCE (never from cache)
    r3 = client.post("/chat", json={
        "session_id": "session-c",
        "message": "What is the deepest ocean trench?"
    })
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["metadata"]["resolution_source"] == "LIVE_INFERENCE"
