document.addEventListener("DOMContentLoaded", () => {
    // --- Element References ---
    const taskList = document.getElementById("task-list");
    const taskInput = document.getElementById("task-input");
    const addTaskBtn = document.getElementById("add-task-btn");
    const filterBtns = document.querySelectorAll(".filter-btn");
    
    // Modal Elements
    const modal = document.getElementById("edit-modal");
    const modalInput = document.getElementById("edit-task-input");
    const modalSaveBtn = document.getElementById("edit-save-btn");
    const modalCancelBtn = document.getElementById("edit-cancel-btn");
    
    let currentEditTaskId = null; // Stores the ID of the task being edited

    // --- State ---
    let currentFilter = "all"; // 'all', 'active', 'completed'

    // --- API Functions ---

    /**
     * Fetches all tasks from the API and re-renders the list.
     */
    const loadTasks = async () => {
        try {
            const response = await fetch("/tasks");
            if (!response.ok) throw new Error("Could not fetch tasks");
            const tasks = await response.json();
            
            taskList.innerHTML = ""; // Clear list before re-rendering
            tasks.forEach(task => renderTask(task));
            
            // Re-apply the current filter after re-rendering
            applyFilter();
        } catch (error) {
            console.error("Error fetching tasks:", error);
        }
    };

    /**
     * Creates a new task.
     */
    const addTask = async () => {
        const title = taskInput.value.trim();
        if (title === "") {
            alert("Task title cannot be empty!");
            return;
        }

        try {
            const response = await fetch("/tasks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: title })
            });

            if (!response.ok) throw new Error("Could not add task");

            // --- THIS IS THE FIX ---

            // 1. Get the new task object back from the API response
            const newTask = await response.json(); 

            taskInput.value = ""; // Clear input
            
            // 2. Instead of re-fetching all tasks, just render the new one.
            //    This is *much* faster.
            renderTask(newTask);
            
            // 3. Re-apply the filter in case we're on "Completed"
            //    (This will correctly hide the new, active task)
            applyFilter();
            
            // OLD, SLOW WAY (REMOVED):
            // await loadTasks(); 

            // --- END OF FIX ---

        } catch (error) {
            console.error("Error adding task:", error);
        }
    };

    /**
     * Toggles the 'completed' status of a task.
     * (This still uses the re-fetch method, which is fine for updates)
     */
    const toggleTaskComplete = async (id, completed) => {
        try {
            await fetch(`/tasks/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ completed: completed })
            });
            await loadTasks(); // Re-fetch and render all tasks
        } catch (error) {
            console.error("Error updating task:", error);
        }
    };

    /**
     * Deletes a task by its ID.
     * (This still uses the re-fetch method, which is fine for updates)
     */
    const deleteTask = async (id) => {
        if (!confirm("Are you sure you want to delete this task?")) {
            return;
        }
        
        try {
            await fetch(`/tasks/${id}`, {
                method: "DELETE"
            });
            await loadTasks(); // Re-fetch and render all tasks
        } catch (error) {
            console.error("Error deleting task:", error);
        }
    };
    
    /**
     * Updates a task's title.
     * (This still uses the re-fetch method, which is fine for updates)
     */
    const updateTaskTitle = async (id, newTitle) => {
        if (newTitle.trim() === "") {
            alert("Title cannot be empty!");
            return;
        }
        
        try {
             await fetch(`/tasks/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle })
            });
            closeEditModal();
            await loadTasks(); // Re-fetch and render all tasks
        } catch (error) {
            console.error("Error updating title:", error);
        }
    };

    // --- DOM Rendering & Modal Logic ---

    /**
     * Renders a single task item and appends it to the task list.
     */
    const renderTask = (task) => {
        const li = document.createElement("li");
        li.className = "task-item";
        li.dataset.id = task.id;
        li.dataset.completed = task.completed;

        if (task.completed) {
            li.classList.add("completed");
        }

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "checkbox";
        checkbox.checked = task.completed;
        checkbox.addEventListener("change", () => toggleTaskComplete(task.id, checkbox.checked));

        const span = document.createElement("span");
        span.className = "task-title";
        span.textContent = task.title;

        const actions = document.createElement("div");
        actions.className = "task-actions";

        const editBtn = document.createElement("button");
        editBtn.className = "edit-btn";
        editBtn.innerHTML = '<i class="fa fa-pencil"></i>';
        editBtn.title = "Edit task";
        editBtn.addEventListener("click", () => showEditModal(task.id, task.title));

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-btn";
        deleteBtn.innerHTML = '<i class="fa fa-trash"></i>';
        deleteBtn.title = "Delete task";
        deleteBtn.addEventListener("click", () => deleteTask(task.id));

        actions.appendChild(editBtn);
        actions.appendChild(deleteBtn);
        li.appendChild(checkbox);
        li.appendChild(span);
        li.appendChild(actions);
        taskList.appendChild(li); // Adds the new item to the list
    };

    /**
     * Shows the edit modal with the task's current title.
     */
    const showEditModal = (id, title) => {
        currentEditTaskId = id;
        modalInput.value = title;
        modal.style.display = "flex";
        modalInput.focus();
    };

    /**
     * Hides the edit modal.
     */
    const closeEditModal = () => {
        currentEditTaskId = null;
        modal.style.display = "none";
    };

    /**
     * Applies the current filter to the task list (client-side).
     */
    const applyFilter = () => {
        const tasks = taskList.querySelectorAll(".task-item");
        tasks.forEach(task => {
            const isCompleted = task.dataset.completed === 'true';
            switch (currentFilter) {
                case 'active':
                    task.classList.toggle('hidden', isCompleted);
                    break;
                case 'completed':
                    task.classList.toggle('hidden', !isCompleted);
                    break;
                case 'all':
                default:
                    task.classList.remove('hidden');
                    break;
            }
        });
    };

    // --- Event Listeners ---

    // Add task (button click)
    addTaskBtn.addEventListener("click", addTask);
    
    // Add task (Enter key)
    taskInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            addTask();
        }
    });

    // Modal "Save" button
    modalSaveBtn.addEventListener("click", () => {
        updateTaskTitle(currentEditTaskId, modalInput.value);
    });

    // Modal "Cancel" button
    modalCancelBtn.addEventListener("click", closeEditModal);

    // Filter buttons
    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            // Update active button style
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Set filter and apply it
            currentFilter = btn.dataset.filter;
            applyFilter();
        });
    });

    // --- Initial Load ---
    loadTasks();
});