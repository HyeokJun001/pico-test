"""
Pico IoT — FastAPI 수신 서버 + 웹 대시보드

- POST /readings : Pico가 보낸 온습도 저장
- GET  /readings : 최근 측정값 JSON
- GET  /         : 실시간 대시보드(현재값 + 온도 그래프 + 최근 표)

실행:
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000
  (--host 0.0.0.0 이어야 같은 WiFi의 Pico가 접속할 수 있음)
"""
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Pico IoT Sensor API")

# ponytail: 메모리 링버퍼(최근 500개). 영구 저장 필요하면 SQLite로 교체.
readings = deque(maxlen=500)


class Reading(BaseModel):
    temperature: float
    humidity: float
    device_id: str = "pico-01"


@app.post("/readings")
def add_reading(reading: Reading):
    item = {**reading.model_dump(), "ts": datetime.now(timezone.utc).isoformat()}
    readings.append(item)
    return {"ok": True, "stored": item}


@app.get("/readings")
def get_readings(limit: int = 50):
    return list(readings)[-limit:]


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pico IoT 대시보드</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; margin: 0; background: #0f1117; color: #e6e8ee; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }
  h1 { font-size: 1.25rem; margin: 0 0 4px; }
  .sub { color: #8b90a0; font-size: .85rem; margin-bottom: 20px; }
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
  .card { background: #1a1d29; border: 1px solid #262a38; border-radius: 14px; padding: 20px; }
  .card .label { color: #8b90a0; font-size: .8rem; }
  .card .value { font-size: 2.4rem; font-weight: 700; margin-top: 6px; }
  .card .value span { font-size: 1rem; color: #8b90a0; font-weight: 400; }
  .temp .value { color: #ff7a59; }
  .hum .value { color: #4ea8ff; }
  canvas { width: 100%; height: 180px; background: #1a1d29; border: 1px solid #262a38; border-radius: 14px; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: .85rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #262a38; }
  th { color: #8b90a0; font-weight: 500; }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#3ddc84; margin-right:6px; }
  .stale { background:#ff5a6e; }
</style>
</head>
<body>
<div class="wrap">
  <h1>🌡️ Pico IoT 온습도 대시보드</h1>
  <div class="sub"><span id="status" class="dot"></span><span id="statusText">연결 대기 중…</span></div>
  <div class="cards">
    <div class="card temp"><div class="label">온도</div><div class="value"><span id="tempVal">--</span> <span>°C</span></div></div>
    <div class="card hum"><div class="label">습도</div><div class="value"><span id="humVal">--</span> <span>%</span></div></div>
  </div>
  <canvas id="chart" width="728" height="180"></canvas>
  <table>
    <thead><tr><th>시각</th><th>온도(°C)</th><th>습도(%)</th><th>기기</th></tr></thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<script>
const fmt = t => new Date(t).toLocaleTimeString('ko-KR');
async function refresh() {
  try {
    const rows = await (await fetch('/readings?limit=50')).json();
    const statusEl = document.getElementById('status');
    const statusText = document.getElementById('statusText');
    if (!rows.length) { statusText.textContent = '데이터 없음 — Pico 전송 대기'; return; }
    const last = rows[rows.length - 1];
    document.getElementById('tempVal').textContent = last.temperature;
    document.getElementById('humVal').textContent = last.humidity;
    const ageSec = (Date.now() - new Date(last.ts).getTime()) / 1000;
    const live = ageSec < 30;
    statusEl.className = 'dot' + (live ? '' : ' stale');
    statusText.textContent = live ? ('실시간 · 마지막 수신 ' + fmt(last.ts)) : ('수신 끊김 · 마지막 ' + fmt(last.ts));
    // 표(최근 10개, 최신순)
    document.getElementById('tbody').innerHTML = rows.slice(-10).reverse().map(r =>
      `<tr><td>${fmt(r.ts)}</td><td>${r.temperature}</td><td>${r.humidity}</td><td>${r.device_id}</td></tr>`).join('');
    drawChart(rows.map(r => r.temperature));
  } catch (e) {
    document.getElementById('statusText').textContent = '서버 연결 오류';
  }
}
function drawChart(data) {
  const c = document.getElementById('chart'), ctx = c.getContext('2d');
  const W = c.width, H = c.height, pad = 24;
  ctx.clearRect(0, 0, W, H);
  if (data.length < 2) return;
  const min = Math.min(...data) - 1, max = Math.max(...data) + 1;
  const x = i => pad + (W - 2 * pad) * i / (data.length - 1);
  const y = v => H - pad - (H - 2 * pad) * (v - min) / (max - min);
  ctx.strokeStyle = '#ff7a59'; ctx.lineWidth = 2; ctx.beginPath();
  data.forEach((v, i) => i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v)));
  ctx.stroke();
  ctx.fillStyle = '#8b90a0'; ctx.font = '11px system-ui';
  ctx.fillText(max.toFixed(0) + '°C', 4, pad);
  ctx.fillText(min.toFixed(0) + '°C', 4, H - pad + 10);
}
refresh(); setInterval(refresh, 3000);
</script>
</body>
</html>"""
