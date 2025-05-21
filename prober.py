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

# Shared variable for latest probe results
probe_results = {
    "last_run": None,
    "results": []
}

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

# Start probe loop in background thread
threading.Thread(target=run_probe_loop, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    html_content = f"""
    <html>
    <head>
      <title>Prober Dashboard</title>
      <meta http-equiv="refresh" content="20" />
      <style>
        body {{ font-family: Arial, sans-serif; padding: 2em; }}
        h1 {{ color: #2a9d8f; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ margin: 0.5em 0; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
      </style>
    </head>
    <body>
      <h1>Hospital Prober Dashboard</h1>
      <div class="timestamp">Last probe run: {probe_results.get('last_run', 'N/A')}</div>
      <ul>
        {"".join(f"<li>{r}</li>" for r in probe_results.get("results", []))}
      </ul>
      <p>Page auto-refreshes every 20 seconds.</p>
    </body>
    </html>
    """
    return html_content
