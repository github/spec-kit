// Mock state scenarios for UX previews.
// Each scenario returns the same shape as scanner.mjs `scanProject()`.

import { STAGES } from "./scanner.mjs";

const MOCK_CONSTITUTION = {
    exists: true,
    path: "/mock/.specify/memory/constitution.md",
    principles: [
        { title: "I. User-First", body: "Every change MUST be driven by an observable user outcome with a measurable signal — anchored to a usage metric, not an internal milestone." },
        { title: "II. Test-Backed Change (NON-NEGOTIABLE)", body: "Every behavioral change MUST ship with automated tests and a passing CI gate across the supported matrix." },
        { title: "III. Offline-First Performance", body: "Core flows MUST work offline; cold-start budget is under 250 ms on a mid-tier laptop, measured in CI." },
        { title: "IV. Minimal Dependencies", body: "Zero new runtime deps by default; additions require a written justification in plan.md and an owner." },
        { title: "V. Cross-Platform Parity", body: "Linux, macOS, and Windows ship the same behavior; CI proves it on every PR." },
    ],
};

function emptyFiles(slug) {
    return {
        spec: { exists: false },
        plan: { exists: false },
        tasks: { exists: false },
        checklists: [],
        analyze: null,
        research: null,
        dataModel: null,
        quickstart: null,
        contracts: null,
    };
}

function mockFeature(num, slug, name) {
    return {
        slug,
        name,
        dir: `specs/${slug}`,
        absDir: `/Users/me/projects/launch-pad/specs/${slug}`,
        files: emptyFiles(slug),
        stages: { specify: false, clarify: false, plan: false, tasks: false, analyze: false, implement: false },
        tasks: { total: 0, done: 0 },
        next: { stage: "specify", command: "/speckit.specify", requiresArgs: true },
    };
}

function withSpec(f) {
    f.files.spec = { path: `${f.absDir}/spec.md`, exists: true };
    f.stages.specify = true;
    f.next = { stage: "plan", command: "/speckit.plan", requiresArgs: true };
    return f;
}

function withClarify(f) {
    f.stages.clarify = true;
    return f;
}

function withPlan(f) {
    f.files.plan = { path: `${f.absDir}/plan.md`, exists: true };
    f.files.research = { path: `${f.absDir}/research.md` };
    f.files.dataModel = { path: `${f.absDir}/data-model.md` };
    f.files.contracts = { path: `${f.absDir}/contracts` };
    f.stages.plan = true;
    f.next = { stage: "tasks", command: "/speckit.tasks", requiresArgs: false };
    return f;
}

function withTasks(f, total = 24, done = 0) {
    f.files.tasks = { path: `${f.absDir}/tasks.md`, exists: true };
    f.files.checklists = [
        { name: "checklist-ux.md", path: `${f.absDir}/checklist-ux.md` },
        { name: "checklist-security.md", path: `${f.absDir}/checklist-security.md` },
    ];
    f.stages.tasks = true;
    f.tasks = { total, done };
    if (done > 0) f.stages.implement = true;
    if (done < total) {
        f.next = { stage: "implement", command: "/speckit.implement", requiresArgs: false };
    } else {
        f.next = { stage: "analyze", command: "/speckit.analyze", requiresArgs: false };
    }
    return f;
}

function withAnalyze(f) {
    f.files.analyze = { name: "analyze-report.md", path: `${f.absDir}/analyze-report.md` };
    f.stages.analyze = true;
    return f;
}

// ---------- Board scenarios --------------------------------------------------

const BOARD_SCENARIOS = {
    "not-initialized": () => ({
        isSpecKit: false,
        cwd: "/Users/me/projects/blank-repo",
        constitution: { exists: false, path: null, principles: [] },
        features: [],
        currentBranch: "main",
        currentFeatureSlug: null,
        stages: STAGES,
    }),

    "initialized-empty": () => ({
        isSpecKit: true,
        cwd: "/Users/me/projects/new-spec-kit-project",
        constitution: MOCK_CONSTITUTION,
        features: [],
        currentBranch: "main",
        currentFeatureSlug: null,
        stages: STAGES,
    }),

    "early": () => ({
        isSpecKit: true,
        cwd: "/Users/me/projects/launch-pad",
        constitution: MOCK_CONSTITUTION,
        features: [
            withSpec(mockFeature(1, "001-onboarding-redesign", "Redesign first-run onboarding")),
        ],
        currentBranch: "001-onboarding-redesign",
        currentFeatureSlug: "001-onboarding-redesign",
        stages: STAGES,
    }),

    "mixed": () => {
        const features = [
            withTasks(withPlan(withClarify(withSpec(mockFeature(1, "001-onboarding-redesign", "Redesign first-run onboarding")))), 18, 18),
            withTasks(withPlan(withClarify(withSpec(mockFeature(2, "002-billing-portal", "Self-serve billing portal")))), 24, 11),
            withPlan(withClarify(withSpec(mockFeature(3, "003-auth-refresh", "Rotate refresh tokens silently")))),
            withClarify(withSpec(mockFeature(4, "004-search-rewrite", "Replace ES with hybrid vector search"))),
            withSpec(mockFeature(5, "005-audit-export", "Tenant-scoped audit log export")),
        ];
        return {
            isSpecKit: true,
            cwd: "/Users/me/projects/launch-pad",
            constitution: MOCK_CONSTITUTION,
            features,
            currentBranch: "002-billing-portal",
            currentFeatureSlug: "002-billing-portal",
            stages: STAGES,
        };
    },

    "mature": () => {
        const features = [
            withTasks(withPlan(withClarify(withSpec(mockFeature(1, "001-onboarding-redesign", "Redesign first-run onboarding")))), 18, 18),
            withAnalyze(withTasks(withPlan(withClarify(withSpec(mockFeature(2, "002-billing-portal", "Self-serve billing portal")))), 24, 24)),
            withAnalyze(withTasks(withPlan(withClarify(withSpec(mockFeature(3, "003-auth-refresh", "Rotate refresh tokens silently")))), 16, 12)),
            withTasks(withPlan(withClarify(withSpec(mockFeature(4, "004-search-rewrite", "Replace ES with hybrid vector search")))), 30, 6),
            withPlan(withClarify(withSpec(mockFeature(5, "005-audit-export", "Tenant-scoped audit log export")))),
            withClarify(withSpec(mockFeature(6, "006-mobile-share", "Native iOS/Android share sheet"))),
            withSpec(mockFeature(7, "007-cli-telemetry", "Opt-in CLI usage telemetry")),
        ];
        return {
            isSpecKit: true,
            cwd: "/Users/me/projects/launch-pad",
            constitution: MOCK_CONSTITUTION,
            features,
            currentBranch: "003-auth-refresh",
            currentFeatureSlug: "003-auth-refresh",
            stages: STAGES,
        };
    },
};

// ---------- Feature scenarios ------------------------------------------------

function buildFeatureScenario(builder, slug = "002-billing-portal", name = "Self-serve billing portal") {
    const f = builder(mockFeature(2, slug, name));
    return f;
}

const FEATURE_SCENARIOS = {
    "not-found": () => ({ wrapper: emptyProject(), feature: null }),

    "spec-only": () => {
        const f = buildFeatureScenario((b) => withSpec(b));
        return { wrapper: projectWith(f), feature: f };
    },

    "with-clarify": () => {
        const f = buildFeatureScenario((b) => withClarify(withSpec(b)));
        return { wrapper: projectWith(f), feature: f };
    },

    "planned": () => {
        const f = buildFeatureScenario((b) => withPlan(withClarify(withSpec(b))));
        return { wrapper: projectWith(f), feature: f };
    },

    "tasks-started": () => {
        const f = buildFeatureScenario((b) => withTasks(withPlan(withClarify(withSpec(b))), 24, 8));
        return { wrapper: projectWith(f), feature: f };
    },

    "tasks-done": () => {
        const f = buildFeatureScenario((b) => withTasks(withPlan(withClarify(withSpec(b))), 24, 24));
        return { wrapper: projectWith(f), feature: f };
    },

    "analyzed": () => {
        const f = buildFeatureScenario((b) => withAnalyze(withTasks(withPlan(withClarify(withSpec(b))), 24, 24)));
        return { wrapper: projectWith(f), feature: f };
    },

    "implemented": () => {
        const f = buildFeatureScenario((b) => withAnalyze(withTasks(withPlan(withClarify(withSpec(b))), 24, 24)));
        f.next = { stage: null, command: null, requiresArgs: false };
        return { wrapper: projectWith(f), feature: f };
    },
};

function emptyProject() {
    return {
        isSpecKit: true,
        cwd: "/Users/me/projects/launch-pad",
        constitution: MOCK_CONSTITUTION,
        features: [],
        currentBranch: "main",
        currentFeatureSlug: null,
        stages: STAGES,
    };
}

function projectWith(feature) {
    return {
        isSpecKit: true,
        cwd: "/Users/me/projects/launch-pad",
        constitution: MOCK_CONSTITUTION,
        features: [feature],
        currentBranch: feature.slug,
        currentFeatureSlug: feature.slug,
        stages: STAGES,
    };
}

// ---------- Public API -------------------------------------------------------

export const BOARD_SCENARIO_NAMES = [
    { value: "", label: "Live (real project)" },
    { value: "not-initialized", label: "Mock · Not initialized" },
    { value: "initialized-empty", label: "Mock · Empty project" },
    { value: "early", label: "Mock · 1 feature (spec only)" },
    { value: "mixed", label: "Mock · 5 features (mixed stages)" },
    { value: "mature", label: "Mock · 7 features (mature project)" },
];

export const FEATURE_SCENARIO_NAMES = [
    { value: "", label: "Live (real feature)" },
    { value: "not-found", label: "Mock · Feature not found" },
    { value: "spec-only", label: "Mock · Spec only" },
    { value: "with-clarify", label: "Mock · Spec + clarify" },
    { value: "planned", label: "Mock · Plan complete" },
    { value: "tasks-started", label: "Mock · Tasks 33%" },
    { value: "tasks-done", label: "Mock · Tasks 100%" },
    { value: "analyzed", label: "Mock · Analyzed" },
    { value: "implemented", label: "Mock · Implemented" },
];

export function getBoardScenario(name) {
    const fn = BOARD_SCENARIOS[name];
    if (!fn) return null;
    const state = fn();
    state._mock = name;
    return state;
}

export function getFeatureScenario(name) {
    const fn = FEATURE_SCENARIOS[name];
    if (!fn) return null;
    const { wrapper, feature } = fn();
    wrapper._mock = name;
    return { wrapper, feature };
}
