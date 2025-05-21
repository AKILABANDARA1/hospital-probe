import requests
import socket
import time
import random
import threading

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

TARGET_IP = "20.109.32.217"
HTTP_PORTS = [80, 443]

app = FastAPI()

probe_results = {
    "last_run": None,
    "results": []
}

metrics_data = {}

def tcp_check(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=3):
            return f"TCP port {port} is open"
    except Exception as e:
        return f"TCP port {port} closed ({e})"

def http_check(ip, port):
    try:
        scheme = "https" if port == 443 else "http"
        url = f"{scheme}://{ip}"
        res = requests.head(url, timeout=3, verify=False)
        return f"{scheme.upper()} port {port} responded with status {res.status_code}"
    except requests.exceptions.SSLError:
        return f"SSL error on port {port}"
    except Exception as e:
        return f"HTTP check failed on port {port} ({e})"

def run_probe_loop():
    while True:
        results = []
        for port in HTTP_PORTS:
            tcp_status = tcp_check(TARGET_IP, port)
            http_status = http_check(TARGET_IP, port)
            results.append(f"{tcp_status}; {http_status}")
        probe_results["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        probe_results["results"] = results
        time.sleep(random.randint(15, 30))

threading.Thread(target=run_probe_loop, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/metrics")
async def receive_metrics(data: dict):
    global metrics_data
    metrics_data = data
    return {"status": "received"}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    metrics_html = "<p><em>No metrics received yet.</em></p>"
    if metrics_data:
        metrics_html = f"""
        <div class="card">
          <div class="metrics-title">Latest Hospital VM Metrics</div>
          <ul>
            <li><strong>OS:</strong> {metrics_data.get('os', 'N/A')}</li>
            <li><strong>CPU Usage:</strong> {metrics_data.get('cpu_percent', 'N/A')}%</li>
            <li><strong>RAM Used:</strong> {metrics_data.get('ram_used_mb', 'N/A')} MB / {metrics_data.get('ram_total_mb', 'N/A')} MB</li>
            <li><strong>Disk Used:</strong> {metrics_data.get('disk_used_gb', 'N/A')} GB / {metrics_data.get('disk_total_gb', 'N/A')} GB</li>
            <li><strong>Timestamp:</strong> {metrics_data.get('timestamp', 'N/A')}</li>
          </ul>
        </div>
        """

    html_content = f"""
    <html>
    <head>
      <title>Hospital Prober Dashboard</title>
      <meta http-equiv="refresh" content="10" />
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto+Mono&display=swap');

        * {{
          box-sizing: border-box;
        }}

        body {{
          margin: 0;
          padding: 2rem;
          font-family: 'Inter', sans-serif;
          background: linear-gradient(145deg, #0f172a, #1e293b);
          color: #e2e8f0;
          display: flex;
          flex-direction: column;
          align-items: center;
          min-height: 100vh;
        }}

        h1 {{
          font-size: 2.5rem;
          margin-bottom: 0.25rem;
          color: #60a5fa;
        }}

        .timestamp {{
          font-size: 0.95rem;
          color: #94a3b8;
          margin-bottom: 2rem;
        }}

        .card {{
          background: #1e293b;
          border-radius: 12px;
          padding: 1.5rem 2rem;
          margin-bottom: 2rem;
          max-width: 700px;
          width: 100%;
          box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
          transition: transform 0.2s;
        }}

        .card:hover {{
          transform: translateY(-2px);
        }}

        ul {{
          list-style: none;
          padding: 0;
          margin: 0;
        }}

        li {{
          padding: 0.75rem 0;
          border-bottom: 1px solid #334155;
          font-size: 1rem;
          line-height: 1.6;
        }}

        li:last-child {{
          border-bottom: none;
        }}

        .metrics-title {{
          color: #38bdf8;
          font-size: 1.5rem;
          margin-bottom: 1rem;
        }}

        .footer {{
          font-size: 0.85rem;
          color: #64748b;
          margin-top: auto;
          margin-top: 3rem;
        }}
      </style>
    </head>
    <body>
      <h1>Hospital Prober Dashboard</h1>
      <div class="timestamp">Last probe run: {probe_results.get('last_run', 'N/A')}</div>
      
      <div class="card">
        <ul>
          {"".join(f"<li>{r}</li>" for r in probe_results.get('results', []))}
        </ul>
      </div>

      {metrics_html}

      <div class="footer">Page auto-refreshes every 10 seconds.</div>
    </body>
    </html>
    """
    return html_content
