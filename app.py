import time
import random
import threading
import os
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
# We use these global flags to simulate bad behavior
chaos_config = {
    "latency": False,   # If True, requests will be slow
    "error_rate": False # If True, 50% of requests will return 500
}

# --- FAKE DATABASE ---
products = {
    "laptop": {"price": 1200, "stock": 50},
    "phone": {"price": 800, "stock": 100},
    "headphones": {"price": 200, "stock": 200}
}

# Initialize Metrics
for p, data in products.items():
    INVENTORY.labels(product=p).set(data["stock"])

# --- BACKGROUND TRAFFIC GENERATOR ---
def traffic_simulator():
    """Simulates background user activity"""
    while True:
        try:
            # Simulate active users fluctuating
            ACTIVE_USERS.set(random.randint(50, 200))
            
            # Randomly simulate sales if not in error mode
            if not chaos_config["error_rate"]:
                p = random.choice(list(products.keys()))
                products[p]["stock"] -= 1
                if products[p]["stock"] < 0: products[p]["stock"] = 100 # Restock
                INVENTORY.labels(product=p).set(products[p]["stock"])
                SALES_TOTAL.inc(products[p]["price"])
                
        except Exception:
            pass
        time.sleep(2)

# Start background thread
t = threading.Thread(target=traffic_simulator)
t.daemon = True
t.start()

# --- ROUTES ---

@app.route("/")
def index():
    start = time.time()
    status = 200
    
    # Simulate Latency
    if chaos_config["latency"]:
        time.sleep(random.uniform(1.0, 3.0))
        
    # Simulate Errors
    if chaos_config["error_rate"] and random.random() < 0.5:
        status = 500
        HTTP_REQUESTS.labels(method="GET", endpoint="/", status=500).inc()
        return render_template("index.html", error=True), 500

    HTTP_REQUESTS.labels(method="GET", endpoint="/", status=200).inc()
    REQUEST_LATENCY.labels(endpoint="/").observe(time.time() - start)
    return render_template("index.html", products=products, chaos=chaos_config)

@app.route("/buy/<product>", methods=["POST"])
def buy(product):
    start = time.time()
    
    # Chaos Logic
    if chaos_config["error_rate"]:
        HTTP_REQUESTS.labels(method="POST", endpoint="/buy", status=500).inc()
        return jsonify({"error": "Payment Gateway Failed"}), 500

    if product in products:
        SALES_TOTAL.inc(products[product]["price"])
        products[product]["stock"] -= 1
        INVENTORY.labels(product=product).set(products[product]["stock"])
        
        HTTP_REQUESTS.labels(method="POST", endpoint="/buy", status=200).inc()
        REQUEST_LATENCY.labels(endpoint="/buy").observe(time.time() - start)
        return jsonify({"status": "purchased", "price": products[product]["price"]})
    
    return jsonify({"error": "Not found"}), 404

# --- API TO CONTROL CHAOS ---
@app.route("/api/chaos/<type>/<action>", methods=["POST"])
def set_chaos(type, action):
    if type in chaos_config:
        chaos_config[type] = (action == "on")
    return jsonify(chaos_config)

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)