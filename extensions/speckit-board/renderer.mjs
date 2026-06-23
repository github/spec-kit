// Renderer: HTML for both speckit-board and speckit-feature canvases.
// Uses GitHub canvas theme tokens for native theming.

const STYLES = `
:root {
    color-scheme: light dark;
}
* { box-sizing: border-box; }
html, body {
    margin: 0;
    padding: 0;
    background: var(--background-color-default, #fff);
    color: var(--text-color-default, #1f2328);
    font-family: var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif);
    font-size: var(--text-body-medium, 14px);
    line-height: var(--leading-body-medium, 1.5);
    -webkit-font-smoothing: antialiased;
}
.app {
    padding: 16px;
    max-width: 100%;
}
header.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    gap: 12px;
    flex-wrap: wrap;
}
.title-block { display: flex; align-items: center; gap: 10px; min-width: 0; }
.brand-mark {
    width: 28px; height: 28px;
    border-radius: 6px;
    background: linear-gradient(135deg, var(--b-11-10, #0969da), var(--p-11-10, #8250df));
    display: inline-flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 700; font-size: 13px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08);
    flex-shrink: 0;
}
h1.title {
    font-size: 16px;
    font-weight: var(--font-weight-semibold, 600);
    margin: 0;
    color: var(--text-color-default, #1f2328);
}
.subtitle {
    color: var(--text-color-muted, #59636e);
    font-size: 12px;
    margin: 2px 0 0;
}
.toolbar {
    display: flex;
    gap: 6px;
    align-items: center;
    flex-shrink: 0;
}
button, .btn {
    appearance: none;
    background: var(--background-color-default, #fff);
    color: var(--text-color-default, #1f2328);
    border: 1px solid var(--border-color-default, rgba(31,35,40,0.15));
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-family: inherit;
    cursor: pointer;
    transition: background 0.12s, border-color 0.12s, transform 0.05s;
    font-weight: 500;
    line-height: 18px;
    display: inline-flex; align-items: center; gap: 5px;
}
button:hover:not(:disabled), .btn:hover:not(:disabled) {
    background: var(--n-1-10, rgba(208,215,222,0.32));
}
button:active:not(:disabled) { transform: translateY(0.5px); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:focus-visible, .btn:focus-visible {
    outline: 2px solid var(--color-focus-outline, #0969da);
    outline-offset: 1px;
}
button.primary {
    background: var(--b-11-10, #0969da);
    color: #fff;
    border-color: transparent;
}
button.primary:hover:not(:disabled) {
    background: var(--b-12-10, #0860c7);
}
button.ghost { border-color: transparent; }
button.ghost:hover:not(:disabled) {
    background: var(--n-1-10, rgba(208,215,222,0.32));
}

.constitution-strip {
    background: var(--n-1-10, rgba(208,215,222,0.16));
    border: 1px solid var(--border-color-default, rgba(31,35,40,0.12));
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 16px;
    font-size: 12px;
}
.constitution-strip details summary {
    cursor: pointer;
    font-weight: var(--font-weight-semibold, 600);
    list-style: none;
    display: flex; align-items: center; gap: 6px;
    color: var(--text-color-default, #1f2328);
}
.constitution-strip details summary::before {
    content: "▸";
    transition: transform 0.15s;
    font-size: 10px;
    color: var(--text-color-muted, #59636e);
}
.constitution-strip details[open] summary::before { transform: rotate(90deg); }
.constitution-strip ul {
    margin: 8px 0 0;
    padding-left: 18px;
}
.constitution-strip li { color: var(--text-color-muted, #59636e); margin: 2px 0; }
.constitution-strip li strong { color: var(--text-color-default, #1f2328); font-weight: 600; }
.constitution-missing {
    color: var(--text-color-muted, #59636e);
    font-style: italic;
}

.feature-list {
    display: flex; flex-direction: column; gap: 10px;
}
.feature-card {
    border: 1px solid var(--border-color-default, rgba(31,35,40,0.15));
    border-radius: 8px;
    padding: 12px 14px;
    background: var(--background-color-default, #fff);
    transition: border-color 0.12s, box-shadow 0.12s;
}
.feature-card:hover {
    border-color: var(--border-color-muted, rgba(31,35,40,0.25));
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.feature-card.current {
    border-color: var(--b-11-10, #0969da);
    box-shadow: 0 0 0 1px var(--b-11-10, #0969da);
}
.feature-header {
    display: flex; align-items: center; justify-content: space-between;
    gap: 10px; margin-bottom: 10px;
}
.feature-title { display: flex; align-items: center; gap: 8px; min-width: 0; }
.feature-name {
    font-weight: var(--font-weight-semibold, 600);
    font-size: 13px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.feature-slug {
    color: var(--text-color-muted, #59636e);
    font-family: var(--font-mono, ui-monospace, monospace);
    font-size: 11px;
}
.current-badge {
    background: var(--b-11-10, #0969da);
    color: #fff;
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.pipeline {
    display: flex; align-items: center; gap: 4px;
    margin: 8px 0;
    flex-wrap: wrap;
}
.stage {
    display: inline-flex; align-items: center;
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 500;
    border: 1px solid;
    transition: all 0.12s;
    white-space: nowrap;
}
.stage.done {
    background: var(--g-1-10, rgba(26,127,55,0.10));
    border-color: var(--g-4-10, rgba(26,127,55,0.30));
    color: var(--g-11-10, #1a7f37);
}
.stage.pending {
    background: transparent;
    border-color: var(--border-color-default, rgba(31,35,40,0.15));
    color: var(--text-color-muted, #59636e);
}
.stage.next {
    background: var(--b-1-10, rgba(9,105,218,0.10));
    border-color: var(--b-11-10, #0969da);
    color: var(--b-11-10, #0969da);
    font-weight: 600;
}
.stage-arrow {
    color: var(--text-color-muted, #59636e);
    font-size: 10px;
    opacity: 0.4;
}

.next-action {
    display: flex; gap: 6px; align-items: center;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed var(--border-color-default, rgba(31,35,40,0.10));
}
.next-action-label {
    font-size: 11px;
    color: var(--text-color-muted, #59636e);
    margin-right: 4px;
    flex-shrink: 0;
}
.feature-actions {
    display: flex; gap: 4px; flex-wrap: wrap;
    margin-left: auto;
}

input[type="text"], textarea {
    appearance: none;
    background: var(--background-color-default, #fff);
    color: var(--text-color-default, #1f2328);
    border: 1px solid var(--border-color-default, rgba(31,35,40,0.15));
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    font-family: inherit;
    min-width: 0;
    flex: 1;
}
input[type="text"]:focus, textarea:focus {
    outline: none;
    border-color: var(--b-11-10, #0969da);
    box-shadow: 0 0 0 2px var(--b-1-10, rgba(9,105,218,0.20));
}
.inline-form {
    display: flex; gap: 6px; align-items: center;
    flex: 1;
}

.empty-state {
    text-align: center;
    padding: 32px 16px;
    color: var(--text-color-muted, #59636e);
}
.empty-state h2 {
    font-size: 15px;
    color: var(--text-color-default, #1f2328);
    margin: 0 0 6px;
}
.empty-state p { margin: 4px 0 16px; font-size: 12px; }
.empty-state .empty-actions {
    display: flex; gap: 6px; justify-content: center; flex-wrap: wrap;
}
.empty-state form.inline-form { max-width: 420px; margin: 0 auto; }

.toast {
    position: fixed;
    bottom: 12px;
    right: 12px;
    background: var(--text-color-default, #1f2328);
    color: var(--background-color-default, #fff);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    opacity: 0;
    transform: translateY(4px);
    transition: opacity 0.15s, transform 0.15s;
    pointer-events: none;
    max-width: 320px;
    z-index: 100;
}
.toast.show { opacity: 1; transform: translateY(0); }
.toast.err { background: var(--r-11-10, #cf222e); }

/* Feature canvas */
.feature-meta {
    background: var(--n-1-10, rgba(208,215,222,0.16));
    border: 1px solid var(--border-color-default, rgba(31,35,40,0.12));
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 16px;
}
.section-title {
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 10px;
    font-weight: var(--font-weight-semibold, 600);
    color: var(--text-color-muted, #59636e);
    margin: 18px 0 8px;
}
.file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px;
}
.file-tile {
    border: 1px solid var(--border-color-default, rgba(31,35,40,0.15));
    border-radius: 6px;
    padding: 10px;
    display: flex; flex-direction: column; gap: 6px;
    background: var(--background-color-default, #fff);
    transition: border-color 0.12s, background 0.12s;
}
.file-tile.missing {
    opacity: 0.55;
    border-style: dashed;
}
.file-tile-name {
    font-family: var(--font-mono, ui-monospace, monospace);
    font-size: 11px;
    font-weight: 600;
    color: var(--text-color-default, #1f2328);
    overflow: hidden; text-overflow: ellipsis;
}
.file-tile-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.task-summary {
    display: flex; align-items: center; gap: 8px;
    margin-top: 4px;
    font-size: 11px;
    color: var(--text-color-muted, #59636e);
}
.progress-track {
    flex: 1;
    height: 4px;
    background: var(--n-2-10, rgba(208,215,222,0.5));
    border-radius: 2px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    background: var(--g-11-10, #1a7f37);
    transition: width 0.2s;
}
.back-link {
    color: var(--text-color-muted, #59636e);
    font-size: 12px;
    text-decoration: none;
    display: inline-flex; align-items: center; gap: 4px;
    margin-bottom: 8px;
    cursor: pointer;
}
.back-link:hover { color: var(--text-color-default, #1f2328); }
.scenario-picker {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px 4px 10px;
    border: 1px dashed var(--border-color-default, #d1d9e0);
    border-radius: 6px;
    background: var(--n-1-10, transparent);
    margin-left: 8px;
}
.scenario-picker .scenario-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-color-muted, #59636e);
    font-weight: var(--font-weight-semibold, 600);
}
.scenario-picker select {
    font: inherit;
    font-size: 12px;
    color: var(--text-color-default, #1f2328);
    background: var(--background-color-default, #fff);
    border: 1px solid var(--border-color-default, #d1d9e0);
    border-radius: 4px;
    padding: 2px 6px;
    cursor: pointer;
}
.scenario-picker select:focus {
    outline: 2px solid var(--color-focus-outline, #0969da);
    outline-offset: 1px;
}
.mock-banner {
    background: linear-gradient(90deg, var(--p-11-10, #8250df), var(--b-11-10, #0969da));
    color: #fff;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: var(--font-weight-semibold, 600);
    margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
}
.mock-banner code {
    background: rgba(255,255,255,0.18);
    padding: 1px 6px;
    border-radius: 3px;
    color: #fff;
    font-family: var(--font-mono, ui-monospace, monospace);
    font-size: 11px;
}
`;

const CLIENT_JS = `
const STATE = window.__STATE__;

function toast(msg, isErr) {
    const t = document.createElement("div");
    t.className = "toast" + (isErr ? " err" : "");
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => {
        t.classList.remove("show");
        setTimeout(() => t.remove(), 200);
    }, isErr ? 3200 : 1800);
}

async function postJSON(url, body) {
    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body || {}),
        });
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || "Request failed (" + res.status + ")");
        }
        return await res.json();
    } catch (e) {
        toast(e.message || "Action failed", true);
        throw e;
    }
}

async function sendPrompt(prompt, successMsg) {
    if (!prompt || !prompt.trim()) {
        toast("Prompt is empty", true);
        return;
    }
    await postJSON("/api/send", { prompt });
    toast(successMsg || "Sent to session");
    // Trigger a refresh after a short delay so artifacts show up
    setTimeout(refresh, 1500);
}

async function refresh() {
    location.reload();
}

document.addEventListener("click", async (ev) => {
    const t = ev.target.closest("[data-action]");
    if (!t) return;
    ev.preventDefault();
    const action = t.dataset.action;
    const slug = t.dataset.slug || null;
    const prompt = t.dataset.prompt || null;
    const file = t.dataset.file || null;
    const inputId = t.dataset.input || null;
    const inputEl = inputId ? document.getElementById(inputId) : null;
    const args = inputEl ? inputEl.value.trim() : "";

    if (action === "refresh") return refresh();
    if (action === "open-editor" && file) {
        await postJSON("/api/open-editor", { file });
        toast("Opening in editor…");
        return;
    }
    if (action === "open-feature" && slug) {
        await postJSON("/api/open-feature", { slug });
        toast("Opening feature view…");
        return;
    }
    if (action === "send-prompt" && prompt) {
        const requiresArgs = t.dataset.requiresArgs === "true";
        if (requiresArgs && !args) {
            toast("Type a description first", true);
            inputEl?.focus();
            return;
        }
        const full = args ? prompt + " " + args : prompt;
        await sendPrompt(full, t.dataset.success || "Sent");
        if (inputEl) inputEl.value = "";
        return;
    }
    if (action === "init-project") {
        await sendPrompt("Please run 'specify init --here' and walk me through choosing an AI agent.", "Asked agent");
        return;
    }
});

document.addEventListener("submit", (ev) => {
    const form = ev.target;
    if (form.matches(".inline-form")) {
        ev.preventDefault();
        const btn = form.querySelector("[data-action]");
        if (btn) btn.click();
    }
});

document.addEventListener("change", (ev) => {
    if (ev.target.matches(".scenario-picker select")) {
        const v = ev.target.value;
        const url = new URL(window.location.href);
        if (v) url.searchParams.set("scenario", v);
        else url.searchParams.delete("scenario");
        window.__lastRefresh = Date.now();
        window.location.href = url.toString();
    }
});

window.addEventListener("focus", () => {
    if (window.__lastRefresh && Date.now() - window.__lastRefresh < 800) return;
    window.__lastRefresh = Date.now();
    refresh();
});

document.addEventListener("keydown", (ev) => {
    if ((ev.key === "r" || ev.key === "R") && !ev.target.matches("input,textarea")) {
        refresh();
    }
});
`;

function renderScenarioPicker(scenarios, active) {
    if (!scenarios || scenarios.length === 0) return "";
    const opts = scenarios
        .map((s) => `<option value="${escapeHtml(s.value)}"${s.value === (active || "") ? " selected" : ""}>${escapeHtml(s.label)}</option>`)
        .join("");
    return `<label class="scenario-picker" title="Preview canvas with synthetic data — no project changes">
        <span class="scenario-label">Mock</span>
        <select aria-label="Mock scenario">${opts}</select>
    </label>`;
}

function renderMockBanner(active, scenarios) {
    if (!active) return "";
    const found = (scenarios || []).find((s) => s.value === active);
    const label = found ? found.label : active;
    return `<div class="mock-banner">🎭 Previewing mock scenario: <code>${escapeHtml(label)}</code></div>`;
}

function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[c]));
}

function renderConstitution(constitution) {
    if (!constitution || !constitution.exists) {
        return `<div class="constitution-strip">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                <span class="constitution-missing">No constitution yet — establish project principles first.</span>
                <button class="primary" data-action="send-prompt" data-prompt="/speckit.constitution" data-success="Constitution prompt sent">
                    Draft constitution
                </button>
            </div>
        </div>`;
    }
    const principles = constitution.principles || [];
    if (!principles.length) {
        return `<div class="constitution-strip">
            <details>
                <summary>Constitution</summary>
                <p class="constitution-missing" style="margin:8px 0 0;">Constitution exists but no principles parsed.</p>
            </details>
        </div>`;
    }
    const items = principles
        .map((p) => `<li><strong>${escapeHtml(p.title)}</strong>${p.body ? " — " + escapeHtml(p.body) : ""}</li>`)
        .join("");
    return `<div class="constitution-strip">
        <details>
            <summary>Constitution · ${principles.length} principle${principles.length === 1 ? "" : "s"}</summary>
            <ul>${items}</ul>
        </details>
    </div>`;
}

function renderPipeline(feature) {
    const stages = [
        { id: "specify", label: "Spec", done: feature.stages.specify },
        { id: "clarify", label: "Clarify", done: feature.stages.clarify, optional: true },
        { id: "plan", label: "Plan", done: feature.stages.plan },
        { id: "tasks", label: "Tasks", done: feature.stages.tasks },
        { id: "analyze", label: "Analyze", done: feature.stages.analyze, optional: true },
        { id: "implement", label: "Implement", done: feature.stages.implement, optional: true },
    ];
    const chips = stages
        .map((s, i) => {
            const isNext = feature.next?.stage === s.id;
            const cls = s.done ? "done" : isNext ? "next" : "pending";
            const icon = s.done ? "✓ " : isNext ? "→ " : "";
            const arrow = i < stages.length - 1 ? '<span class="stage-arrow">›</span>' : "";
            return `<span class="stage ${cls}" title="${s.optional ? "optional" : "required"}">${icon}${s.label}</span>${arrow}`;
        })
        .join("");
    return `<div class="pipeline">${chips}</div>`;
}

function renderFeatureCard(feature, isCurrent) {
    const next = feature.next;
    const requiresArgs = next?.requiresArgs;
    const inputId = "input-" + feature.slug;
    const taskBar =
        feature.tasks.total > 0
            ? `<div class="task-summary">
                <span>${feature.tasks.done}/${feature.tasks.total} tasks</span>
                <div class="progress-track"><div class="progress-fill" style="width:${(feature.tasks.done / feature.tasks.total) * 100}%"></div></div>
              </div>`
            : "";

    let actionBlock = "";
    if (requiresArgs) {
        const placeholder =
            next.stage === "specify"
                ? "Describe the feature…"
                : next.stage === "plan"
                ? "Tech stack & architecture context…"
                : "Arguments…";
        actionBlock = `<form class="inline-form">
            <input type="text" id="${inputId}" placeholder="${escapeHtml(placeholder)}" />
            <button class="primary" data-action="send-prompt"
                    data-prompt="${escapeHtml(next.command)}"
                    data-input="${inputId}"
                    data-requires-args="true"
                    data-success="${escapeHtml(next.command + " sent")}">
                ${escapeHtml(next.command)}
            </button>
        </form>`;
    } else {
        actionBlock = `<div class="feature-actions">
            <button class="primary" data-action="send-prompt"
                    data-prompt="${escapeHtml(next.command)}"
                    data-success="${escapeHtml(next.command + " sent")}">
                Next: ${escapeHtml(next.command)}
            </button>
        </div>`;
    }

    return `<div class="feature-card ${isCurrent ? "current" : ""}">
        <div class="feature-header">
            <div class="feature-title">
                <span class="feature-name">${escapeHtml(feature.name)}</span>
                <span class="feature-slug">${escapeHtml(feature.slug)}</span>
                ${isCurrent ? '<span class="current-badge">current branch</span>' : ""}
            </div>
            <div class="toolbar">
                <button class="ghost" data-action="open-feature" data-slug="${escapeHtml(feature.slug)}" title="Open detailed view">
                    Details →
                </button>
            </div>
        </div>
        ${renderPipeline(feature)}
        ${taskBar}
        <div class="next-action">
            <span class="next-action-label">Next:</span>
            ${actionBlock}
        </div>
    </div>`;
}

function renderEmptyStates(state) {
    if (!state.isSpecKit) {
        return `<div class="empty-state">
            <h2>Not a Spec Kit project</h2>
            <p>${escapeHtml(state.reason || "")}</p>
            <div class="empty-actions">
                <button class="primary" data-action="init-project">Initialize with <code>specify init</code></button>
            </div>
        </div>`;
    }
    if (state.features.length === 0) {
        return `<div class="empty-state">
            <h2>No features yet</h2>
            <p>Create your first spec by describing what you want to build.</p>
            <form class="inline-form">
                <input type="text" id="bootstrap-input" placeholder="A dashboard for tracking…" />
                <button class="primary" data-action="send-prompt"
                        data-prompt="/speckit.specify"
                        data-input="bootstrap-input"
                        data-requires-args="true"
                        data-success="/speckit.specify sent">
                    /speckit.specify
                </button>
            </form>
        </div>`;
    }
    return "";
}

export function renderBoard(state, opts = {}) {
    const featureList =
        state.features.length > 0
            ? `<div class="feature-list">${state.features
                  .map((f) => renderFeatureCard(f, f.slug === state.currentFeatureSlug))
                  .join("")}</div>`
            : "";

    const featureCount = state.features.length;
    const branchLabel = state.currentBranch ? `branch: <code>${escapeHtml(state.currentBranch)}</code>` : "";
    const picker = renderScenarioPicker(opts.scenarios, opts.activeScenario);
    const banner = renderMockBanner(opts.activeScenario, opts.scenarios);

    return `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Spec Kit Board</title>
<style>${STYLES}</style>
</head>
<body>
<div class="app">
    <header class="topbar">
        <div class="title-block">
            <span class="brand-mark">SK</span>
            <div>
                <h1 class="title">Spec Kit Board</h1>
                <p class="subtitle">${featureCount} feature${featureCount === 1 ? "" : "s"}${branchLabel ? " · " + branchLabel : ""}</p>
            </div>
        </div>
        <div class="toolbar">
            ${picker}
            <button class="ghost" data-action="refresh" title="Refresh (R)">
                ↻ Refresh
            </button>
        </div>
    </header>
    ${banner}
    ${state.isSpecKit ? renderConstitution(state.constitution) : ""}
    ${state.isSpecKit && state.features.length > 0 ? featureList : ""}
    ${renderEmptyStates(state)}
</div>
<script>window.__STATE__ = ${JSON.stringify({ kind: "board" })};</script>
<script>${CLIENT_JS}</script>
</body>
</html>`;
}

function renderFileTile(label, fileObj, options = {}) {
    const exists = !!fileObj && (fileObj.exists !== false);
    const path = fileObj?.path || "";
    const actions = exists
        ? `<div class="file-tile-actions">
            <button class="ghost" data-action="open-editor" data-file="${escapeHtml(path)}">Open in editor</button>
          </div>`
        : options.createPrompt
        ? `<div class="file-tile-actions">
            <button data-action="send-prompt" data-prompt="${escapeHtml(options.createPrompt)}" data-success="${escapeHtml(options.createPrompt + " sent")}">Create</button>
          </div>`
        : `<div class="file-tile-actions"><span class="constitution-missing">missing</span></div>`;
    return `<div class="file-tile ${exists ? "" : "missing"}">
        <div class="file-tile-name">${escapeHtml(label)}</div>
        ${actions}
    </div>`;
}

export function renderFeatureView(state, feature, opts = {}) {
    const picker = renderScenarioPicker(opts.scenarios, opts.activeScenario);
    const banner = renderMockBanner(opts.activeScenario, opts.scenarios);

    if (!feature) {
        return `<!doctype html><html><head><meta charset="utf-8"/><title>Feature not found</title><style>${STYLES}</style></head>
<body><div class="app">
    <header class="topbar">
        <div class="title-block">
            <span class="brand-mark">SK</span>
            <div>
                <h1 class="title">Spec Kit Feature</h1>
                <p class="subtitle">no feature loaded</p>
            </div>
        </div>
        <div class="toolbar">
            ${picker}
            <button class="ghost" data-action="refresh">↻ Refresh</button>
        </div>
    </header>
    ${banner}
    <div class="empty-state">
        <h2>Feature not found</h2>
        <p>${escapeHtml(opts.requestedSlug ? "Slug '" + opts.requestedSlug + "' doesn't exist in specs/." : "That feature slug doesn't exist in specs/.")}</p>
        <p>Pick a mock scenario above to preview the feature canvas.</p>
    </div>
</div><script>${CLIENT_JS}</script></body></html>`;
    }

    const files = feature.files;
    const taskPct =
        feature.tasks.total > 0
            ? Math.round((feature.tasks.done / feature.tasks.total) * 100)
            : 0;

    return `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>${escapeHtml(feature.name)} · Spec Kit</title>
<style>${STYLES}</style>
</head>
<body>
<div class="app">
    <header class="topbar">
        <div class="title-block">
            <span class="brand-mark">SK</span>
            <div>
                <h1 class="title">${escapeHtml(feature.name)}</h1>
                <p class="subtitle"><code>${escapeHtml(feature.dir)}</code></p>
            </div>
        </div>
        <div class="toolbar">
            ${picker}
            <button class="ghost" data-action="refresh">↻ Refresh</button>
        </div>
    </header>

    ${banner}
    <div class="feature-meta">
        ${renderPipeline(feature)}
        ${feature.tasks.total > 0 ? `<div class="task-summary">
            <span>${feature.tasks.done}/${feature.tasks.total} tasks (${taskPct}%)</span>
            <div class="progress-track"><div class="progress-fill" style="width:${taskPct}%"></div></div>
        </div>` : ""}
    </div>

    <div class="section-title">Next step</div>
    ${(() => {
        const next = feature.next;
        if (!next) return `<p class="constitution-missing">Feature complete.</p>`;
        if (next.requiresArgs) {
            const inputId = "fv-input";
            return `<form class="inline-form">
                <input type="text" id="${inputId}" placeholder="${next.stage === "specify" ? "Describe the feature…" : "Tech context…"}" />
                <button class="primary" data-action="send-prompt"
                        data-prompt="${escapeHtml(next.command)}"
                        data-input="${inputId}"
                        data-requires-args="true"
                        data-success="${escapeHtml(next.command + " sent")}">${escapeHtml(next.command)}</button>
            </form>`;
        }
        return `<button class="primary" data-action="send-prompt"
                    data-prompt="${escapeHtml(next.command)}"
                    data-success="${escapeHtml(next.command + " sent")}">${escapeHtml(next.command)}</button>`;
    })()}

    <div class="section-title">Artifacts</div>
    <div class="file-grid">
        ${renderFileTile("spec.md", files.spec, { createPrompt: "/speckit.specify" })}
        ${renderFileTile("plan.md", files.plan, { createPrompt: "/speckit.plan" })}
        ${renderFileTile("tasks.md", files.tasks, { createPrompt: "/speckit.tasks" })}
        ${files.research ? renderFileTile("research.md", files.research) : ""}
        ${files.dataModel ? renderFileTile("data-model.md", files.dataModel) : ""}
        ${files.quickstart ? renderFileTile("quickstart.md", files.quickstart) : ""}
        ${files.analyze ? renderFileTile(files.analyze.name, files.analyze) : ""}
        ${files.checklists.map((c) => renderFileTile(c.name, c)).join("")}
    </div>

    <div class="section-title">Stage actions</div>
    <div class="feature-actions" style="margin-left:0;">
        <button data-action="send-prompt" data-prompt="/speckit.clarify" data-success="/speckit.clarify sent">/speckit.clarify</button>
        <button data-action="send-prompt" data-prompt="/speckit.checklist" data-success="/speckit.checklist sent">/speckit.checklist</button>
        <button data-action="send-prompt" data-prompt="/speckit.analyze" data-success="/speckit.analyze sent">/speckit.analyze</button>
        <button data-action="send-prompt" data-prompt="/speckit.implement" data-success="/speckit.implement sent">/speckit.implement</button>
    </div>
</div>
<script>window.__STATE__ = ${JSON.stringify({ kind: "feature", slug: feature.slug })};</script>
<script>${CLIENT_JS}</script>
</body>
</html>`;
}
