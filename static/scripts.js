async function loadTasks() {
    const res = await fetch('/tasks');
    const tasks = await res.json();
    const list = document.getElementById("taskList");
    list.innerHTML = "";

    tasks.forEach(task => {
        const li = document.createElement("li");
        li.textContent = task.title + (task.completed ? " ✔" : "");

        // Trash icon for deletion
        const delBtn = document.createElement("span");
        delBtn.textContent = "🗑️"; // Unicode trash icon
        delBtn.className = "delete-btn";
        delBtn.onclick = (e) => {
            e.stopPropagation(); // prevent triggering li click if added later
            deleteTask(task.id);
        };

        li.appendChild(delBtn);
        list.appendChild(li);
    });
}

async function addTask() {
    const title = document.getElementById("taskInput").value;
    if(title.trim() === "") return;

    await fetch('/tasks', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title})
    });

    document.getElementById("taskInput").value = "";
    loadTasks();
}

async function deleteTask(id) {
    await fetch(`/tasks/${id}`, {method: 'DELETE'});
    loadTasks();
}

loadTasks();
