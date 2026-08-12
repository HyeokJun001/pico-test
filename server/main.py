"""
Pico IoT — FastAPI 수신 서버 + 웹 대시보드

엔드포인트:
- POST /readings      : Pico가 보낸 온습도 저장
- GET  /readings      : 최근 측정값 JSON (그래프용)
- GET  /summary       : 최신값 + 파생지표(불쾌지수·이슬점) + 통계(최소/최대/평균) — 서버에서 계산
- GET  /readings.csv  : 전체 데이터 CSV 다운로드
- GET  /              : 실시간 대시보드

실행:
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
import csv
import io
import math
from collections import deque
from datetime import datetime, timezone
from statistics import mean

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="Pico IoT Sensor API")

# ponytail: 메모리 링버퍼(최근 500개). 영구 저장 필요하면 SQLite로 교체.
readings = deque(maxlen=500)


class Reading(BaseModel):
    temperature: float
    humidity: float
    device_id: str = "pico-01"


# ── 온습도 파생 지표 (서버에서 계산) ─────────────────────────────

def dew_point(t: float, rh: float) -> float:
    """이슬점 (Magnus 공식). rh: 상대습도(%)."""
    a, b = 17.27, 237.7
    rh = max(1.0, rh)  # log(0) 방지
    gamma = (a * t) / (b + t) + math.log(rh / 100.0)
    return round((b * gamma) / (a - gamma), 1)


def discomfort_index(t: float, rh: float) -> float:
    """불쾌지수(THI)."""
    return round(0.81 * t + 0.01 * rh * (0.99 * t - 14.3) + 46.3, 1)


def comfort_level(di: float) -> str:
    if di < 68:
        return "쾌적"
    if di < 75:
        return "보통"
    if di < 80:
        return "다소 불쾌"
    return "매우 불쾌"


def warnings_for(t: float, rh: float) -> list:
    w = []
    if rh < 30:
        w.append("건조 주의")
    if rh > 60:
        w.append("습함")
    if t > 28:
        w.append("더움")
    if t < 18:
        w.append("추움")
    return w


def _stats(xs):
    return {"min": min(xs), "max": max(xs), "avg": round(mean(xs), 1)}


# ── API ──────────────────────────────────────────────────────────

@app.post("/readings")
def add_reading(reading: Reading):
    item = {**reading.model_dump(), "ts": datetime.now(timezone.utc).isoformat()}
    readings.append(item)
    return {"ok": True, "stored": item}


@app.get("/readings")
def get_readings(limit: int = 50):
    return list(readings)[-limit:]


@app.get("/summary")
def summary(limit: int = 50):
    data = list(readings)[-limit:]
    if not data:
        return {"count": 0, "latest": None, "stats": None}
    temps = [r["temperature"] for r in data]
    hums = [r["humidity"] for r in data]
    last = data[-1]
    t, rh = last["temperature"], last["humidity"]
    di = discomfort_index(t, rh)
    latest = {
        "temperature": t,
        "humidity": rh,
        "ts": last["ts"],
        "dew_point": dew_point(t, rh),
        "discomfort_index": di,
        "comfort": comfort_level(di),
        "warnings": warnings_for(t, rh),
    }
    return {
        "count": len(data),
        "latest": latest,
        "stats": {"temperature": _stats(temps), "humidity": _stats(hums)},
    }


@app.get("/readings.csv")
def readings_csv():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ts", "device_id", "temperature", "humidity"])
    for r in readings:
        writer.writerow([r["ts"], r["device_id"], r["temperature"], r["humidity"]])
    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=readings.csv"},
    )


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
  :root { color-scheme: dark; }
  body { font-family: system-ui, sans-serif; margin: 0; background: #0f1117; color: #e6e8ee; }
  .wrap { max-width: 820px; margin: 0 auto; padding: 24px 16px 48px; }
  h1 { font-size: 1.25rem; margin: 0; }
  .top { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:6px; }
  .sub { color:#8b90a0; font-size:.85rem; margin-bottom:18px; }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#3ddc84; margin-right:6px; }
  .dot.stale { background:#ff5a6e; }
  a.btn { color:#e6e8ee; text-decoration:none; font-size:.8rem; border:1px solid #2d3242; border-radius:8px; padding:6px 12px; }
  a.btn:hover { background:#1a1d29; }
  .badge { display:inline-flex; align-items:center; gap:8px; padding:10px 16px; border-radius:12px; font-weight:700; margin-bottom:16px; }
  .warns { display:inline-flex; gap:6px; flex-wrap:wrap; margin-left:8px; }
  .warns span { background:#3a1d22; color:#ff9db0; font-size:.72rem; font-weight:600; padding:3px 8px; border-radius:20px; }
  .cards { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }
  .card { background:#1a1d29; border:1px solid #262a38; border-radius:14px; padding:16px; }
  .card .label { color:#8b90a0; font-size:.78rem; }
  .card .value { font-size:1.9rem; font-weight:700; margin-top:4px; }
  .card .value span { font-size:.9rem; color:#8b90a0; font-weight:400; }
  .card .stat { color:#6b7183; font-size:.72rem; margin-top:6px; }
  .temp .value { color:#ff7a59; } .hum .value { color:#4ea8ff; }
  .di .value { color:#ffd166; } .dew .value { color:#9d8cff; }
  canvas { width:100%; height:220px; background:#1a1d29; border:1px solid #262a38; border-radius:14px; }
  .clegend { display:flex; gap:16px; font-size:.78rem; color:#8b90a0; margin:8px 2px 0; }
  .clegend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; vertical-align:middle; }
  table { width:100%; border-collapse:collapse; margin-top:20px; font-size:.85rem; }
  th, td { text-align:left; padding:8px 10px; border-bottom:1px solid #262a38; }
  th { color:#8b90a0; font-weight:500; }
  @media (max-width:620px){ .cards{ grid-template-columns:repeat(2,1fr);} }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h1>🌡️ Pico IoT 온습도 대시보드</h1>
    <a class="btn" href="/readings.csv">⬇ CSV 다운로드</a>
  </div>
  <div class="sub"><span id="dot" class="dot"></span><span id="statusText">연결 대기 중…</span></div>

  <div id="badge" class="badge" style="background:#1a1d29;">쾌적도 --<span id="warns" class="warns"></span></div>

  <div class="cards">
    <div class="card temp"><div class="label">온도</div><div class="value"><span id="t">--</span> <span>°C</span></div><div class="stat" id="tStat"></div></div>
    <div class="card hum"><div class="label">습도</div><div class="value"><span id="h">--</span> <span>%</span></div><div class="stat" id="hStat"></div></div>
    <div class="card di"><div class="label">불쾌지수</div><div class="value"><span id="di">--</span></div><div class="stat">THI</div></div>
    <div class="card dew"><div class="label">이슬점</div><div class="value"><span id="dew">--</span> <span>°C</span></div><div class="stat">결로 기준</div></div>
  </div>

  <canvas id="chart" width="788" height="220"></canvas>
  <div class="clegend"><span><i style="background:#ff7a59"></i>온도(°C)</span><span><i style="background:#4ea8ff"></i>습도(%)</span></div>

  <table>
    <thead><tr><th>시각</th><th>온도(°C)</th><th>습도(%)</th><th>기기</th></tr></thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<script>
const fmt = ts => new Date(ts).toLocaleTimeString('ko-KR');
const COMFORT = { "쾌적":"#153a29", "보통":"#14304a", "다소 불쾌":"#3a2a12", "매우 불쾌":"#3a161c" };
const COMFORT_FG = { "쾌적":"#3ddc84", "보통":"#4ea8ff", "다소 불쾌":"#ffb84d", "매우 불쾌":"#ff6b7f" };

async function refresh() {
  try {
    const [sum, rows] = await Promise.all([
      fetch('/summary?limit=50').then(r => r.json()),
      fetch('/readings?limit=50').then(r => r.json()),
    ]);
    const dot = document.getElementById('dot'), status = document.getElementById('statusText');
    if (!sum.count) { status.textContent = '데이터 없음 — Pico 전송 대기'; return; }
    const L = sum.latest, s = sum.stats;
    document.getElementById('t').textContent = L.temperature;
    document.getElementById('h').textContent = L.humidity;
    document.getElementById('di').textContent = L.discomfort_index;
    document.getElementById('dew').textContent = L.dew_point;
    document.getElementById('tStat').textContent = `최저 ${s.temperature.min} · 평균 ${s.temperature.avg} · 최고 ${s.temperature.max}`;
    document.getElementById('hStat').textContent = `최저 ${s.humidity.min} · 평균 ${s.humidity.avg} · 최고 ${s.humidity.max}`;
    const badge = document.getElementById('badge');
    badge.style.background = COMFORT[L.comfort] || '#1a1d29';
    badge.style.color = COMFORT_FG[L.comfort] || '#e6e8ee';
    badge.firstChild.textContent = '쾌적도 ' + L.comfort + ' ';
    document.getElementById('warns').innerHTML = (L.warnings || []).map(w => `<span>⚠ ${w}</span>`).join('');
    const age = (Date.now() - new Date(L.ts).getTime()) / 1000, live = age < 30;
    dot.className = 'dot' + (live ? '' : ' stale');
    status.textContent = (live ? '실시간 · ' : '수신 끊김 · ') + '마지막 ' + fmt(L.ts) + ` (${sum.count}건)`;
    document.getElementById('tbody').innerHTML = rows.slice(-10).reverse().map(r =>
      `<tr><td>${fmt(r.ts)}</td><td>${r.temperature}</td><td>${r.humidity}</td><td>${r.device_id}</td></tr>`).join('');
    drawChart(rows.map(r => r.temperature), rows.map(r => r.humidity));
  } catch (e) { document.getElementById('statusText').textContent = '서버 연결 오류'; }
}

function drawChart(temp, hum) {
  const c = document.getElementById('chart'), ctx = c.getContext('2d');
  const W = c.width, H = c.height, PL = 40, PR = 40, PT = 16, PB = 26;
  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = '#1f2430'; ctx.lineWidth = 1;
  for (let g = 0; g <= 4; g++) { const yy = PT + (H-PT-PB)*g/4; ctx.beginPath(); ctx.moveTo(PL,yy); ctx.lineTo(W-PR,yy); ctx.stroke(); }
  if (temp.length < 2) return;
  const band = (arr) => { const lo = Math.min(...arr), hi = Math.max(...arr), pad = (hi-lo||1)*0.2; return [lo-pad, hi+pad]; };
  const [tLo,tHi] = band(temp), [hLo,hHi] = band(hum);
  const drawLine = (arr, lo, hi, color) => {
    const x = i => PL + (W-PL-PR)*i/(arr.length-1);
    const y = v => H-PB - (H-PT-PB)*(v-lo)/(hi-lo);
    ctx.strokeStyle = color; ctx.lineWidth = 2.2; ctx.beginPath();
    arr.forEach((v,i)=> i ? ctx.lineTo(x(i),y(v)) : ctx.moveTo(x(i),y(v)));
    ctx.stroke();
    const li = arr.length-1; ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x(li),y(arr[li]),3.5,0,7); ctx.fill();
  };
  drawLine(temp, tLo, tHi, '#ff7a59');
  drawLine(hum, hLo, hHi, '#4ea8ff');
  ctx.font = '11px system-ui';
  ctx.fillStyle = '#ff7a59'; ctx.textAlign = 'right';
  ctx.fillText(tHi.toFixed(0)+'°', PL-5, PT+4); ctx.fillText(tLo.toFixed(0)+'°', PL-5, H-PB);
  ctx.fillStyle = '#4ea8ff'; ctx.textAlign = 'left';
  ctx.fillText(hHi.toFixed(0)+'%', W-PR+5, PT+4); ctx.fillText(hLo.toFixed(0)+'%', W-PR+5, H-PB);
}
refresh(); setInterval(refresh, 3000);
</script>
</body>
</html>"""
