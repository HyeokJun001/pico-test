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
- **Server (FastAPI):** 측정값 수신·저장, **불쾌지수·이슬점·통계를 서버에서 계산**해 제공, 대시보드 렌더링
- **Dashboard:** 현재값 + 파생지표(불쾌지수·이슬점) + 쾌적도 배지 + 통계 + 온습도 2축 그래프 + CSV 다운로드

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
| `GET`  | `/summary?limit=50` | 최신값 + **파생지표(불쾌지수·이슬점·쾌적도·경고)** + **통계(최소/최대/평균)** — 서버에서 계산 |
| `GET`  | `/readings.csv` | 전체 데이터 CSV 다운로드 |
| `GET`  | `/` | 실시간 대시보드(HTML) |

### 파생 지표 (서버 계산)

- **이슬점(Dew point)** — Magnus 공식으로 온도·습도에서 결로 온도 산출
- **불쾌지수(THI)** — `0.81·T + 0.01·RH·(0.99·T − 14.3) + 46.3`, 4단계 쾌적도 분류
- **경고** — 건조(습도<30%)·습함(>60%)·더움(>28℃)·추움(<18℃) 임계값 판정

## 기술 스택

Python · MicroPython · FastAPI · REST API · Raspberry Pi Pico W · DHT11 · HTML/JS(Canvas)
