import requests
import socket
import time
import random
import threading

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

TARGET_IP = "172.210.155.65"
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
        <div style="background:#1e2a58; padding:1rem 2rem; border-radius:8px; max-width:650px; margin-top:2rem; box-shadow: 0 4px 10px rgba(0,0,0,0.3); color:#a1c0ff; font-family: 'Roboto Mono', monospace;">
          <h2 style="color:#4a90e2; margin-top:0;">Latest Hospital VM Metrics</h2>
          <ul style="list-style:none; padding-left:0;">
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
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap');

        body {{
          margin: 0;
          background: #121f3d;
          color: #c8d7ff;
          font-family: 'Roboto Mono', monospace;
          display: flex;
          flex-direction: column;
          align-items: center;
          min-height: 100vh;
          padding: 2rem;
        }}

        h1 {{
          margin-bottom: 0.25rem;
          font-weight: 700;
          color: #4a90e2;
          letter-spacing: 1px;
        }}

        .timestamp {{
          margin-bottom: 1.5rem;
          font-size: 0.9rem;
          color: #a1b9ff;
          font-style: italic;
        }}

        ul {{
          list-style: none;
          padding: 1rem 2rem;
          background: #1e2a58;
          border-radius: 8px;
          box-shadow: 0 4px 10px rgba(0,0,0,0.3);
          max-width: 650px;
          width: 100%;
        }}

        li {{
          padding: 0.5rem 0;
          border-bottom: 1px solid #3657a3;
          line-height: 1.4;
        }}

        li:last-child {{
          border-bottom: none;
        }}

        p {{
          margin-top: 2rem;
          font-size: 0.85rem;
          color: #7c98d9;
        }}
      </style>
    </head>
    <body>
      <h1>Hospital Prober Dashboard</h1>
      <div class="timestamp">Last probe run: {probe_results.get('last_run', 'N/A')}</div>
      <ul>
        {"".join(f"<li>{r}</li>" for r in probe_results.get('results', []))}
      </ul>
      {metrics_html}
      <p>Page auto-refreshes every 10 seconds.</p>
    </body>
    </html>
    """
    return html_content
