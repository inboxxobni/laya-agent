// laya-agent web app: vanilla JS talking to the local decision server. No build step, no dependencies.
const API = "";

async function post(path, body) {
  const response = await fetch(API + path, { method: "POST", body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

async function get(path) {
  const response = await fetch(API + path);
  return response.json();
}

// ---------------------------------------------------------------------------------------- nav

document.getElementById("nav").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-view]");
  if (!button) return;
  document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("active", b === button));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${button.dataset.view}`));
});

// -------------------------------------------------------------------------------------- status

async function checkStatus() {
  const el = document.getElementById("status");
  try {
    const health = await get("/health");
    el.textContent = `model: ${health.model}`;
    el.className = "status ok";
  } catch {
    el.textContent = "server unreachable";
    el.className = "status bad";
  }
}
checkStatus();
setInterval(checkStatus, 15000);

// ----------------------------------------------------------------------------------- playground

function barChart(probabilities) {
  const max = Math.max(...Object.values(probabilities));
  return Object.entries(probabilities)
    .sort((a, b) => b[1] - a[1])
    .map(([label, p]) => `
      <div class="bar-row">
        <div class="bar-label">${label}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(p / max) * 100}%"></div></div>
        <div class="bar-value">${p.toFixed(3)}</div>
      </div>`)
    .join("");
}

document.getElementById("pg-mode").addEventListener("change", (event) => {
  const isYesNo = event.target.value === "yesno";
  document.getElementById("pg-options-label").style.display = isYesNo ? "none" : "block";
  document.getElementById("pg-options").style.display = isYesNo ? "none" : "block";
});

document.getElementById("pg-run").addEventListener("click", async () => {
  const state = document.getElementById("pg-state").value;
  const question = document.getElementById("pg-question").value;
  const mode = document.getElementById("pg-mode").value;
  const options = document.getElementById("pg-options").value.split("\n").map((s) => s.trim()).filter(Boolean);
  const box = document.getElementById("pg-result");
  box.style.display = "block";
  box.textContent = "running...";
  try {
    let data, html;
    if (mode === "choice") {
      data = await post("/v1/choice", { state, instructions: question, options });
      html = `<div><strong>${data.choice}</strong> &middot; ${data.latency_ms} ms</div>` + barChart(data.probabilities);
    } else if (mode === "score") {
      data = await post("/v1/score", { state, instructions: question, levels: options });
      html = `<div><strong>${data.level}</strong> (score ${data.score.toFixed(2)}) &middot; ${data.latency_ms} ms</div>` + barChart(data.probabilities);
    } else {
      data = await post("/v1/yesno", { state, proposition: question });
      html = `<div><strong>${data.answer ? "yes" : "no"}</strong> (p_true ${data.p_true.toFixed(3)}) &middot; ${data.latency_ms} ms</div>`;
    }
    box.innerHTML = html;
  } catch (error) {
    box.textContent = `Error: ${error.message}`;
  }
});

// ------------------------------------------------------------------------------------- usecases

let selectedUsecase = null;

async function loadUsecases() {
  const catalog = await get("/v1/usecases");
  const grid = document.getElementById("uc-grid");
  grid.innerHTML = Object.entries(catalog)
    .map(([name, info]) => `
      <div class="usecase-card" data-name="${name}" data-example="${info.example.replace(/"/g, "&quot;")}">
        <div class="group">${info.group}</div>
        <h3>${name}</h3>
        <p>${info.help}</p>
      </div>`)
    .join("");
  grid.querySelectorAll(".usecase-card").forEach((card) => {
    card.addEventListener("click", () => {
      selectedUsecase = card.dataset.name;
      document.getElementById("uc-name").textContent = selectedUsecase;
      document.getElementById("uc-input").value = card.dataset.example;
      document.getElementById("uc-run").disabled = false;
      document.getElementById("uc-result").style.display = "none";
    });
  });
}
loadUsecases().catch(() => {
  document.getElementById("uc-grid").textContent = "Could not load the use-case catalog. Is the server running?";
});

document.getElementById("uc-run").addEventListener("click", async () => {
  if (!selectedUsecase) return;
  const box = document.getElementById("uc-result");
  box.style.display = "block";
  box.textContent = "running...";
  try {
    const data = await post(`/v1/usecase/${selectedUsecase}`, { input: document.getElementById("uc-input").value });
    box.textContent = JSON.stringify(data.result, null, 2);
  } catch (error) {
    box.textContent = `Error: ${error.message}`;
  }
});

// ------------------------------------------------------------------------------------------ chat

let chatHistory = [];

function appendMessage(role, content, route) {
  const log = document.getElementById("chat-log");
  const div = document.createElement("div");
  div.className = `msg ${role}` + (route && route.attack ? " blocked" : "");
  div.textContent = content;
  if (route) {
    const meta = document.createElement("div");
    meta.className = "route";
    meta.textContent = `intent: ${route.intent} · difficulty: ${route.difficulty} · model: ${route.model || "-"}${route.attack ? " · BLOCKED" : ""}`;
    div.appendChild(meta);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  appendMessage("user", message);
  try {
    const data = await post("/v1/chat", { history: chatHistory, message });
    chatHistory = data.history;
    appendMessage("assistant", data.answer, data.route);
  } catch (error) {
    appendMessage("assistant", `Error: ${error.message}`);
  }
}

document.getElementById("chat-send").addEventListener("click", sendChat);
document.getElementById("chat-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter") sendChat();
});
