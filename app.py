# app.py
import json, os, threading, time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__, static_url_path="/static", template_folder="templates")

DATA_FILE = os.environ.get("TASKS_FILE", "tasks.json")
LOCK = threading.Lock()

# in-memory with load/save
tasks = []
task_id_counter = 1

def load_data():
    global tasks, task_id_counter
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                payload = json.load(f)
                tasks = payload.get("tasks", [])
                task_id_counter = payload.get("counter", 1)
            except Exception:
                tasks = []
                task_id_counter = 1
    else:
        tasks = []
        task_id_counter = 1

def save_data():
    with LOCK:
        with open(DATA_FILE, "w") as f:
            json.dump({"tasks": tasks, "counter": task_id_counter}, f, indent=2, default=str)

# --- Prometheus metrics ---
REQS = Counter("todo_http_requests_total", "Total HTTP requests", ["method", "endpoint"])
TASKS_CREATED = Counter("todo_tasks_created_total", "Total tasks created")
TASKS_DELETED = Counter("todo_tasks_deleted_total", "Total tasks deleted")
TASK_CREATE_TIME = Histogram("todo_task_creation_seconds", "Time spent creating task")
TASK_DELETE_TIME = Histogram("todo_task_deletion_seconds", "Time spent deleting task")

# load persisted data at startup
load_data()

# --- helpers ---
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def find_task(task_id):
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None

# ------------------
# Frontend
# ------------------
@app.route("/")
def index():
    REQS.labels(method="GET", endpoint="/").inc()
    return render_template("index.html")

# serve static explicitly if needed
@app.route("/static/<path:p>")
def static_files(p):
    return send_from_directory("static", p)

# --------------------------------
# API endpoints
# --------------------------------
@app.route("/tasks", methods=["GET"])
def get_tasks():
    REQS.labels(method="GET", endpoint="/tasks").inc()
    q = request.args.get("search", "").strip().lower()
    sort = request.args.get("sort", "created_desc")
    results = tasks.copy()

    # filter
    if q:
        results = [t for t in results if q in t.get("title", "").lower() or q in t.get("description", "").lower()]

    # sort
    if sort == "due_asc":
        results.sort(key=lambda x: (x.get("due_date") is None, x.get("due_date") or ""), reverse=False)
    elif sort == "priority_desc":
        order = {"high": 2, "medium": 1, "low": 0}
        results.sort(key=lambda x: order.get(x.get("priority", "medium"), 1), reverse=True)
    else:  # created_desc
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return jsonify(results)

@app.route("/tasks", methods=["POST"])
@TASK_CREATE_TIME.time()
def create_task():
    global task_id_counter
    REQS.labels(method="POST", endpoint="/tasks").inc()
    data = request.json or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    with LOCK:
        task = {
            "id": task_id_counter,
            "title": title,
            "description": (data.get("description") or "").strip(),
            "completed": False,
            "due_date": data.get("due_date") or None,
            "priority": data.get("priority") or "medium",
            "created_at": now_iso()
        }
        tasks.append(task)
        task_id_counter += 1
        save_data()

    TASKS_CREATED.inc()
    return jsonify(task), 201

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    REQS.labels(method="PUT", endpoint="/tasks/<id>").inc()
    data = request.json or {}
    with LOCK:
        t = find_task(task_id)
        if not t:
            return jsonify({"error": "Task not found"}), 404
        # update fields if present
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                return jsonify({"error": "Title cannot be empty"}), 400
            t["title"] = title
        if "description" in data:
            t["description"] = (data.get("description") or "").strip()
        if "completed" in data:
            t["completed"] = bool(data.get("completed"))
        if "priority" in data:
            t["priority"] = data.get("priority") or "medium"
        if "due_date" in data:
            t["due_date"] = data.get("due_date") or None
        save_data()
        return jsonify(t)

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@TASK_DELETE_TIME.time()
def delete_task(task_id):
    REQS.labels(method="DELETE", endpoint="/tasks/<id>").inc()
    global tasks
    with LOCK:
        before = len(tasks)
        tasks = [t for t in tasks if t.get("id") != task_id]
        if len(tasks) < before:
            TASKS_DELETED.inc()
            save_data()
            return jsonify({"message": "Task deleted"})
    return jsonify({"error": "Task not found"}), 404

# Clear completed tasks
@app.route("/tasks/clear_completed", methods=["POST"])
def clear_completed():
    REQS.labels(method="POST", endpoint="/tasks/clear_completed").inc()
    global tasks
    with LOCK:
        tasks = [t for t in tasks if not t.get("completed")]
        save_data()
    return jsonify({"message": "Cleared completed"}), 200

# Mark all complete/undo
@app.route("/tasks/mark_all", methods=["POST"])
def mark_all():
    REQS.labels(method="POST", endpoint="/tasks/mark_all").inc()
    data = request.json or {}
    value = bool(data.get("completed", True))
    with LOCK:
        for t in tasks:
            t["completed"] = value
        save_data()
    return jsonify({"message": "Updated all"}), 200

# Prometheus metrics endpoint
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# health
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # run for local dev; production should use gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
