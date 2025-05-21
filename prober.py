import requests
import socket
import time
import random
import threading

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

TARGET_IP = "20.109.32.217"
HTTP_PORTS = [80, 443]

probe_results = {
    "last_run": None,
    "results": []
}

metrics_data = {}

# TCP Port Check
def tcp_check(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=3):
            return f"TCP port {port} is open"
    except Exception as e:
        return f"TCP port {port} closed ({e})"

# HTTP/S Head Request
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

# Background Probe Loop
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
async def receive_metrics(request: Request):
    global metrics_data
    try:
        data = await request.json()
        metrics_data = data
        return {"status": "received"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

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
        body {{
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background-color: #1e293b;
          color: #e2e8f0;
          padding: 2rem;
        }}
        h1 {{
          color: #60a5fa;
        }}
        .card {{
          background: #2d3748;
          padding: 1rem 2rem;
          border-radius: 10px;
          margin-bottom: 1rem;
        }}
        li {{
          padding: 0.5rem 0;
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

      <p style="color: #64748b; margin-top: 2rem;">Page auto-refreshes every 10 seconds.</p>
    </body>
    </html>
    """
    return html_content
