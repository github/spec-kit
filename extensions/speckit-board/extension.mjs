// speckit-board — Spec-Driven Development dashboard for the Copilot CLI.
//
// Registers two canvases on the same session:
//   - speckit-board    : portfolio view of all features in this Spec Kit project
//   - speckit-feature  : focused drill-in for a single feature
//
// Each open canvas instance gets its own loopback HTTP server. The iframe
// in the canvas talks back to its server with POST /api/* to invoke session
// actions (sending slash commands, opening other canvases, opening files in
// the built-in editor canvas). All canvas → session communication is driven
// by `session.send()` from the SDK.

import { createServer } from "node:http";
import path from "node:path";
import { joinSession, createCanvas, CanvasError } from "@github/copilot-sdk/extension";
import { scanProject } from "./scanner.mjs";
import { renderBoard, renderFeatureView } from "./renderer.mjs";
import {
    getBoardScenario,
    getFeatureScenario,
    BOARD_SCENARIO_NAMES,
    FEATURE_SCENARIO_NAMES,
} from "./mocks.mjs";

// instanceId → { server, url, kind, slug?, cwd }
const servers = new Map();

// Captured after joinSession returns, used by HTTP handlers.
let SESSION = null;

function logSafe(msg) {
    if (SESSION && typeof SESSION.log === "function") {
        try {
            SESSION.log(msg);
        } catch {
            // noop
        }
    }
}

async function readBody(req) {
    return new Promise((resolve, reject) => {
        let data = "";
        req.on("data", (c) => {
            data += c;
            if (data.length > 64 * 1024) reject(new Error("Body too large"));
        });
        req.on("end", () => resolve(data));
        req.on("error", reject);
    });
}

function jsonResponse(res, status, body) {
    res.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(body));
}

function htmlResponse(res, status, body) {
    res.writeHead(status, {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store",
    });
    res.end(body);
}

async function handleBoardRequest(req, res, entry) {
    const url = new URL(req.url, "http://127.0.0.1");
    const scenario = url.searchParams.get("scenario") || "";

    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        const state = scenario ? getBoardScenario(scenario) : await scanProject(entry.cwd);
        if (!state) return htmlResponse(res, 404, `<p>Unknown scenario: ${scenario}</p>`);
        return htmlResponse(res, 200, renderBoard(state, { scenarios: BOARD_SCENARIO_NAMES, activeScenario: scenario }));
    }
    if (req.method === "GET" && url.pathname === "/api/state") {
        const state = scenario ? getBoardScenario(scenario) : await scanProject(entry.cwd);
        if (!state) return jsonResponse(res, 404, { error: "unknown scenario" });
        return jsonResponse(res, 200, state);
    }
    return handleCommonRequest(req, res, entry, url);
}

async function handleFeatureRequest(req, res, entry) {
    const url = new URL(req.url, "http://127.0.0.1");
    const scenario = url.searchParams.get("scenario") || "";

    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
        let state, feature;
        if (scenario) {
            const mock = getFeatureScenario(scenario);
            if (!mock) return htmlResponse(res, 404, `<p>Unknown scenario: ${scenario}</p>`);
            state = mock.wrapper;
            feature = mock.feature;
        } else {
            state = await scanProject(entry.cwd);
            feature = state.features.find((f) => f.slug === entry.slug) || null;
        }
        return htmlResponse(res, 200, renderFeatureView(state, feature, {
            scenarios: FEATURE_SCENARIO_NAMES,
            activeScenario: scenario,
            requestedSlug: entry.slug,
        }));
    }
    return handleCommonRequest(req, res, entry, url);
}

async function handleCommonRequest(req, res, entry, url) {
    if (req.method === "POST" && url.pathname === "/api/send") {
        try {
            const body = JSON.parse(await readBody(req));
            const prompt = String(body.prompt || "").trim();
            if (!prompt) return jsonResponse(res, 400, { error: "prompt required" });
            if (!SESSION) return jsonResponse(res, 500, { error: "session not ready" });
            await SESSION.send({ prompt });
            logSafe(`[speckit-board] sent: ${prompt.slice(0, 100)}`);
            return jsonResponse(res, 200, { ok: true });
        } catch (e) {
            logSafe(`[speckit-board] send failed: ${e.message}`);
            return jsonResponse(res, 500, { error: e.message });
        }
    }

    if (req.method === "POST" && url.pathname === "/api/open-feature") {
        try {
            const body = JSON.parse(await readBody(req));
            const slug = String(body.slug || "").trim();
            if (!slug) return jsonResponse(res, 400, { error: "slug required" });
            const prompt = `Open the "speckit-feature" canvas for the "${slug}" feature (use open_canvas with canvasId "speckit-feature" and input { "slug": "${slug}" }).`;
            await SESSION.send({ prompt });
            return jsonResponse(res, 200, { ok: true });
        } catch (e) {
            return jsonResponse(res, 500, { error: e.message });
        }
    }

    if (req.method === "POST" && url.pathname === "/api/open-editor") {
        try {
            const body = JSON.parse(await readBody(req));
            const file = String(body.file || "").trim();
            if (!file) return jsonResponse(res, 400, { error: "file required" });
            // Ask the agent to open the built-in editor canvas on the file.
            const prompt = `Open the built-in "editor" canvas on the file at \`${file}\` (use open_canvas with canvasId "editor").`;
            await SESSION.send({ prompt });
            return jsonResponse(res, 200, { ok: true });
        } catch (e) {
            return jsonResponse(res, 500, { error: e.message });
        }
    }

    if (req.method === "POST" && url.pathname === "/api/refresh") {
        // Refresh is handled client-side by location.reload() which re-hits GET /.
        return jsonResponse(res, 200, { ok: true });
    }

    return jsonResponse(res, 404, { error: "not found" });
}

async function startServer(kind, instanceId, cwd, slug = null) {
    const server = createServer(async (req, res) => {
        const entry = servers.get(instanceId);
        if (!entry) {
            return jsonResponse(res, 410, { error: "instance gone" });
        }
        try {
            if (kind === "board") return await handleBoardRequest(req, res, entry);
            if (kind === "feature") return await handleFeatureRequest(req, res, entry);
            return jsonResponse(res, 404, { error: "unknown canvas" });
        } catch (e) {
            logSafe(`[speckit-board] handler error: ${e.message}`);
            return jsonResponse(res, 500, { error: e.message });
        }
    });
    await new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", () => resolve());
    });
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : 0;
    return { server, url: `http://127.0.0.1:${port}/`, kind, slug, cwd };
}

function resolveCwd(ctx) {
    return ctx?.session?.workingDirectory || process.cwd();
}

SESSION = await joinSession({
    canvases: [
        createCanvas({
            id: "speckit-board",
            displayName: "Spec Kit Board",
            description:
                "Portfolio dashboard for Spec-Driven Development: every feature, its pipeline stage, and one-click slash-command actions to drive the next step.",
            actions: [
                {
                    name: "refresh",
                    description: "Re-scan the project and refresh the board.",
                    handler: async (ctx) => {
                        const state = await scanProject(resolveCwd(ctx));
                        return { ok: true, featureCount: state.features.length };
                    },
                },
                {
                    name: "open_feature",
                    description:
                        "Identify a feature by slug. The agent should call open_canvas for canvasId 'speckit-feature' with the same slug after this returns.",
                    inputSchema: {
                        type: "object",
                        properties: { slug: { type: "string", description: "Feature directory name under specs/" } },
                        required: ["slug"],
                    },
                    handler: async (ctx) => {
                        const slug = String(ctx.input?.slug || "").trim();
                        if (!slug) throw new CanvasError("invalid_input", "slug is required");
                        return { ok: true, slug, hint: "Now call open_canvas with canvasId 'speckit-feature' and input { slug }." };
                    },
                },
            ],
            open: async (ctx) => {
                const cwd = resolveCwd(ctx);
                let entry = servers.get(ctx.instanceId);
                if (!entry || entry.kind !== "board") {
                    if (entry) await closeEntry(entry, ctx.instanceId);
                    entry = await startServer("board", ctx.instanceId, cwd);
                    servers.set(ctx.instanceId, entry);
                }
                logSafe(`[speckit-board] open board instance=${ctx.instanceId} cwd=${cwd}`);
                return { title: "Spec Kit Board", url: entry.url };
            },
            onClose: async (ctx) => {
                const entry = servers.get(ctx.instanceId);
                if (entry) await closeEntry(entry, ctx.instanceId);
            },
        }),

        createCanvas({
            id: "speckit-feature",
            displayName: "Spec Kit Feature",
            description:
                "Focused drill-in for a single Spec Kit feature: pipeline status, artifact files, stage-specific actions. Open with input { slug }.",
            inputSchema: {
                type: "object",
                properties: {
                    slug: {
                        type: "string",
                        description: "Feature directory name under specs/ (e.g. '001-payments-dashboard').",
                    },
                },
                required: ["slug"],
            },
            actions: [
                {
                    name: "refresh",
                    description: "Re-scan and refresh the feature view.",
                    handler: async (ctx) => {
                        const state = await scanProject(resolveCwd(ctx));
                        const entry = servers.get(ctx.instanceId);
                        const slug = entry?.slug;
                        const feature = state.features.find((f) => f.slug === slug);
                        return { ok: true, slug, found: !!feature };
                    },
                },
                {
                    name: "run_command",
                    description:
                        "Send a Spec Kit slash command to the chat session for the current feature.",
                    inputSchema: {
                        type: "object",
                        properties: {
                            command: { type: "string", description: "Slash command, e.g. '/speckit.plan'" },
                            args: { type: "string", description: "Optional arguments to append" },
                        },
                        required: ["command"],
                    },
                    handler: async (ctx) => {
                        const cmd = String(ctx.input?.command || "").trim();
                        if (!cmd.startsWith("/speckit.")) {
                            throw new CanvasError("invalid_input", "command must be a /speckit.* slash command");
                        }
                        const args = String(ctx.input?.args || "").trim();
                        const prompt = args ? `${cmd} ${args}` : cmd;
                        if (!SESSION) throw new CanvasError("internal", "session not ready");
                        await SESSION.send({ prompt });
                        return { ok: true, sent: prompt };
                    },
                },
            ],
            open: async (ctx) => {
                const cwd = resolveCwd(ctx);
                const slug = String(ctx.input?.slug || "").trim();
                if (!slug) throw new CanvasError("invalid_input", "slug is required in input");
                let entry = servers.get(ctx.instanceId);
                if (!entry || entry.kind !== "feature" || entry.slug !== slug) {
                    if (entry) await closeEntry(entry, ctx.instanceId);
                    entry = await startServer("feature", ctx.instanceId, cwd, slug);
                    servers.set(ctx.instanceId, entry);
                }
                logSafe(`[speckit-board] open feature instance=${ctx.instanceId} slug=${slug}`);
                return { title: `Spec Kit · ${slug}`, url: entry.url };
            },
            onClose: async (ctx) => {
                const entry = servers.get(ctx.instanceId);
                if (entry) await closeEntry(entry, ctx.instanceId);
            },
        }),
    ],
});

async function closeEntry(entry, instanceId) {
    servers.delete(instanceId);
    try {
        await new Promise((resolve) => entry.server.close(() => resolve()));
    } catch {
        // ignore
    }
}

logSafe("[speckit-board] joined session, 2 canvases registered");
