const board = document.getElementById("board");
const reader = document.getElementById("reader");
const nameEl = document.getElementById("engagement-name");
const progressEl = document.getElementById("progress");

function render(snapshot) {
  nameEl.textContent = snapshot.engagement;
  const { done, total } = snapshot.progress;
  progressEl.textContent = `${done} / ${total} phases complete`;

  board.innerHTML = "";
  for (const phase of snapshot.phases) {
    const card = document.createElement("button");
    card.className = `card status-${phase.status}`;
    card.disabled = phase.status !== "done";
    card.innerHTML =
      `<span class="phase-id">${phase.id}</span>` +
      `<span class="phase-name">${phase.name}</span>` +
      `<span class="badge">${phase.status}</span>` +
      (phase.blocked_reason ? `<span class="reason">${phase.blocked_reason}</span>` : "");
    if (phase.status === "done") {
      card.addEventListener("click", () => openFile(phase));
    }
    board.appendChild(card);
  }

  const gates = document.createElement("div");
  gates.className = "gates";
  for (const gate of snapshot.gates) {
    const g = document.createElement("div");
    g.className = `gate gate-${gate.status}`;
    g.textContent = `${gate.name}: ${gate.status}` + (gate.reason ? ` — ${gate.reason}` : "");
    gates.appendChild(g);
  }
  board.appendChild(gates);
}

async function openFile(phase) {
  reader.innerHTML = `<p class="hint">Loading ${phase.output}…</p>`;
  if (phase.output.endsWith(".html")) {
    reader.innerHTML = `<iframe class="deliverable" src="/api/file-raw?path=${encodeURIComponent(phase.output)}"></iframe>`;
    return;
  }
  const r = await fetch(`/api/file?path=${encodeURIComponent(phase.output)}`);
  if (!r.ok) {
    reader.innerHTML = `<p class="hint">Could not load ${phase.output}.</p>`;
    return;
  }
  const { content } = await r.json();
  const pre = document.createElement("pre");
  pre.className = "markdown";
  pre.textContent = content;
  reader.innerHTML = `<h2>${phase.name} — ${phase.output}</h2>`;
  reader.appendChild(pre);
}

const source = new EventSource("/api/events");
source.onmessage = (e) => render(JSON.parse(e.data));
source.onerror = () => fetch("/api/state").then((r) => r.json()).then(render);
