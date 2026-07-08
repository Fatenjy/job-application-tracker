"use strict";

/* ---------- API client: thin wrappers over our FastAPI endpoints ---------- */
const api = {
  async jobs(params) {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v !== null))
    );
    const res = await fetch(`/jobs?${qs}`);
    return res.json();
  },
  async applications() {
    const res = await fetch("/applications");
    return res.json();
  },
  async createApplication(jobId) {
    return fetch("/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId }),
    });
  },
  async updateApplication(id, data) {
    return fetch(`/applications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  async deleteApplication(id) {
    return fetch(`/applications/${id}`, { method: "DELETE" });
  },
};

const STATUSES = [
  { key: "saved", label: "Saved" },
  { key: "applied", label: "Applied" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "rejected", label: "Rejected" },
];

let applicationsCache = [];
let panelApplicationId = null;

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
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

/* ---------- Board (Kanban) ---------- */
async function renderBoard() {
  applicationsCache = await api.applications();
  const board = $("#board");
  board.innerHTML = "";

  for (const status of STATUSES) {
    const apps = applicationsCache.filter((a) => a.status === status.key);
    const column = document.createElement("div");
    column.className = "column";
    column.dataset.status = status.key;
    column.innerHTML = `
      <div class="column-head">${status.label} <span class="count">${apps.length}</span></div>
      ${apps.length === 0 ? '<div class="empty">Drop a card here</div>' : ""}
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
      card.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", String(app.id));
      });
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
      const newStatus = column.dataset.status;
      const res = await api.updateApplication(id, { status: newStatus });
      if (res.ok) {
        toast(`Moved to ${newStatus}`);
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
    toast("Saved");
    closePanel();
    renderBoard();
  }
}

async function deleteFromPanel() {
  if (!confirm("Stop tracking this application?")) return;
  const res = await api.deleteApplication(panelApplicationId);
  if (res.ok || res.status === 204) {
    toast("Deleted");
    closePanel();
    renderBoard();
  }
}

/* ---------- Job search ---------- */
async function renderJobSearch(event) {
  if (event) event.preventDefault();
  const results = $("#job-results");
  results.innerHTML = '<div class="empty">Searching...</div>';

  const jobs = await api.jobs({
    q: $("#search-q").value,
    source: $("#search-source").value,
    remote: $("#search-remote").checked ? "true" : "",
    limit: "50",
  });

  const trackedJobIds = new Set(applicationsCache.map((a) => a.job.id));
  results.innerHTML = jobs.length === 0 ? '<div class="empty">No jobs match.</div>' : "";

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
        ${already ? "Saved ✓" : "Save"}
      </button>
    `;
    const btn = row.querySelector("button");
    btn.addEventListener("click", async () => {
      const res = await api.createApplication(job.id);
      if (res.ok) {
        btn.textContent = "Saved ✓";
        btn.classList.add("saved");
        btn.disabled = true;
        toast("Added to your board");
        applicationsCache = await api.applications();
      } else if (res.status === 409) {
        toast("Already on your board");
      }
    });
    results.appendChild(row);
  }
}

/* ---------- Tabs ---------- */
function switchView(view) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.view === view)
  );
  $("#view-board").classList.toggle("hidden", view !== "board");
  $("#view-jobs").classList.toggle("hidden", view !== "jobs");
  if (view === "board") renderBoard();
  else renderJobSearch();
}

/* ---------- Wiring ---------- */
document.querySelectorAll(".tab").forEach((tab) =>
  tab.addEventListener("click", () => switchView(tab.dataset.view))
);
$("#search-form").addEventListener("submit", renderJobSearch);
$("#panel-close").addEventListener("click", closePanel);
$("#panel-save").addEventListener("click", savePanel);
$("#panel-delete").addEventListener("click", deleteFromPanel);

renderBoard();
