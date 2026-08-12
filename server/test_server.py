"""수신 API 동작 테스트 (pytest)."""
from fastapi.testclient import TestClient

import main


def setup_function():
    # 테스트마다 저장소 초기화
    main.readings.clear()


def _client():
    return TestClient(main.app)


def test_post_reading_is_stored_and_returned():
    client = _client()

    res = client.post("/readings", json={"temperature": 24.5, "humidity": 40, "device_id": "pico-01"})

    assert res.status_code == 200
    assert res.json()["ok"] is True

    listing = client.get("/readings").json()
    assert len(listing) == 1
    assert listing[0]["temperature"] == 24.5
    assert listing[0]["device_id"] == "pico-01"
    assert "ts" in listing[0]  # 서버가 타임스탬프를 붙였는지


def test_get_readings_respects_limit():
    client = _client()
    for i in range(5):
        client.post("/readings", json={"temperature": 20 + i, "humidity": 50})

    res = client.get("/readings?limit=3")

    assert res.status_code == 200
    assert len(res.json()) == 3  # 최근 3개만


def test_dashboard_serves_html():
    res = _client().get("/")

    assert res.status_code == 200
    assert "Pico IoT" in res.text
