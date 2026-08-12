"""수신 API + 파생지표/통계/CSV 테스트 (pytest)."""
from fastapi.testclient import TestClient

import main


def setup_function():
    main.readings.clear()  # 테스트마다 저장소 초기화


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
    assert "ts" in listing[0]


def test_get_readings_respects_limit():
    client = _client()
    for i in range(5):
        client.post("/readings", json={"temperature": 20 + i, "humidity": 50})

    assert len(client.get("/readings?limit=3").json()) == 3


def test_summary_computes_derived_and_stats():
    client = _client()
    for temp in (22, 24, 26):
        client.post("/readings", json={"temperature": temp, "humidity": 45})

    body = client.get("/summary").json()

    assert body["count"] == 3
    latest = body["latest"]
    # 파생지표가 계산되어 포함되는지
    assert "dew_point" in latest and "discomfort_index" in latest
    assert latest["comfort"] in ("쾌적", "보통", "다소 불쾌", "매우 불쾌")
    assert isinstance(latest["warnings"], list)
    # 통계
    assert body["stats"]["temperature"]["min"] == 22
    assert body["stats"]["temperature"]["max"] == 26
    assert body["stats"]["temperature"]["avg"] == 24


def test_summary_empty_is_safe():
    body = _client().get("/summary").json()
    assert body["count"] == 0
    assert body["latest"] is None


def test_dry_warning_triggers_below_30_humidity():
    client = _client()
    client.post("/readings", json={"temperature": 25, "humidity": 20})

    warnings = client.get("/summary").json()["latest"]["warnings"]

    assert "건조 주의" in warnings


def test_csv_export_has_header_and_rows():
    client = _client()
    client.post("/readings", json={"temperature": 23, "humidity": 44, "device_id": "pico-01"})

    res = client.get("/readings.csv")

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    lines = res.text.strip().splitlines()
    assert lines[0] == "ts,device_id,temperature,humidity"
    assert "pico-01" in lines[1]


def test_dashboard_serves_html():
    res = _client().get("/")
    assert res.status_code == 200
    assert "Pico IoT" in res.text
