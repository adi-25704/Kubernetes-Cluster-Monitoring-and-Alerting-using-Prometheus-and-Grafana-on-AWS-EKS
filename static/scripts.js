// static/scripts.js
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const taskList = document.getElementById("task-list");
  const taskInput = document.getElementById("task-input");
  const addBtn = document.getElementById("add-task-btn");
  const searchInput = document.getElementById("search-input");
  const sortSelect = document.getElementById("sort-select");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const emptyState = document.getElementById("empty-state");
  const totalCountSpan = document.getElementById("total-count");
  const countsBanner = document.getElementById("counts");
  const btnClearCompleted = document.getElementById("btn-clear-completed");
  const btnMarkAll = document.getElementById("btn-mark-all");
  const openAdvancedBtn = document.getElementById("open-advanced-btn");

  // Modal elements (Bootstrap)
  const taskModalEl = document.getElementById("task-modal");
  const taskModal = new bootstrap.Modal(taskModalEl, {});
  const modalForm = document.getElementById("task-form");
  const modalTitleInput = document.getElementById("modal-title-input");
  const modalDescInput = document.getElementById("modal-desc-input");
  const modalDueInput = document.getElementById("modal-due-input");
  const modalPriorityInput = document.getElementById("modal-priority-input");
  const modalTaskId = document.getElementById("task-id");
  const modalTitle = document.getElementById("modal-title");

  let tasks = [];
  let currentFilter = "all";
  let currentSearch = "";
  let currentSort = sortSelect.value;

  // Helpers
  function formatDate(d) {
    if (!d) return "";
    const dt = new Date(d);
    return dt.toLocaleDateString();
  }
  function daysUntil(d) {
    if(!d) return Infinity;
    const now = new Date(); const due = new Date(d);
    const diff = Math.ceil((due - now) / (1000*60*60*24));
    return diff;
  }

  // API
  async function apiFetch(path, opts = {}) {
    const res = await fetch(path, opts);
    if (!res.ok) {
      const txt = await res.text();
      console.error("API error", path, res.status, txt);
      throw new Error(`API ${path} returned ${res.status}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  async function loadTasks() {
    const q = new URLSearchParams({ search: currentSearch, sort: currentSort });
    const data = await apiFetch(`/tasks?${q.toString()}`);
    tasks = data;
    renderAll();
  }

  async function addTask(payload) {
    const newTask = await apiFetch("/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    // push locally and re-render (faster)
    tasks.unshift(newTask);
    renderAll();
  }

  async function updateTask(id, payload) {
    const updated = await apiFetch(`/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    // replace local copy
    tasks = tasks.map(t => t.id === updated.id ? updated : t);
    renderAll();
  }

  async function deleteTask(id) {
    await apiFetch(`/tasks/${id}`, { method: "DELETE" });
    tasks = tasks.filter(t => t.id !== id);
    renderAll();
  }

  async function clearCompleted() {
    await apiFetch("/tasks/clear_completed", { method: "POST" });
    await loadTasks();
  }

  async function markAll(complete) {
    await apiFetch("/tasks/mark_all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed: complete })
    });
    await loadTasks();
  }

  // Render
  function renderAll() {
    taskList.innerHTML = "";
    const visible = tasks.filter(t => {
      if (currentFilter === "active") return !t.completed;
      if (currentFilter === "completed") return t.completed;
      return true;
    });
    if (visible.length === 0) {
      emptyState.style.display = "";
    } else {
      emptyState.style.display = "none";
    }
    // counts
    const total = tasks.length;
    const completed = tasks.filter(t => t.completed).length;
    const active = total - completed;
    totalCountSpan.textContent = total;
    countsBanner.textContent = `${active} active • ${completed} completed`;
    // sort visible already done server-side, but keep client stability
    visible.forEach(t => {
      const li = document.createElement("li");
      li.className = "list-group-item task-item d-flex align-items-start gap-3";
      li.dataset.id = t.id;

      // left: checkbox
      const chk = document.createElement("input");
      chk.type = "checkbox";
      chk.className = "form-check-input mt-1";
      chk.checked = !!t.completed;
      chk.addEventListener("change", async () => {
        await updateTask(t.id, { completed: chk.checked });
      });

      // content
      const divMain = document.createElement("div");
      divMain.style.flex = "1";

      // title row
      const titleRow = document.createElement("div");
      titleRow.className = "d-flex align-items-start justify-content-between";
      const title = document.createElement("div");
      title.className = "task-title";
      if (t.completed) title.classList.add("completed");
      title.style.cursor = "pointer";
      title.innerHTML = `<strong>${escapeHtml(t.title)}</strong>`;

      title.addEventListener("click", () => openEditModal(t));

      const metaRight = document.createElement("div");
      metaRight.className = "text-end small-muted";

      // priority badge
      const prBadge = document.createElement("span");
      prBadge.className = "me-2 small";
      if (t.priority === "high") prBadge.classList.add("priority-high");
      else if (t.priority === "medium") prBadge.classList.add("priority-medium");
      else prBadge.classList.add("priority-low");
      prBadge.textContent = (t.priority || "medium").toUpperCase();

      // due
      const dueSpan = document.createElement("div");
      dueSpan.className = "small-muted";
      const dueText = t.due_date ? formatDate(t.due_date) : "";
      dueSpan.textContent = dueText;

      metaRight.appendChild(prBadge);
      metaRight.appendChild(document.createElement("br"));
      metaRight.appendChild(dueSpan);

      titleRow.appendChild(title);
      titleRow.appendChild(metaRight);

      // description and meta
      const desc = document.createElement("div");
      desc.className = "task-meta small-muted";
      desc.innerHTML = escapeHtml(t.description || "");
      const created = document.createElement("div");
      created.className = "small-muted mt-1";
      created.textContent = `Created: ${formatDate(t.created_at)}`;

      // actions (edit/delete)
      const actions = document.createElement("div");
      actions.className = "d-flex flex-column gap-1 ms-2";

      const btnEdit = document.createElement("button");
      btnEdit.className = "btn btn-sm btn-outline-secondary";
      btnEdit.innerHTML = '<i class="fa fa-pen"></i>';
      btnEdit.title = "Edit";
      btnEdit.addEventListener("click", () => openEditModal(t));

      const btnDelete = document.createElement("button");
      btnDelete.className = "btn btn-sm btn-outline-danger";
      btnDelete.innerHTML = '<i class="fa fa-trash"></i>';
      btnDelete.title = "Delete";
      btnDelete.addEventListener("click", async () => {
        if (!confirm("Delete this task?")) return;
        await deleteTask(t.id);
      });

      actions.appendChild(btnEdit);
      actions.appendChild(btnDelete);

      divMain.appendChild(titleRow);
      if (t.description) divMain.appendChild(desc);
      divMain.appendChild(created);

      // due soon highlight
      const wrapper = document.createElement("div");
      wrapper.className = "d-flex w-100 align-items-center";
      if (!t.completed && daysUntil(t.due_date) <= 2) {
        li.classList.add("due-soon");
      }

      wrapper.appendChild(chk);
      wrapper.appendChild(divMain);

      li.appendChild(wrapper);
      li.appendChild(actions);
      taskList.appendChild(li);
    });
  }

  // modal helpers
  function openAddModal(prefill = {}) {
    modalTitle.textContent = "Add Task";
    modalTaskId.value = "";
    modalTitleInput.value = prefill.title || "";
    modalDescInput.value = prefill.description || "";
    modalDueInput.value = prefill.due_date || "";
    modalPriorityInput.value = prefill.priority || "medium";
    taskModal.show();
    modalTitleInput.focus();
  }
  function openEditModal(task) {
    modalTitle.textContent = "Edit Task";
    modalTaskId.value = task.id;
    modalTitleInput.value = task.title || "";
    modalDescInput.value = task.description || "";
    modalDueInput.value = task.due_date ? task.due_date.split("T")[0] : "";
    modalPriorityInput.value = task.priority || "medium";
    taskModal.show();
  }

  // Escape helper
  function escapeHtml(s) {
    if (!s) return "";
    return s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  }

  // Events
  addBtn.addEventListener("click", () => {
    const title = taskInput.value.trim();
    if (!title) { openAddModal(); return; }
    addTask({ title, description: "", due_date: null, priority: "medium" })
      .then(() => { taskInput.value = ""; });
  });

  taskInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") addBtn.click();
  });

  searchInput.addEventListener("input", async (e) => {
    currentSearch = e.target.value.trim();
    await loadTasks();
  });

  sortSelect.addEventListener("change", async (e) => {
    currentSort = e.target.value;
    await loadTasks();
  });

  filterBtns.forEach(b => {
    b.addEventListener("click", async () => {
      filterBtns.forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      currentFilter = b.dataset.filter;
      renderAll();
    });
  });

  btnClearCompleted.addEventListener("click", async () => {
    if (!confirm("Delete all completed tasks?")) return;
    await clearCompleted();
  });

  btnMarkAll.addEventListener("click", async () => {
    // toggle: if some are incomplete, mark all complete; otherwise, unmark all
    const someIncomplete = tasks.some(t => !t.completed);
    await markAll(someIncomplete);
  });

  openAdvancedBtn.addEventListener("click", () => {
    openAddModal();
  });

  modalForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = modalTaskId.value;
    const payload = {
      title: modalTitleInput.value.trim(),
      description: modalDescInput.value.trim(),
      due_date: modalDueInput.value || null,
      priority: modalPriorityInput.value || "medium"
    };
    if (!payload.title) { alert("Title required"); return; }
    if (id) {
      await updateTask(Number(id), payload);
    } else {
      await addTask({ ...payload });
    }
    taskModal.hide();
  });

  // initial load
  loadTasks().catch(err => {
    console.error("Failed to load tasks:", err);
  });
});
