// Login and register pages.
// Already signed in? Skip this page. pageshow also fires when the browser
// restores the page from its back/forward cache, where plain scripts don't re-run.
function skipIfSignedIn() {
  if (Auth.access) window.location.replace("/dashboard/");
}
skipIfSignedIn();
window.addEventListener("pageshow", skipIfSignedIn);

function requireFields(form) {
  let ok = true;
  form.querySelectorAll("[required]").forEach((input) => {
    if (!input.value.trim()) {
      input.classList.add("is-invalid");
      const fb = input.parentElement.querySelector(".invalid-feedback");
      if (fb) fb.textContent = "This field is required.";
      ok = false;
    }
  });
  return ok;
}

function wire(formId, endpoint, onSuccess) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors(form);
    if (!requireFields(form)) return;
    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      const payload = Object.fromEntries(new FormData(form).entries());
      const data = await api(endpoint, { method: "POST", body: payload, auth: false });
      onSuccess(data, payload);
    } catch (err) {
      if (err.status === 401) err.data = { detail: "Incorrect username or password." };
      showErrors(form, err);
    } finally {
      btn.disabled = false;
    }
  });
}

wire("loginForm", "/auth/login/", (data, payload) => {
  Auth.save(data, payload.username);
  window.location.replace("/dashboard/");
});

wire("registerForm", "/auth/register/", (data) => {
  Auth.save(data, data.user.username);
  window.location.replace("/dashboard/");
});
