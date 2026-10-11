// Dashboard: list, filter, create, edit, complete, delete.
// Not signed in (or just logged out and pressed Back)? Go to login.
function requireLogin() {
  if (!Auth.access) window.location.replace("/login/");
}
requireLogin();
window.addEventListener("pageshow", requireLogin);

const state = { status: "all", search: "", priority: "", editingId: null, tasks: [] };

const els = {
  form: document.getElementById("taskForm"),
  panel: document.querySelector(".form-panel"),
  formTitle: document.getElementById("formTitle"),
  saveBtn: document.getElementById("saveBtn"),
  cancelBtn: document.getElementById("cancelEditBtn"),
  list: document.getElementById("taskList"),
  empty: document.getElementById("emptyState"),
  count: document.getElementById("count"),
  search: document.getElementById("search"),
  priority: document.getElementById("priorityFilter"),
  tabs: document.querySelectorAll(".status-tabs .btn"),
};

const todayISO = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 10);
};

function formatDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

// ---------- loading & rendering ----------
async function loadTasks() {
  const params = new URLSearchParams({ status: state.status, ordering: "due_date" });
  if (state.search) params.set("search", state.search);
  if (state.priority) params.set("priority", state.priority);
  try {
    state.tasks = await api(`/tasks/?${params}`);
    render();
  } catch (err) {
    if (err.status !== 401) toast("Could not load your tasks.", "error");
  }
}

function render() {
  els.list.replaceChildren();
  const n = state.tasks.length;
  els.count.textContent = n ? `${n} ${n === 1 ? "task" : "tasks"}, earliest due date first` : "";
  els.empty.classList.toggle("d-none", n > 0);
  if (!n) {
    const filtered = state.search || state.priority || state.status !== "all";
    els.empty.textContent = filtered
      ? "No tasks match these filters."
      : "No tasks yet. Add your first one using the form.";
  }
  state.tasks.forEach((t) => els.list.appendChild(taskNode(t)));
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function taskNode(t) {
  const done = t.status === "completed";
  const li = el("li", `task${done ? " done" : ""}`);
  li.dataset.priority = t.priority;

  const check = el("input", "task-check");
  check.type = "checkbox";
  check.checked = done;
  check.title = done ? "Mark as pending" : "Mark as completed";
  check.setAttribute("aria-label", check.title + ": " + t.title);
  check.addEventListener("change", () => toggleDone(t, check));

  const body = el("div");
  body.appendChild(el("h3", "task-title h6", t.title));
  if (t.description) body.appendChild(el("p", "task-desc", t.description));
  const meta = el("div", "task-meta");
  meta.appendChild(el("span", "prio", t.priority[0].toUpperCase() + t.priority.slice(1) + " priority"));
  const overdue = !done && t.due_date < todayISO();
  const due = el("span", overdue ? "overdue" : "", (overdue ? "Overdue, was due " : "Due ") + formatDate(t.due_date));
  meta.appendChild(due);
  body.appendChild(meta);

  const actions = el("div", "task-actions");
  const edit = el("button", "btn btn-sm btn-outline-secondary", "Edit");
  edit.type = "button";
  edit.addEventListener("click", () => startEdit(t));
  const del = el("button", "btn btn-sm btn-outline-danger", "Delete");
  del.type = "button";
  del.addEventListener("click", () => removeTask(t));
  actions.append(edit, del);

  li.append(check, body, actions);
  return li;
}

// ---------- actions ----------
async function toggleDone(t, checkbox) {
  checkbox.disabled = true;
  try {
    if (t.status === "completed") {
      await api(`/tasks/${t.id}/`, { method: "PATCH", body: { status: "pending" } });
      toast("Task moved back to pending.");
    } else {
      await api(`/tasks/${t.id}/complete/`, { method: "POST" });
      toast("Task marked as completed.");
    }
    await loadTasks();
  } catch (err) {
    checkbox.checked = t.status === "completed";
    checkbox.disabled = false;
    toast("Could not update the task.", "error");
  }
}

async function removeTask(t) {
  if (!confirm(`Delete "${t.title}"? This cannot be undone.`)) return;
  try {
    await api(`/tasks/${t.id}/`, { method: "DELETE" });
    if (state.editingId === t.id) resetForm();
    toast("Task deleted.");
    await loadTasks();
  } catch (err) {
    toast("Could not delete the task.", "error");
  }
}

function startEdit(t) {
  state.editingId = t.id;
  clearErrors(els.form);
  els.form.elements.title.value = t.title;
  els.form.elements.description.value = t.description;
  els.form.elements.priority.value = t.priority;
  els.form.elements.due_date.value = t.due_date;
  els.formTitle.textContent = "Edit task";
  els.saveBtn.textContent = "Save changes";
  els.cancelBtn.classList.remove("d-none");
  els.panel.classList.add("editing");
  els.form.elements.title.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  state.editingId = null;
  els.form.reset();
  els.form.elements.due_date.min = todayISO();
  clearErrors(els.form);
  els.formTitle.textContent = "Add a task";
  els.saveBtn.textContent = "Add task";
  els.cancelBtn.classList.add("d-none");
  els.panel.classList.remove("editing");
}

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors(els.form);
  const payload = {
    title: els.form.elements.title.value.trim(),
    description: els.form.elements.description.value.trim(),
    priority: els.form.elements.priority.value,
    due_date: els.form.elements.due_date.value,
  };
  // Client-side checks (the API validates again).
  const local = {};
  if (!payload.title) local.title = ["Title is required."];
  if (!payload.due_date) local.due_date = ["Pick a due date."];
  if (Object.keys(local).length) return showErrors(els.form, { data: local });

  els.saveBtn.disabled = true;
  try {
    if (state.editingId) {
      await api(`/tasks/${state.editingId}/`, { method: "PATCH", body: payload });
      toast("Task updated.");
    } else {
      await api("/tasks/", { method: "POST", body: payload });
      toast("Task added.");
    }
    resetForm();
    await loadTasks();
  } catch (err) {
    if (err.status !== 401) showErrors(els.form, err);
  } finally {
    els.saveBtn.disabled = false;
  }
});

els.cancelBtn.addEventListener("click", resetForm);

// ---------- filters ----------
els.tabs.forEach((btn) =>
  btn.addEventListener("click", () => {
    els.tabs.forEach((b) => b.classList.toggle("active", b === btn));
    state.status = btn.dataset.status;
    loadTasks();
  })
);
els.priority.addEventListener("change", () => { state.priority = els.priority.value; loadTasks(); });

let searchTimer;
els.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { state.search = els.search.value.trim(); loadTasks(); }, 250);
});

// ---------- header ----------
document.getElementById("logoutBtn").addEventListener("click", Auth.logout);
(async function init() {
  document.getElementById("whoami").textContent = Auth.username;
  resetForm();
  try {
    const me = await api("/auth/me/");
    document.getElementById("whoami").textContent = me.username;
    localStorage.setItem("tp_username", me.username);
  } catch (_) { /* handled by api() */ }
  loadTasks();
})();
