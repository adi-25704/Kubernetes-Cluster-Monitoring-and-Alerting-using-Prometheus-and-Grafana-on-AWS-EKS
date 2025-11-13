from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
# This line automatically creates a /metrics endpoint
metrics = PrometheusMetrics(app)

@app.route('/')
def hello():
    """Serves a simple hello world page."""
    return "Hello! Your EKS application is running."

@app.route('/health')
def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)