from flask import Flask, request, jsonify, render_template
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# --- In-memory "database" ---
tasks = []
task_id_counter = 1

# --- Prometheus Metrics ---
REQUEST_COUNTER = Counter(
    "todo_http_requests_total", 
    "Total HTTP requests", 
    ["method", "endpoint"]
)
TASK_CREATION_TIME = Histogram(
    "todo_task_creation_seconds",
    "Time spent creating task"
)
TASK_DELETION_TIME = Histogram(
    "todo_task_deletion_seconds",
    "Time spent deleting task"
)
TASKS_CREATED = Counter(
    "todo_tasks_created_total",
    "Total number of tasks created"
)
TASKS_DELETED = Counter(
    "todo_tasks_deleted_total",
    "Total number of tasks deleted"
)

# --- Frontend Route ---
@app.route("/")
def index():
    """Serves the main HTML page."""
    # This looks for 'index.html' in a folder named 'templates'
    return render_template("index.html")

# --- API Routes ---
@app.route("/tasks", methods=['GET'])
def get_tasks():
    REQUEST_COUNTER.labels(method="GET", endpoint="/tasks").inc()
    return jsonify(tasks)


@app.route("/tasks", methods=['POST'])
@TASK_CREATION_TIME.time()
def create_task():
    global task_id_counter
    REQUEST_COUNTER.labels(method="POST", endpoint="/tasks").inc()

    data = request.json
    
    # --- IMPROVEMENT ---
    # Add validation to prevent empty tasks
    if not data or not data.get("title") or data.get("title").strip() == "":
        return jsonify({"error": "Title is required"}), 400
    # -------------------

    task = {
        "id": task_id_counter,
        "title": data.get("title").strip(),
        "completed": False
    }
    tasks.append(task)
    task_id_counter += 1

    TASKS_CREATED.inc()
    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=['PUT'])
def update_task(task_id):
    REQUEST_COUNTER.labels(method="PUT", endpoint="/tasks/<id>").inc()

    data = request.json
    for task in tasks:
        if task["id"] == task_id:
            # Update title if provided, else keep old title
            task["title"] = data.get("title", task["title"])
            # Update completed status if provided, else keep old status
            task["completed"] = data.get("completed", task["completed"])
            return jsonify(task)

    return jsonify({"error": "Task not found"}), 404


@app.route("/tasks/<int:task_id>", methods=['DELETE'])
@TASK_DELETION_TIME.time()
def delete_task(task_id):
    REQUEST_COUNTER.labels(method="DELETE", endpoint="/tasks/<id>").inc()

    global tasks
    old_length = len(tasks)
    tasks = [task for task in tasks if task["id"] != task_id]

    if len(tasks) < old_length:
        TASKS_DELETED.inc()
        return jsonify({"message": "Task deleted"})

    return jsonify({"error": "Task not found"}), 404


# --- Prometheus Metrics Endpoint ---
@app.route("/metrics")
def metrics():
    """Serves Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# --- Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)