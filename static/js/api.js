// Shared helpers: token storage, authenticated fetch (with auto-refresh), toasts, form errors.
const Auth = {
  get access() { return localStorage.getItem("tp_access"); },
  get refresh() { return localStorage.getItem("tp_refresh"); },
  get username() { return localStorage.getItem("tp_username") || ""; },
  save({ access, refresh }, username) {
    if (access) localStorage.setItem("tp_access", access);
    if (refresh) localStorage.setItem("tp_refresh", refresh);
    if (username) localStorage.setItem("tp_username", username);
  },
  clear() {
    ["tp_access", "tp_refresh", "tp_username"].forEach((k) => localStorage.removeItem(k));
  },
  logout() {
    Auth.clear();
    window.location.replace("/login/");
  },
};

class ApiError extends Error {
  constructor(status, data) {
    super("Request failed");
    this.status = status;
    this.data = data || {};
  }
}

async function refreshAccessToken() {
  if (!Auth.refresh) return false;
  const res = await fetch("/api/auth/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: Auth.refresh }),
  });
  if (!res.ok) return false;
  Auth.save(await res.json());
  return true;
}

// api("/tasks/", { method, body, auth })
async function api(path, { method = "GET", body, auth = true } = {}) {
  const send = () => {
    const headers = { "Content-Type": "application/json" };
    if (auth && Auth.access) headers.Authorization = `Bearer ${Auth.access}`;
    return fetch(`/api${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  };

  let res = await send();
  if (res.status === 401 && auth) {
    if (await refreshAccessToken()) res = await send();
    if (res.status === 401) {
      Auth.logout();
      throw new ApiError(401, {});
    }
  }
  const data = res.status === 204 ? null : await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

// ---- UI helpers ----
function toast(message, kind = "success") {
  const host = document.getElementById("toastHost");
  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${kind === "success" ? "success" : "danger"} border-0`;
  el.setAttribute("role", "status");
  const inner = document.createElement("div");
  inner.className = "d-flex";
  const msg = document.createElement("div");
  msg.className = "toast-body";
  msg.textContent = message;
  inner.appendChild(msg);
  el.appendChild(inner);
  host.appendChild(el);
  // A notification problem (e.g. Bootstrap JS failed to load) must never break the page.
  if (typeof bootstrap !== "undefined" && bootstrap.Toast) {
    const t = new bootstrap.Toast(el, { delay: 2800 });
    el.addEventListener("hidden.bs.toast", () => el.remove());
    t.show();
  } else {
    el.classList.add("show");
    setTimeout(() => el.remove(), 2800);
  }
}

function clearErrors(form) {
  form.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
  form.querySelectorAll(".invalid-feedback").forEach((el) => (el.textContent = ""));
  const alertBox = document.getElementById("formAlert");
  if (alertBox) { alertBox.classList.add("d-none"); alertBox.textContent = ""; }
}

// Shows field errors under inputs; anything else goes in the alert box.
function showErrors(form, err) {
  const alertBox = document.getElementById("formAlert");
  const general = [];
  const data = err.data || {};
  Object.entries(data).forEach(([field, msgs]) => {
    const list = Array.isArray(msgs) ? msgs : [String(msgs)];
    const input = form.elements[field];
    if (input && input.classList) {
      input.classList.add("is-invalid");
      const fb = input.parentElement.querySelector(".invalid-feedback");
      if (fb) fb.textContent = list.join(" ");
    } else {
      general.push(list.join(" "));
    }
  });
  if (!Object.keys(data).length) general.push("Something went wrong. Please try again.");
  if (general.length && alertBox) {
    alertBox.textContent = general.join(" ");
    alertBox.classList.remove("d-none");
  }
}
