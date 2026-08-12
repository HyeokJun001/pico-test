# 배선 & MicroPython 굽기 가이드

## 1. 배선 (점퍼선 3가닥, 납땜 없음)

DHT11 모듈은 보통 핀이 3개예요. 모듈에 적힌 **글자로** 맞추세요
(제품마다 `+ / OUT / -` 또는 `VCC / DATA / GND` 또는 `S / + / -` 로 표기).

| DHT11 모듈 핀 | 연결 → | Pico W 핀 | Pico 물리 핀 번호 |
|---|---|---|---|
| `+` / `VCC` (전원) | → | `3V3(OUT)` | 36번 |
| `S` / `OUT` / `DATA` (신호) | → | `GP15` | 20번 |
| `-` / `GND` (접지) | → | `GND` | 38번 |

```
  DHT11 모듈                 Raspberry Pi Pico W
  ┌─────────┐
  │   +  ───┼──────(빨강)──────►  3V3(OUT)  [물리 36]
  │   S  ───┼──────(노랑)──────►  GP15      [물리 20]
  │   -  ───┼──────(검정)──────►  GND       [물리 38]
  └─────────┘
```

- 핀 위치는 **피코 핀아웃 그림**(Raspberry Pi Pico W pinout)을 옆에 두고 보면 쉬워요.
  물리 핀 번호는 USB 단자를 **위쪽**에 두었을 때, 왼쪽 위가 1번, 시계 반대 방향으로 셉니다.
- 색은 예시일 뿐 — 전원=빨강, 신호=노랑, 접지=검정으로 하면 헷갈리지 않아요.
- ⚠️ DATA 핀을 코드에서 바꾸려면 `device/main.py`의 `Pin(15)` 숫자만 바꾸면 됩니다.

## 2. MicroPython 굽기 (한 번만, 약 2분)

1. Raspberry Pi 공식 사이트에서 **Pico W용 MicroPython `.uf2`** 파일 다운로드
   → https://micropython.org/download/RPI_PICO_W/
2. 피코의 **BOOTSEL 버튼을 누른 채로** USB 케이블로 PC에 연결
3. 잠시 후 피코가 **USB 저장장치(`RPI-RP2`)** 로 컴퓨터에 나타남
4. 다운받은 **`.uf2` 파일을 그 드라이브로 드래그 앤 드롭**
5. 자동 재부팅 → 완료. 이제 파이썬이 돌아갑니다.

## 3. 코드 올리고 실행

1. **Thonny** IDE 설치 (https://thonny.org) → 우측 하단에서 인터프리터를 **MicroPython (Raspberry Pi Pico)** 로 선택
2. `device/config.example.py` 를 복사해 **`config.py`** 를 만들고 WiFi 이름·비밀번호, PC의 로컬 IP(`API_URL`)를 입력
   - PC 로컬 IP 확인: Windows에서 `ipconfig` → IPv4 주소 (예: `192.168.0.10`)
   - ⚠️ WiFi는 **2.4GHz** 여야 함 (피코 W는 5GHz 못 잡음)
3. Thonny로 피코에 **`config.py`** 와 **`main.py`** 두 파일을 저장 (피코 파일시스템에)
4. 먼저 PC에서 서버 실행: `cd server && uvicorn main:app --host 0.0.0.0 --port 8000`
5. 피코에서 `main.py` 실행 → Thonny 콘솔에 `[WiFi] 접속 성공`, `[TX] 응답: 200` 이 뜨면 성공
6. 브라우저에서 `http://localhost:8000` 열면 실시간 대시보드 확인
