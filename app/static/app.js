"use strict";

/* ---------- Auth token storage ---------- */
const TOKEN_KEY = "jobtracker_token";
const getToken = () => localStorage.getItem(TOKEN_KEY);
const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
const clearToken = () => localStorage.removeItem(TOKEN_KEY);

/* ---------- API client ---------- */
function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

const api = {
  async register(email, password) {
    return fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  },
  async login(email, password) {
    // OAuth2 password flow expects form-encoded fields; "username" = email.
    const body = new URLSearchParams({ username: email, password });
    return fetch("/auth/token", { method: "POST", body });
  },
  async me() {
    return fetch("/auth/me", { headers: authHeaders() });
  },
  async jobs(params) {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v !== null))
    );
    return (await fetch(`/jobs?${qs}`)).json();
  },
  async applications() {
    return (await fetch("/applications", { headers: authHeaders() })).json();
  },
  async createApplication(jobId) {
    return fetch("/applications", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ job_id: jobId }),
    });
  },
  async updateApplication(id, data) {
    return fetch(`/applications/${id}`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(data),
    });
  },
  async deleteApplication(id) {
    return fetch(`/applications/${id}`, { method: "DELETE", headers: authHeaders() });
  },
};

const STATUSES = ["saved", "applied", "interview", "offer", "rejected"];
let applicationsCache = [];
let panelApplicationId = null;
let authMode = "login"; // or "signup"

/* ---------- Helpers ---------- */
const $ = (sel) => document.querySelector(sel);

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.remove("hidden");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.add("hidden"), 2500);
}

function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString(currentLang === "fr" ? "fr-FR" : "en-GB", {
    day: "2-digit",
    month: "short",
  });
}

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

/* ---------- View routing ---------- */
function showView(view) {
  ["landing", "auth", "board", "jobs"].forEach((v) =>
    $(`#view-${v}`).classList.toggle("hidden", v !== view)
  );
  const loggedIn = view === "board" || view === "jobs";
  $("#topbar-public").classList.toggle("hidden", loggedIn);
  $("#topbar-app").classList.toggle("hidden", !loggedIn);
  if (view === "board") {
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", t.dataset.view === "board")
    );
    renderBoard();
  } else if (view === "jobs") {
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", t.dataset.view === "jobs")
    );
    renderJobSearch();
  }
}

/* ---------- Auth views ---------- */
function openAuth(mode) {
  authMode = mode;
  $("#auth-error").classList.add("hidden");
  $("#auth-form").reset();
  const isLogin = mode === "login";
  $("#auth-title").textContent = t(isLogin ? "auth.login_title" : "auth.signup_title");
  $("#auth-submit").textContent = t(isLogin ? "auth.login_btn" : "auth.signup_btn");
  $("#auth-password").autocomplete = isLogin ? "current-password" : "new-password";
  $("#auth-switch-text").textContent = t(isLogin ? "auth.no_account" : "auth.have_account");
  $("#auth-switch-link").textContent = t(isLogin ? "auth.switch_signup" : "auth.switch_login");
  showView("auth");
}

async function submitAuth(event) {
  event.preventDefault();
  const email = $("#auth-email").value.trim();
  const password = $("#auth-password").value;
  const errEl = $("#auth-error");
  errEl.classList.add("hidden");

  try {
    let res;
    if (authMode === "signup") {
      res = await api.register(email, password);
      if (res.status === 409) return showAuthError(t("error.email_taken"));
      if (!res.ok) return showAuthError(t("error.generic"));
      setToken((await res.json()).access_token);
    } else {
      res = await api.login(email, password);
      if (res.status === 401) return showAuthError(t("error.bad_login"));
      if (!res.ok) return showAuthError(t("error.generic"));
      setToken((await res.json()).access_token);
    }
    await enterApp();
  } catch {
    showAuthError(t("error.generic"));
  }
}

function showAuthError(message) {
  const errEl = $("#auth-error");
  errEl.textContent = message;
  errEl.classList.remove("hidden");
}

async function enterApp() {
  const res = await api.me();
  if (!res.ok) {
    clearToken();
    return showView("landing");
  }
  const user = await res.json();
  $("#user-email").textContent = user.email;
  applicationsCache = await api.applications();
  showView("board");
}

function logout() {
  clearToken();
  applicationsCache = [];
  showView("landing");
}

/* ---------- Board (Kanban) ---------- */
async function renderBoard() {
  applicationsCache = await api.applications();
  const board = $("#board");
  board.innerHTML = "";

  for (const status of STATUSES) {
    const apps = applicationsCache.filter((a) => a.status === status);
    const column = document.createElement("div");
    column.className = "column";
    column.dataset.status = status;
    column.innerHTML = `
      <div class="column-head">${t("status." + status)} <span class="count">${apps.length}</span></div>
      ${apps.length === 0 ? `<div class="empty">${t("board.drop")}</div>` : ""}
    `;

    for (const app of apps) {
      const card = document.createElement("div");
      card.className = "card";
      card.draggable = true;
      card.dataset.id = app.id;
      card.innerHTML = `
        <h3>${esc(app.job.title)}</h3>
        <div class="company">${esc(app.job.company)}</div>
        <div class="meta">
          <span class="date">${fmtDate(app.job.posted_at || app.created_at)}</span>
          <span class="badge">${esc(app.job.source)}</span>
        </div>
      `;
      card.addEventListener("click", () => openPanel(app.id));
      card.addEventListener("dragstart", (e) => e.dataTransfer.setData("text/plain", String(app.id)));
      column.appendChild(card);
    }

    column.addEventListener("dragover", (e) => {
      e.preventDefault();
      column.classList.add("dragover");
    });
    column.addEventListener("dragleave", () => column.classList.remove("dragover"));
    column.addEventListener("drop", async (e) => {
      e.preventDefault();
      column.classList.remove("dragover");
      const id = Number(e.dataTransfer.getData("text/plain"));
      const res = await api.updateApplication(id, { status: column.dataset.status });
      if (res.ok) {
        toast(`${t("toast.moved")} ${t("status." + column.dataset.status)}`);
        renderBoard();
      }
    });

    board.appendChild(column);
  }
}

/* ---------- Detail panel ---------- */
function openPanel(applicationId) {
  const app = applicationsCache.find((a) => a.id === applicationId);
  if (!app) return;
  panelApplicationId = applicationId;
  $("#panel-title").textContent = app.job.title;
  $("#panel-company").textContent =
    app.job.company + (app.job.location ? ` — ${app.job.location}` : "");
  $("#panel-status").value = app.status;
  $("#panel-notes").value = app.notes || "";
  $("#panel-url").href = app.job.url;
  $("#panel").classList.remove("hidden");
}

function closePanel() {
  $("#panel").classList.add("hidden");
  panelApplicationId = null;
}

async function savePanel() {
  const res = await api.updateApplication(panelApplicationId, {
    status: $("#panel-status").value,
    notes: $("#panel-notes").value || null,
  });
  if (res.ok) {
    toast(t("toast.saved"));
    closePanel();
    renderBoard();
  }
}

async function deleteFromPanel() {
  if (!confirm(t("confirm.delete"))) return;
  const res = await api.deleteApplication(panelApplicationId);
  if (res.ok || res.status === 204) {
    toast(t("toast.deleted"));
    closePanel();
    renderBoard();
  }
}

/* ---------- Job search ---------- */
async function renderJobSearch(event) {
  if (event) event.preventDefault();
  const results = $("#job-results");
  results.innerHTML = `<div class="empty">${t("search.searching")}</div>`;

  const jobs = await api.jobs({
    q: $("#search-q").value,
    source: $("#search-source").value,
    remote: $("#search-remote").checked ? "true" : "",
    limit: "50",
  });

  const trackedJobIds = new Set(applicationsCache.map((a) => a.job.id));
  results.innerHTML = jobs.length === 0 ? `<div class="empty">${t("search.no_results")}</div>` : "";

  for (const job of jobs) {
    const row = document.createElement("div");
    row.className = "job-row";
    const already = trackedJobIds.has(job.id);
    row.innerHTML = `
      <div class="info">
        <h3><a href="${esc(job.url)}" target="_blank" rel="noopener">${esc(job.title)}</a></h3>
        <div class="sub">${esc(job.company)}${job.location ? " — " + esc(job.location) : ""}
          · ${esc(job.source)}${job.remote ? " · remote" : ""}</div>
      </div>
      <button class="btn ${already ? "saved" : ""}" ${already ? "disabled" : ""}>
        ${already ? t("search.saved") : t("search.save")}
      </button>
    `;
    const btn = row.querySelector("button");
    btn.addEventListener("click", async () => {
      const res = await api.createApplication(job.id);
      if (res.ok) {
        btn.textContent = t("search.saved");
        btn.classList.add("saved");
        btn.disabled = true;
        toast(t("toast.added"));
        applicationsCache = await api.applications();
      } else if (res.status === 409) {
        toast(t("toast.already"));
      }
    });
    results.appendChild(row);
  }
}

/* ---------- Wiring ---------- */
document.querySelectorAll("[data-nav]").forEach((btn) =>
  btn.addEventListener("click", () => openAuth(btn.dataset.nav))
);
document.querySelectorAll(".tab").forEach((tab) =>
  tab.addEventListener("click", () => showView(tab.dataset.view))
);
$("#auth-form").addEventListener("submit", submitAuth);
$("#auth-switch-link").addEventListener("click", (e) => {
  e.preventDefault();
  openAuth(authMode === "login" ? "signup" : "login");
});
$("#logout-btn").addEventListener("click", logout);
$("#search-form").addEventListener("submit", renderJobSearch);
$("#panel-close").addEventListener("click", closePanel);
$("#panel-save").addEventListener("click", savePanel);
$("#panel-delete").addEventListener("click", deleteFromPanel);

// Re-render the active board/search when the language changes.
document.addEventListener("langchange", () => {
  if (!$("#view-board").classList.contains("hidden")) renderBoard();
  else if (!$("#view-jobs").classList.contains("hidden")) renderJobSearch();
});

/* ---------- Boot ---------- */
document.querySelectorAll("[data-lang-switch]").forEach(renderLangSwitch);
applyTranslations();
if (getToken()) {
  enterApp();
} else {
  showView("landing");
}
