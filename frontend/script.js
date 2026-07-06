// script.js — talks to the FastAPI /agent endpoint and renders results dynamically.

const API_BASE = ""; // same origin, since FastAPI serves this frontend too

const requestInput = document.getElementById("requestInput");
const generateBtn = document.getElementById("generateBtn");
const btnText = generateBtn.querySelector(".btn-text");
const btnSpinner = generateBtn.querySelector(".btn-spinner");

const statusPanel = document.getElementById("statusPanel");
const statusText = document.getElementById("statusText");

const resultsPanel = document.getElementById("resultsPanel");
const taskListEl = document.getElementById("taskList");
const executionLogEl = document.getElementById("executionLog");
const engineeringNoteEl = document.getElementById("engineeringNote");
const reflectionNoteEl = document.getElementById("reflectionNote");
const docMessageEl = document.getElementById("docMessage");
const downloadLinkEl = document.getElementById("downloadLink");

const errorPanel = document.getElementById("errorPanel");
const errorTextEl = document.getElementById("errorText");

// Quick-fill example chips
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    requestInput.value = chip.dataset.fill;
    requestInput.focus();
  });
});

const STATUS_MESSAGES = [
  "Agent is planning its own task list…",
  "Calling tools for supporting data…",
  "Drafting each section…",
  "Running self-reflection check…",
  "Formatting the final Word document…",
];

let statusInterval = null;

function cycleStatusMessages() {
  let i = 0;
  statusText.textContent = STATUS_MESSAGES[0];
  statusInterval = setInterval(() => {
    i = (i + 1) % STATUS_MESSAGES.length;
    statusText.textContent = STATUS_MESSAGES[i];
  }, 1400);
}

function stopStatusMessages() {
  if (statusInterval) clearInterval(statusInterval);
}

function setLoading(isLoading) {
  generateBtn.disabled = isLoading;
  btnSpinner.hidden = !isLoading;
  btnText.textContent = isLoading ? "Running…" : "Run Agent";
}

function resetPanels() {
  resultsPanel.hidden = true;
  errorPanel.hidden = true;
  taskListEl.innerHTML = "";
  executionLogEl.innerHTML = "";
}

function renderTaskList(tasks) {
  taskListEl.innerHTML = "";
  tasks.forEach((t) => {
    const li = document.createElement("li");
    const badgeClass = t.status === "failed" ? "badge-failed" : "badge-done";
    li.innerHTML = `
      <div class="step-title">
        <span>Step ${t.step_number}: ${escapeHtml(t.title)}</span>
        <span>
          <span class="badge ${badgeClass}">${t.status}</span>
          ${t.tool_used ? `<span class="badge badge-tool">🔧 ${escapeHtml(t.tool_used)}</span>` : ""}
        </span>
      </div>
      <div class="step-desc">${escapeHtml(t.description)}</div>
    `;
    taskListEl.appendChild(li);
  });
}

function renderExecutionLog(logs) {
  executionLogEl.innerHTML = "";
  logs.forEach((r) => {
    const li = document.createElement("li");
    const badgeClass = r.status === "failed" ? "badge-failed" : "badge-done";
    li.innerHTML = `
      <div class="step-title">
        <span>Step ${r.step_number}: ${escapeHtml(r.title)}</span>
        <span class="badge ${badgeClass}">${r.status}</span>
      </div>
      <div class="step-desc">${escapeHtml(r.output)}</div>
    `;
    executionLogEl.appendChild(li);
  });
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function runAgent() {
  const requestText = requestInput.value.trim();
  if (!requestText) {
    requestInput.focus();
    return;
  }

  resetPanels();
  setLoading(true);
  statusPanel.hidden = false;
  cycleStatusMessages();

  try {
    const res = await fetch(`${API_BASE}/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ request: requestText }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Unknown error from agent.");
    }

    renderTaskList(data.task_list || []);
    renderExecutionLog(data.execution_log || []);
    engineeringNoteEl.textContent = data.engineering_note || "";
    reflectionNoteEl.textContent = data.reflection_note || "";
    docMessageEl.textContent = data.message || "Document generated.";
    downloadLinkEl.href = data.download_url || "#";

    resultsPanel.hidden = false;
  } catch (err) {
    errorTextEl.textContent = err.message || String(err);
    errorPanel.hidden = false;
  } finally {
    stopStatusMessages();
    statusPanel.hidden = true;
    setLoading(false);
  }
}

generateBtn.addEventListener("click", runAgent);
requestInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    runAgent();
  }
});
