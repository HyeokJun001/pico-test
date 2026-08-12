# Pico IoT — 온습도 센서 → REST API → 실시간 대시보드

![CI](https://github.com/HyeokJun001/pico-test/actions/workflows/ci.yml/badge.svg)

라즈베리파이 피코 W와 DHT11 센서로 **온습도를 측정해 WiFi로 REST API 서버에 전송**하고,
웹 대시보드에서 실시간으로 확인하는 IoT 데이터 파이프라인 프로젝트입니다.

## 아키텍처

```
┌──────────────┐   WiFi(HTTP POST)   ┌──────────────┐    HTTP    ┌──────────────┐
│ Raspberry Pi │  ───────────────►   │  FastAPI     │  ◄──────►  │  웹 대시보드  │
│ Pico W       │   JSON              │  REST API    │   폴링     │ (온도 그래프) │
│ + DHT11 센서 │  {temp, humidity}   │  서버        │            │              │
└──────────────┘                     └──────────────┘            └──────────────┘
   MicroPython                          Python                     HTML/JS
```

- **Device (MicroPython):** DHT11에서 5초마다 온습도 측정 → `POST /readings` 로 전송
- **Server (FastAPI):** 측정값 수신·저장, `GET /readings` 제공, 대시보드 렌더링
- **Dashboard:** 3초마다 폴링해 현재값 + 온도 그래프 + 최근 기록 표시

## 이 프로젝트가 보여주는 것

- **IoT 제품 개발** — 실제 센서 데이터를 수집·전송하는 엔드투엔드 파이프라인
- **Python** — 디바이스(MicroPython) & 서버(FastAPI) 양쪽 모두 Python
- **REST API** — 디바이스↔서버 통신을 REST(JSON)로 설계·구현
- **테스트** — 수신 API에 대한 pytest 포함

## 폴더 구조

```
pico-iot/
├── device/
│   ├── main.py            # Pico W MicroPython (센서 읽기 → WiFi → POST)
│   └── config.example.py  # WiFi/서버 설정 템플릿
├── server/
│   ├── main.py            # FastAPI: POST/GET /readings + 대시보드
│   ├── test_server.py     # pytest
│   ├── requirements.txt
│   └── requirements-dev.txt
└── docs/
    └── wiring.md          # 배선도 + MicroPython 굽기 가이드
```

## 실행 방법

### 1) 서버
```bash
cd server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
브라우저에서 http://localhost:8000 → 대시보드

### 2) 디바이스
`docs/wiring.md` 를 따라 배선하고 MicroPython을 구운 뒤,
`config.example.py` → `config.py` 로 WiFi/서버 IP를 채워 피코에 `main.py`와 함께 올려 실행.

### 테스트
```bash
cd server
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/readings` | 온습도 저장 `{temperature, humidity, device_id}` |
| `GET`  | `/readings?limit=50` | 최근 측정값 목록(JSON) |
| `GET`  | `/` | 실시간 대시보드(HTML) |

## 기술 스택

Python · MicroPython · FastAPI · REST API · Raspberry Pi Pico W · DHT11 · HTML/JS(Canvas)
