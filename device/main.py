"""
Raspberry Pi Pico W — DHT11 온습도 센서 → WiFi → REST API 전송

동작:
1. WiFi(2.4GHz)에 접속
2. DHT11에서 온도/습도 측정 (INTERVAL_SEC 마다)
3. FastAPI 서버로 JSON POST
4. 전송 중 온보드 LED 깜빡

MicroPython (Pico W)에서 실행. dht / machine / network / urequests 는 기본 포함.
설정은 config.py 참고 (config.example.py 를 복사해서 만들 것).
"""
import time
import network
import urequests
from machine import Pin
import dht

import config

# DHT11 DATA 핀 = GP15 (물리 20번 핀). 배선은 docs/wiring.md 참고.
sensor = dht.DHT11(Pin(15))
led = Pin("LED", Pin.OUT)  # Pico W 온보드 LED


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("[WiFi] 접속 시도:", config.WIFI_SSID)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(20):  # 최대 20초 대기
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print("[WiFi] 접속 성공:", wlan.ifconfig()[0])
        return True
    print("[WiFi] 접속 실패 — SSID/비밀번호와 2.4GHz 여부 확인")
    return False


def read_and_send():
    sensor.measure()  # DHT11은 측정 간 최소 1초 필요
    payload = {
        "temperature": sensor.temperature(),
        "humidity": sensor.humidity(),
        "device_id": config.DEVICE_ID,
    }
    print("[TX]", payload)
    res = urequests.post(config.API_URL, json=payload)
    print("[TX] 응답:", res.status_code)
    res.close()


def main():
    if not connect_wifi():
        return
    while True:
        try:
            led.on()
            read_and_send()
            led.off()
        except OSError as e:
            # DHT11 읽기 실패 / 네트워크 오류는 넘어가고 다음 주기 재시도
            print("[ERR]", e)
            led.off()
        time.sleep(config.INTERVAL_SEC)


main()
