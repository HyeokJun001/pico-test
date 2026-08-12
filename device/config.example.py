# config.example.py 를 복사해서 config.py 로 만들고 값을 채우세요.
# (config.py 는 비밀번호가 들어가므로 .gitignore 처리)

WIFI_SSID = "여기에_와이파이_이름_2.4GHz"
WIFI_PASSWORD = "여기에_와이파이_비밀번호"

# FastAPI 서버가 도는 PC의 로컬 IP. (Windows에서 ipconfig 로 확인 — 예: 192.168.0.10)
# Pico와 PC가 같은 공유기(WiFi)에 있어야 함.
API_URL = "http://192.168.0.10:8000/readings"

DEVICE_ID = "pico-01"
INTERVAL_SEC = 5  # 몇 초마다 측정·전송할지
