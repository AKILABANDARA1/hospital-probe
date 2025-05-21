# Background probe logic
import requests
import socket
import time
import random
import threading

TARGET_IP = "172.210.155.65"
HTTP_PORTS = [80, 443]

def tcp_check(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=3):
            print(f"[+] TCP port {port} is open on {ip}")
    except Exception as e:
        print(f"[-] TCP port {port} closed on {ip}: {e}")

def http_check(ip, port):
    try:
        scheme = "https" if port == 443 else "http"
        url = f"{scheme}://{ip}"
        res = requests.head(url, timeout=3, verify=False)
        print(f"[+] {scheme.upper()} check on port {port} returned: {res.status_code}")
    except requests.exceptions.SSLError:
        print(f"[!] SSL error on {ip}:{port}")
    except Exception as e:
        print(f"[-] {scheme.upper()} request failed on {ip}:{port}: {e}")

def run_probe_loop():
    print("[*] Prober started.")
    while True:
        print("[*] Starting probe cycle...")
        for port in HTTP_PORTS:
            tcp_check(TARGET_IP, port)
            http_check(TARGET_IP, port)
        sleep_time = random.randint(15, 30)
        print(f"[*] Sleeping {sleep_time}s...\n")
        time.sleep(sleep_time)

# Run in background thread when imported
threading.Thread(target=run_probe_loop, daemon=True).start()
