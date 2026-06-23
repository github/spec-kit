// Scanner: reads a Spec Kit project directory and returns a structured snapshot.
// Pure file-system reads, no caching, no side effects. Safe to call repeatedly.

import { promises as fs } from "node:fs";
import path from "node:path";

const STAGES = [
    { id: "constitution", label: "Constitution", file: null, command: "/speckit.constitution" },
    { id: "specify", label: "Specify", file: "spec.md", command: "/speckit.specify" },
    { id: "clarify", label: "Clarify", file: "spec.md", command: "/speckit.clarify", optional: true, detect: "clarifications" },
    { id: "plan", label: "Plan", file: "plan.md", command: "/speckit.plan" },
    { id: "tasks", label: "Tasks", file: "tasks.md", command: "/speckit.tasks" },
    { id: "analyze", label: "Analyze", file: null, command: "/speckit.analyze", optional: true },
    { id: "implement", label: "Implement", file: null, command: "/speckit.implement", optional: true },
];

async function pathExists(p) {
    try {
        await fs.access(p);
        return true;
    } catch {
        return false;
    }
}

async function readSafe(p) {
    try {
        return await fs.readFile(p, "utf8");
    } catch {
        return null;
    }
}

async function readDirSafe(p) {
    try {
        return await fs.readdir(p, { withFileTypes: true });
    } catch {
        return [];
    }
}

function parseConstitution(text) {
    if (!text) return null;
    const lines = text.split(/\r?\n/);
    const principles = [];
    let currentTitle = null;
    let currentBody = [];

    for (const line of lines) {
        const h2 = line.match(/^##\s+(.+?)\s*$/);
        const h3 = line.match(/^###\s+(.+?)\s*$/);
        if (h2 || h3) {
            if (currentTitle) {
                principles.push({ title: currentTitle, body: currentBody.join(" ").trim().slice(0, 200) });
            }
            currentTitle = (h2 || h3)[1].replace(/^[\*_]+|[\*_]+$/g, "");
            currentBody = [];
        } else if (currentTitle && line.trim() && !line.startsWith("#")) {
            currentBody.push(line.trim());
        }
    }
    if (currentTitle) {
        principles.push({ title: currentTitle, body: currentBody.join(" ").trim().slice(0, 200) });
    }
    return principles
        .filter((p) => !/table of contents|overview|references|governance|amendments/i.test(p.title))
        .slice(0, 8);
}

function parseTaskCounts(text) {
    if (!text) return { total: 0, done: 0 };
    let total = 0;
    let done = 0;
    for (const line of text.split(/\r?\n/)) {
        const m = line.match(/^\s*[-*]\s*\[([ xX])\]/);
        if (m) {
            total++;
            if (m[1].toLowerCase() === "x") done++;
        }
    }
    return { total, done };
}

function hasClarifications(specText) {
    if (!specText) return false;
    return /##\s+Clarifications/i.test(specText) || /\[NEEDS CLARIFICATION/i.test(specText) === false && /Clarifications?:?\s*$/m.test(specText);
}

async function scanFeature(specsDir, entry) {
    const dir = path.join(specsDir, entry);
    const slug = entry;
    const niceName = entry.replace(/^\d+[-_]?/, "").replace(/[-_]+/g, " ").trim() || entry;

    const specPath = path.join(dir, "spec.md");
    const planPath = path.join(dir, "plan.md");
    const tasksPath = path.join(dir, "tasks.md");

    const [specExists, planExists, tasksExists] = await Promise.all([
        pathExists(specPath),
        pathExists(planPath),
        pathExists(tasksPath),
    ]);

    const specText = specExists ? await readSafe(specPath) : null;
    const tasksText = tasksExists ? await readSafe(tasksPath) : null;
    const taskCounts = parseTaskCounts(tasksText);

    const entries = await readDirSafe(dir);
    const checklists = entries
        .filter((e) => e.isFile() && /^checklist[-_]?.*\.md$/i.test(e.name))
        .map((e) => e.name);
    const analyzeReport = entries.find(
        (e) => e.isFile() && /^analyze(-report)?\.md$/i.test(e.name)
    );
    const contractsDir = entries.find((e) => e.isDirectory() && e.name === "contracts");
    const researchFile = entries.find((e) => e.isFile() && e.name === "research.md");
    const dataModelFile = entries.find((e) => e.isFile() && e.name === "data-model.md");
    const quickstartFile = entries.find((e) => e.isFile() && e.name === "quickstart.md");

    const stages = {
        specify: specExists,
        clarify: specExists && hasClarifications(specText),
        plan: planExists,
        tasks: tasksExists,
        analyze: !!analyzeReport,
        implement: taskCounts.total > 0 && taskCounts.done > 0,
    };

    // Determine next legal stage
    let nextStage = null;
    let nextCommand = null;
    let nextRequiresArgs = false;
    if (!specExists) {
        nextStage = "specify";
        nextCommand = "/speckit.specify";
        nextRequiresArgs = true;
    } else if (!planExists) {
        nextStage = "plan";
        nextCommand = "/speckit.plan";
        nextRequiresArgs = true;
    } else if (!tasksExists) {
        nextStage = "tasks";
        nextCommand = "/speckit.tasks";
    } else if (taskCounts.done < taskCounts.total) {
        nextStage = "implement";
        nextCommand = "/speckit.implement";
    } else {
        nextStage = "analyze";
        nextCommand = "/speckit.analyze";
    }

    return {
        slug,
        name: niceName,
        dir: path.relative(path.dirname(specsDir), dir),
        absDir: dir,
        files: {
            spec: specExists ? { path: specPath, exists: true } : { exists: false },
            plan: planExists ? { path: planPath, exists: true } : { exists: false },
            tasks: tasksExists ? { path: tasksPath, exists: true } : { exists: false },
            checklists: checklists.map((name) => ({ name, path: path.join(dir, name) })),
            analyze: analyzeReport ? { name: analyzeReport.name, path: path.join(dir, analyzeReport.name) } : null,
            research: researchFile ? { path: path.join(dir, "research.md") } : null,
            dataModel: dataModelFile ? { path: path.join(dir, "data-model.md") } : null,
            quickstart: quickstartFile ? { path: path.join(dir, "quickstart.md") } : null,
            contracts: contractsDir ? { path: path.join(dir, "contracts") } : null,
        },
        stages,
        tasks: taskCounts,
        next: { stage: nextStage, command: nextCommand, requiresArgs: nextRequiresArgs },
    };
}

async function detectCurrentBranch(cwd) {
    try {
        const headPath = path.join(cwd, ".git", "HEAD");
        const head = await readSafe(headPath);
        if (!head) return null;
        const m = head.match(/^ref:\s+refs\/heads\/(.+)$/m);
        return m ? m[1].trim() : null;
    } catch {
        return null;
    }
}

export async function scanProject(cwd) {
    if (!cwd) {
        return {
            isSpecKit: false,
            cwd: null,
            reason: "No workspace path available",
            constitution: null,
            features: [],
            currentBranch: null,
            currentFeatureSlug: null,
        };
    }

    const specifyDir = path.join(cwd, ".specify");
    const memoryDir = path.join(specifyDir, "memory");
    const constitutionPath = path.join(memoryDir, "constitution.md");
    const specsDir = path.join(cwd, "specs");

    const [hasSpecify, hasSpecs, constitutionExists] = await Promise.all([
        pathExists(specifyDir),
        pathExists(specsDir),
        pathExists(constitutionPath),
    ]);

    if (!hasSpecify && !hasSpecs) {
        return {
            isSpecKit: false,
            cwd,
            reason: "Not a Spec Kit project (no .specify/ or specs/ directory)",
            constitution: null,
            features: [],
            currentBranch: await detectCurrentBranch(cwd),
            currentFeatureSlug: null,
        };
    }

    const constitutionText = constitutionExists ? await readSafe(constitutionPath) : null;
    const constitution = constitutionExists
        ? {
              exists: true,
              path: constitutionPath,
              principles: parseConstitution(constitutionText),
          }
        : { exists: false, path: constitutionPath, principles: [] };

    let features = [];
    if (hasSpecs) {
        const entries = await readDirSafe(specsDir);
        const featureDirs = entries.filter((e) => e.isDirectory() && !e.name.startsWith("."));
        features = await Promise.all(featureDirs.map((d) => scanFeature(specsDir, d.name)));
        features.sort((a, b) => a.slug.localeCompare(b.slug));
    }

    const currentBranch = await detectCurrentBranch(cwd);
    let currentFeatureSlug = null;
    if (currentBranch) {
        // Match branch names like "001-foo" or "feat/001-foo" against feature dirs
        const branchSlug = currentBranch.split("/").pop();
        const match = features.find((f) => f.slug === branchSlug || branchSlug?.startsWith(f.slug));
        if (match) currentFeatureSlug = match.slug;
    }

    return {
        isSpecKit: true,
        cwd,
        constitution,
        features,
        currentBranch,
        currentFeatureSlug,
        stages: STAGES,
    };
}

export { STAGES };
