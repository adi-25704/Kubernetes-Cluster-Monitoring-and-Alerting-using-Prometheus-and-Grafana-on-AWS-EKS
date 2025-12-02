import time
import random
import threading
import math
from flask import Flask, render_template, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- METRICS ---
HTTP_REQUESTS = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["endpoint"])
SALES_TOTAL = Counter("sales_dollars_total", "Total sales in dollars")
INVENTORY = Gauge("inventory_items", "Current items in stock", ["product"])
ACTIVE_USERS = Gauge("active_users", "Fake active users count")

# --- CHAOS SETTINGS ---
chaos_config = {
    "latency": False,     # Sleep 2s
    "error_rate": False,  # 50% 500 Errors
    "cpu_stress": False,  # Calculate Factorials (Burns CPU)
    "memory_leak": False  # Appends to a global list (Eats RAM)
}

# Fake Memory Leak Storage
leak_storage = []

# --- FAKE DATABASE ---
products = {
    "laptop": {"price": 1200, "stock": 50},
    "phone": {"price": 800, "stock": 100},
    "headphones": {"price": 200, "stock": 200}
}

for p, data in products.items():
    INVENTORY.labels(product=p).set(data["stock"])

# --- BACKGROUND TRAFFIC GENERATOR (TURBO MODE) ---
def traffic_simulator():
    """Generates heavy background traffic"""
    while True:
        try:
            # Fluctuate users more aggressively
            ACTIVE_USERS.set(random.randint(200, 5000))
            
            if not chaos_config["error_rate"]:
                p = random.choice(list(products.keys()))
                SALES_TOTAL.inc(products[p]["price"])
                
                # Auto-restock to keep graph moving
                products[p]["stock"] -= 1
                if products[p]["stock"] < 10: products[p]["stock"] = 100 
                INVENTORY.labels(product=p).set(products[p]["stock"])

            # If Memory Leak is on, add 1MB string to memory every cycle
            if chaos_config["memory_leak"]:
                leak_storage.append("A" * 1024 * 1024) 

        except Exception:
            pass
        
        # Sleep ONLY 0.05s to create massive traffic (20 requests/sec)
        time.sleep(0.05)

t = threading.Thread(target=traffic_simulator)
t.daemon = True
t.start()

# --- CPU BURNER ---
def burn_cpu():
    """Forces CPU usage by doing useless math"""
    # Calculate factorial of 5000 (Very heavy operation)
    math.factorial(5000)

@app.route("/")
def index():
    start = time.time()
    status = 200
    
    # 1. CPU Stress (Blocks the thread to spike CPU usage)
    if chaos_config["cpu_stress"]:
        burn_cpu()

    # 2. Latency (Sleeps)
    if chaos_config["latency"]:
        time.sleep(random.uniform(1.0, 2.0))
        
    # 3. Error Rate
    if chaos_config["error_rate"] and random.random() < 0.5:
        status = 500
        HTTP_REQUESTS.labels(method="GET", endpoint="/", status=500).inc()
        return render_template("index.html", error=True, chaos=chaos_config, products=products), 500

    HTTP_REQUESTS.labels(method="GET", endpoint="/", status=200).inc()
    REQUEST_LATENCY.labels(endpoint="/").observe(time.time() - start)
    return render_template("index.html", products=products, chaos=chaos_config)

@app.route("/buy/<product>", methods=["POST"])
def buy(product):
    start = time.time()
    
    if chaos_config["cpu_stress"]:
        burn_cpu()

    if chaos_config["error_rate"]:
        HTTP_REQUESTS.labels(method="POST", endpoint="/buy", status=500).inc()
        return jsonify({"error": "Payment Gateway Failed"}), 500

    if product in products:
        SALES_TOTAL.inc(products[product]["price"])
        HTTP_REQUESTS.labels(method="POST", endpoint="/buy", status=200).inc()
        REQUEST_LATENCY.labels(endpoint="/buy").observe(time.time() - start)
        return jsonify({"status": "purchased"})
    
    return jsonify({"error": "Not found"}), 404

@app.route("/api/chaos/<type>/<action>", methods=["POST"])
def set_chaos(type, action):
    global leak_storage
    if type in chaos_config:
        chaos_config[type] = (action == "on")
        # Clear memory if leak is turned off
        if type == "memory_leak" and action == "off":
            leak_storage = []
    return jsonify(chaos_config)

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)