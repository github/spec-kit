# Changelog

<!-- insert new changelog below this comment -->

## [0.8.7] - 2026-05-07

### Changed

- feat: add agent-orchestrator to community extension catalog (#2236)
- chore: update extension versions in community catalog (#2468)
- fix(goose): Declare args parameter in generated recipes (#2402)
- feat: Add lingma support (#2348)
- docs: Add uv installation guide and inline callouts (#2465)
- Add fx-to-dotnet to community extension catalog (#2471)
- fix: default non-interactive init to copilot integration (#2414)
- fix(forge): use hyphen notation for command refs in Forge integration (#2462)
- feat(catalog): add Cost Tracker (cost) community extension (#2448)
- chore: release 0.8.6, begin 0.8.7.dev0 development (#2463)

## [0.8.6] - 2026-05-06

### Changed

- Load constitution context in `/speckit.implement` to enforce governance during implementation (#2460)
- feat: improve catalog submission templates and CODEOWNERS (#2401)
- fix: validate URL scheme in build_github_request (#2449)
- Add Architecture Guard to community catalog (#2430)
- Add multi-model-review extension to community catalog (#2446)
- Update Ralph Loop to v1.0.2 (#2435)
- Pin GitHub Actions by SHA (#2441)
- fix(workflows): require project for catalog list (#2436)
- Add agent-parity-governance to community catalog (#2382)
- chore: release 0.8.5, begin 0.8.6.dev0 development (#2447)

## [0.8.5] - 2026-05-04

### Changed

- feat(presets): add Spec2Cloud preset for Azure deployment workflow (#2413)
- update security-review and memory-md extensions to latest versions (#2445)
- fix: honor template overrides for tasks-template (#2278) (#2292)
- Add token-analyzer to community catalog (#2433)
- docs: add April 2026 newsletter (#2434)
- feat: emit init-time notice for git extension default change (#2165) (#2432)
- Update DyanGalih(Memory Hub and Security Review) community extensions (#2429)
- Support controlled multi-install for safe AI agent integrations (#2389)
- chore(integrations): clean up docs and project guard (#2428)
- chore: release 0.8.4, begin 0.8.5.dev0 development (#2431)

## [0.8.4] - 2026-05-01

### Changed

- fix(specify): correct self-referencing step number in validation flow (#2152)
- chore(deps): bump DavidAnson/markdownlint-cli2-action (#2425)
- Add security-governance to community catalog (#2386)
- Add cross-platform-governance to community catalog (#2384)
- Add architecture-governance to community catalog (#2383)
- Add a11y-governance to community catalog (#2381)
- feat(extensions): add Spec2Cloud extension for Azure deployment workflow (#2412)
- fix: migrate extension commands on integration switch (#2404)
- feat: add Squad Bridge extension to community catalog (#2417)
- chore: release 0.8.3, begin 0.8.4.dev0 development (#2418)

## [0.8.3] - 2026-04-29

### Changed

- Add Work IQ extension to community catalog (#2415)
- feat(integrations): add Devin for Terminal skills-based integration (#2364)
- fix: include --from git+... in upgrade hint to avoid PyPI squat package (#2411)
- fix: dispatch opencode commands via run (#2410)
- feat: add catalog discovery CLI commands (#2360)
- update security review extension catalog to v1.3.0 (#2374)
- chore(catalog): bump v-model extension to v0.6.0 (#2399)
- feat: add threatmodel extension to community catalog (#2369)
- Add isaqb-architecture-governance to community catalog (#2385)
- chore: release 0.8.2, begin 0.8.3.dev0 development (#2397)

## [0.8.2] - 2026-04-28

### Changed

- Add MarkItDown Document Converter extension to community catalog (#2390)
- feat: Speckit preset fiction book v1.7 - Support for RAG (Chroma DB) offline semantic search (#2367)
- fix(extensions): use explicit UTF-8 encoding when reading manifest YAML (#2370)
- catalog: add m365 community extension
- docs: replace deprecated --ai flag with --integration in all documentation (#2359)
- feat(extensions,presets): authenticate GitHub-hosted catalog and download requests with GITHUB_TOKEN/GH_TOKEN (#2331)
- Update extensify to v1.1.0 in community catalog (#2337)
- feat(init): deprecate --no-git flag, gate deprecations at v0.10.0 (#2357)
- Add Spec Orchestrator extension to community catalog (#2350)
- chore: release 0.8.1, begin 0.8.2.dev0 development (#2356)

## [0.8.1] - 2026-04-24

### Changed

- fix(plan): use .specify/feature.json to allow /speckit.plan on custom git branches (#2305) (#2349)
- feat(vibe): migrate to SkillsIntegration from the old prompts-based MarkdownIntegration (#2336)
- docs: move community presets table to docs site, add missing entries (#2341)
- docs(presets): add lean preset README and enrich catalog metadata (#2340)
- fix: resolve command references per integration type (dot vs hyphen) (#2354)
- Update product-forge to v1.5.1 in community catalog (#2352)
- chore(deps): bump astral-sh/setup-uv from 8.0.0 to 8.1.0 (#2345)
- fix: replace xargs trim with sed to handle quotes in descriptions (#2351)
- feat: register jira preset in community catalog (#2224)
- feat: Preset screenwriting (#2332)
- chore: release 0.8.0, begin 0.8.1.dev0 development (#2333)

## [0.8.0] - 2026-04-23

### Changed

- feat(presets): Composition strategies (prepend, append, wrap) for templates, commands, and scripts (#2133)
- feat(copilot): support `--integration-options="--skills"` for skills-based scaffolding (#2324)
- docs(install): add pipx as alternative installation method (#2288)
- Add Memory MD community extension (#2327)
- Update version-guard to v1.2.0 (#2321)
- fix: `--force` now overwrites shared infra files during init and upgrade (#2320)
- chore: release 0.7.5, begin 0.7.6.dev0 development (#2322)

## [0.7.5] - 2026-04-22

### Changed

- fix: resolve skill placeholders for all SKILL.md agents, not just codex/kimi (#2313)
- feat(cli): add specify self check and self upgrade stub (#2316)
- Update version-guard to v1.1.0 (#2318)
- docs: move community presets from README to docs/community (#2314)
- catalog: add wireframe extension (v0.1.1) (#2262)
- Move community walkthroughs from README to docs/community (#2312)
- docs(readme): list red-team in community-extensions table (#2311)
- feat(catalog): add red-team extension to community catalog (#2306)
- Add superpowers-bridge community extension (#2309)
- feat: implement preset wrap strategy (#2189)
- fix(agents): block directory traversal in command write paths (#2229) (#2296)
- chore: release 0.7.4, begin 0.7.5.dev0 development (#2299)

## [0.7.4] - 2026-04-21

### Changed

- fix(copilot): use --yolo to grant all permissions in non-interactive mode (#2298)
- feat: add CITATION.cff and .zenodo.json for academic citation support (#2291)
- Add spec-validate to community catalog (#2274)
- feat: register Ripple in community catalog (#2272)
- Add version-guard to community catalog (#2286)
- Add spec-reference-loader to community catalog (#2285)
- Add memory-loader to community catalog (#2284)
- fix(integrations): strip UTF-8 BOM when reading agent context files (#2283)
- Preset fiction book writing1.6 (#2270)
- fix(integrations): migrate Antigravity (agy) layout to .agents/ and deprecate --skills (#2276)
- chore: release 0.7.3, begin 0.7.4.dev0 development (#2263)

## [0.7.3] - 2026-04-17

### Changed

- fix: replace shell-based context updates with marker-based upsert (#2259)
- Add Community Friends page to docs site (#2261)
- Add Spec Scope extension to community catalog (#2172)
- docs: add Community-maintained plugin for Claude Code and GitHub Copilot CLI that installs Spec Kit skills via the plugin marketplace to README (#2250)
- fix: suppress CRLF warnings in auto-commit.ps1 (#2258)
- feat: register Blueprint in community catalog (#2252)
- preset: Update preset-fiction-book-writing to community catalog -> v1.5.0 (#2256)
- chore(deps): bump actions/upload-pages-artifact from 3 to 5 (#2251)
- fix: add reference/*.md to docfx content glob (#2248)
- chore: release 0.7.2, begin 0.7.3.dev0 development (#2247)

## [0.7.2] - 2026-04-16

### Changed

- docs: add core commands reference and simplify README CLI section (#2245)
- docs: add workflows reference, reorganize into docs/reference/, and add --version flag (#2244)
- docs: add presets reference page and rename pack_id to preset_id (#2243)
- docs: add extensions reference page and integrations FAQ (#2242)
- docs: consolidate integration documentation into docs/integrations.md (#2241)
- feat: update memorylint and superpowers-bridge versions to 1.3.0 with new download URLs (#2240)
- feat: Integration catalog — discovery, versioning, and community distribution (#2130)
- Add Catalog CI extension to community catalog (#2239)
- Added issues extension (#2194)
- chore: release 0.7.1, begin 0.7.2.dev0 development (#2235)

## [0.7.1] - 2026-04-15

### Changed

- ci: add windows-latest to test matrix (#2233)
- docs: remove deprecated --skip-tls references from local-development guide (#2231)
- fix: allow Claude to chain skills for hook execution (#2227)
- docs: merge TESTING.md into CONTRIBUTING.md, remove TESTING.md (#2228)
- Add agent-assign extension to community catalog (#2030)
- fix: unofficial PyPI warning (#1982) and legacy extension command name auto-correction (#2017) (#2027)
- feat: register architect-preview in community catalog (#2214)
- chore: deprecate --ai flag in favor of --integration on specify init (#2218)
- chore: release 0.7.0, begin 0.7.1.dev0 development (#2217)

## [0.7.0] - 2026-04-14

### Changed

- Add workflow engine with catalog system (#2158)
- docs(catalog): add claude-ask-questions to community preset catalog (#2191)
- Add SFSpeckit — Salesforce SDD Extension (#2208)
- feat(scripts): optional single-segment branch prefix for gitflow (#2202)
- chore: release 0.6.2, begin 0.6.3.dev0 development (#2205)
- Add Worktrees extension to community catalog (#2207)
- feat: Update catalog.community.json for preset-fiction-book-writing (#2199)

## [0.6.2] - 2026-04-13

### Changed

- feat: Register "What-if Analysis" community extension (#2182)
- feat: add GitHub Issues Integration to community catalog (#2188)
- feat(agents): add Goose AI agent support (#2015)
- Update ralph extension to v1.0.1 in community catalog (#2192)
- fix: skip docs deployment workflow on forks (#2171)
- chore: release 0.6.1, begin 0.6.2.dev0 development (#2162)

## [0.6.1] - 2026-04-10

### Changed

- feat: add bundled lean preset with minimal workflow commands (#2161)
- Add Brownfield Bootstrap extension to community catalog (#2145)
- Add CI Guard extension to community catalog (#2157)
- Add SpecTest extension to community catalog (#2159)
- fix: bundled extensions should not have download URLs (#2155)
- Add PR Bridge extension to community catalog (#2148)
- feat(cursor-agent): migrate from .cursor/commands to .cursor/skills (#2156)
- Add TinySpec extension to community catalog (#2147)
- chore: bump spec-kit-verify to 1.0.3 and spec-kit-review to 1.0.1 (#2146)
- Add Status Report extension to community catalog (#2123)
- chore: release 0.6.0, begin 0.6.1.dev0 development (#2144)

## [0.6.0] - 2026-04-09

### Changed

- Add Bugfix Workflow community extension to catalog and README (#2135)
- Add Worktree Isolation extension to community catalog (#2143)
- Add multi-repo-branching preset to community catalog (#2139)
- Readme clarity (#2013)
- Rewrite AGENTS.md for integration architecture (#2119)
- docs: add SpecKit Companion to Community Friends section (#2140)
- feat: add memorylint extension to community catalog (#2138)
- chore: release 0.5.1, begin 0.5.2.dev0 development (#2137)

## [0.5.1] - 2026-04-08

### Changed

- fix: pin typer>=0.24.0 and click>=8.2.1 to fix import crash (#2136)
- feat: update fleet extension to v1.1.0 (#2029)
- fix(forge): use hyphen notation in frontmatter name field (#2075)
- fix(bash): sed replacement escaping, BSD portability, dead cleanup in update-agent-context.sh (#2090)
- Add Spec Diagram community extension to catalog and README (#2129)
- feat: Git extension stage 2 — GIT_BRANCH_NAME override, --force for existing dirs, auto-install tests (#1940) (#2117)
- fix(git): surface checkout errors for existing branches (#2122)
- Add Branch Convention community extension to catalog and README (#2128)
- docs: lighten March 2026 newsletter for readability (#2127)
- fix: restore alias compatibility for community extensions (#2110) (#2125)
- Added March 2026 newsletter (#2124)
- Add Spec Refine community extension to catalog and README (#2118)
- Add explicit-task-dependencies community preset to catalog and README (#2091)
- Add toc-navigation community preset to catalog and README (#2080)
- fix: prevent ambiguous TOML closing quotes when body ends with `"` (#2113) (#2115)
- fix speckit issue for trae (#2112)
- feat: Git extension stage 1 — bundled `extensions/git` with hooks on all core commands (#1941)
- Upgraded confluence extension to v.1.1.1 (#2109)
- Update V-Model Extension Pack to v0.5.0 (#2108)
- Add canon extension and canon-core preset. (#2022)
- [stage2] fix: serialize multiline descriptions in legacy TOML renderer (#2097)
- [stage1] fix: strip YAML frontmatter from TOML integration prompts (#2096)
- Add Confluence extension (#2028)
- fix: accept 4+ digit spec numbers in tests and docs (#2094)
- fix(scripts): improve git branch creation error handling (#2089)
- Add optimize extension to community catalog (#2088)
- feat: add "VS Code Ask Questions" preset (#2086)
- Add security-review v1.1.1 to community extensions catalog (#2073)
- Add `specify integration` subcommand for post-init integration management (#2083)
- Remove template version info from CLI, fix Claude user-invocable, cleanup dead code (#2081)
- fix: add user-invocable: true to skill frontmatter (#2077)
- fix: add actions:write permission to stale workflow (#2079)
- feat: add argument-hint frontmatter to Claude Code commands (#1951) (#2059)
- Update conduct extension to v1.0.1 (#2078)
- chore(deps): bump astral-sh/setup-uv from 7.6.0 to 8.0.0 (#2072)
- chore(deps): bump actions/configure-pages from 5 to 6 (#2071)
- feat: add spec-kit-fixit extension to community catalog (#2024)
- chore: release 0.5.0, begin 0.5.1.dev0 development (#2070)
- feat: add Forgecode agent support (#2034)

## [0.5.0] - 2026-04-02

### Changed

- Introduces DEVELOPMENT.md (#2069)
- Update cc-sdd reference to cc-spex in Community Friends (#2007)
- chore: release 0.4.5, begin 0.4.6.dev0 development (#2064)

## [0.4.5] - 2026-04-02

### Changed

- Stage 6: Complete migration — remove legacy scaffold path (#1924) (#2063)
- Install Claude Code as native skills and align preset/integration flows (#2051)
- Add repoindex 0402 (#2062)
- Stage 5: Skills, Generic & Option-Driven Integrations (#1924) (#2052)
- feat(scripts): add --dry-run flag to create-new-feature (#1998)
- fix: support feature branch numbers with 4+ digits (#2040)
- Add community content disclaimers (#2058)
- docs: add community extensions website link to README and extensions docs (#2014)
- docs: remove dead Cognitive Squad and Understanding extension links and from extensions/catalog.community.json (#2057)
- Add fix-findings extension to community catalog (#2039)
- Stage 4: TOML integrations — gemini and tabnine migrated to plugin architecture (#2050)
- feat: add 5 lifecycle extensions to community catalog (#2049)
- Stage 3: Standard markdown integrations — 19 agents migrated to plugin architecture (#2038)
- chore: release 0.4.4, begin 0.4.5.dev0 development (#2048)

## [0.4.4] - 2026-04-01

### Changed

- Stage 2: Copilot integration — proof of concept with shared template primitives (#2035)
- docs: sync AGENTS.md with AGENT_CONFIG for missing agents (#2025)
- docs: ensure manual tests use local specify (#2020)
- Stage 1: Integration foundation — base classes, manifest system, and registry (#1925)
- fix: harden GitHub Actions workflows (#2021)
- chore: use PEP 440 .dev0 versions on main after releases (#2032)
- feat: add superpowers bridge extension to community catalog (#2023)
- feat: add product-forge extension to community catalog (#2012)
- feat(scripts): add --allow-existing-branch flag to create-new-feature (#1999)
- fix(scripts): add correct path for copilot-instructions.md (#1997)
- Update README.md (#1995)
- fix: prevent extension command shadowing (#1994)
- Fix Claude Code CLI detection for npm-local installs (#1978)
- fix(scripts): honor PowerShell agent and script filters (#1969)
- feat: add MAQA extension suite (7 extensions) to community catalog (#1981)
- feat: add spec-kit-onboard extension to community catalog (#1991)
- Add plan-review-gate to community catalog (#1993)
- chore(deps): bump actions/deploy-pages from 4 to 5 (#1990)
- chore(deps): bump DavidAnson/markdownlint-cli2-action from 19 to 23 (#1989)
- chore: bump version to 0.4.3 (#1986)

## [0.4.3] - 2026-03-26

### Changed

- Unify Kimi/Codex skill naming and migrate legacy dotted Kimi dirs (#1971)
- fix(ps1): replace null-conditional operator for PowerShell 5.1 compatibility (#1975)
- chore: bump version to 0.4.2 (#1973)

## [0.4.2] - 2026-03-25

### Changed

- feat: Auto-register ai-skills for extensions whenever applicable (#1840)
- docs: add manual testing guide for slash command validation (#1955)
- Add AIDE, Extensify, and Presetify to community extensions (#1961)
- docs: add community presets section to main README (#1960)
- docs: move community extensions table to main README for discoverability (#1959)
- docs(readme): consolidate Community Friends sections and fix ToC anchors (#1958)
- fix(commands): rename NFR references to success criteria in analyze and clarify (#1935)
- Add Community Friends section to README (#1956)
- docs: add Community Friends section with Spec Kit Assistant VS Code extension (#1944)

## [0.4.1] - 2026-03-24

### Changed

- Add checkpoint extension (#1947)
- fix(scripts): prioritize .specify over git for repo root detection (#1933)
- docs: add AIDE extension demo to community projects (#1943)
- fix(templates): add missing Assumptions section to spec template (#1939)

## [0.4.0] - 2026-03-23

### Changed

- fix(cli): add allow_unicode=True and encoding="utf-8" to YAML I/O (#1936)
- fix(codex): native skills fallback refresh + legacy prompt suppression (#1930)
- feat(cli): embed core pack in wheel for offline/air-gapped deployment (#1803)
- ci: increase stale workflow operations-per-run to 250 (#1922)
- docs: update publishing guide with Category and Effect columns (#1913)
- fix: Align native skills frontmatter with install_ai_skills (#1920)
- feat: add timestamp-based branch naming option for `specify init` (#1911)
- docs: add Extension Comparison Guide for community extensions (#1897)
- docs: update SUPPORT.md, fix issue templates, add preset submission template (#1910)
- Add support for Junie (#1831)
- feat: migrate Codex/agy init to native skills workflow (#1906)

## [0.3.2] - 2026-03-19

### Changed

- Add conduct extension to community catalog (#1908)
- feat(extensions): add verify-tasks extension to community catalog (#1871)
- feat(presets): add enable/disable toggle and update semantics (#1891)
- feat: add iFlow CLI support (#1875)
- feat(commands): wire before/after hook events into specify and plan templates (#1886)
- docs(catalog): add speckit-utils to community catalog (#1896)
- docs: Add Extensions & Presets section to README (#1898)
- chore: update DocGuard extension to v0.9.11 (#1899)
- Update cognitive-squad catalog entry — Triadic Model, full lifecycle (#1884)
- feat: register spec-kit-iterate extension (#1887)
- fix(scripts): add explicit positional binding to PowerShell create-new-feature params (#1885)
- fix(scripts): encode residual JSON control chars as \uXXXX instead of stripping (#1872)
- chore: update DocGuard extension to v0.9.10 (#1890)
- Feature/spec kit add pi coding agent pullrequest (#1853)
- feat: register spec-kit-learn extension (#1883)

## [0.3.1] - 2026-03-17

### Changed

- docs: add greenfield Spring Boot pirate-speak preset demo to README (#1878)
- fix(ai-skills): exclude non-speckit copilot agent markdown from skills (#1867)
- feat: add Trae IDE support as a new agent (#1817)
- feat(cli): polite deep merge for settings.json and support JSONC (#1874)
- feat(extensions,presets): add priority-based resolution ordering (#1855)
- fix(scripts): suppress stdout from git fetch in create-new-feature.sh (#1876)
- fix(scripts): harden bash scripts — escape, compat, and error handling (#1869)
- Add cognitive-squad to community extension catalog (#1870)
- docs: add Go / React brownfield walkthrough to community walkthroughs (#1868)
- chore: update DocGuard extension to v0.9.8 (#1859)
- Feature: add specify status command (#1837)
- fix(extensions): show extension ID in list output (#1843)
- feat(extensions): add Archive and Reconcile extensions to community catalog (#1844)
- feat: Add DocGuard CDD enforcement extension to community catalog (#1838)

## [0.3.0] - 2026-03-13

### Changed

- feat(presets): Pluggable preset system with catalog, resolver, and skills propagation (#1787)
- fix: match 'Last updated' timestamp with or without bold markers (#1836)
- Add specify doctor command for project health diagnostics (#1828)
- fix: harden bash scripts against shell injection and improve robustness (#1809)
- fix: clean up command templates (specify, analyze) (#1810)
- fix: migrate Qwen Code CLI from TOML to Markdown format (#1589) (#1730)
- fix(cli): deprecate explicit command support for agy (#1798) (#1808)
- Add /selftest.extension core extension to test other extensions (#1758)
- feat(extensions): Quality of life improvements for RFC-aligned catalog integration (#1776)
- Add Java brownfield walkthrough to community walkthroughs (#1820)

## [0.2.1] - 2026-03-11

### Changed

- Added February 2026 newsletter (#1812)
- feat: add Kimi Code CLI agent support (#1790)
- docs: fix broken links in quickstart guide (#1759) (#1797)
- docs: add catalog cli help documentation (#1793) (#1794)
- fix: use quiet checkout to avoid exception on git checkout (#1792)
- feat(extensions): support .extensionignore to exclude files during install (#1781)
- feat: add Codex support for extension command registration (#1767)

## [0.2.0] - 2026-03-09

### Changed

- fix: sync agent list comments with actual supported agents (#1785)
- feat(extensions): support multiple active catalogs simultaneously (#1720)
- Pavel/add tabnine cli support (#1503)
- Add Understanding extension to community catalog (#1778)
- Add ralph extension to community catalog (#1780)
- Update README with project initialization instructions (#1772)
- feat: add review extension to community catalog (#1775)
- Add fleet extension to community catalog (#1771)
- Integration of Mistral vibe support into speckit (#1725)
- fix: Remove duplicate options in specify.md (#1765)
- fix: use global branch numbering instead of per-short-name detection (#1757)
- Add Community Walkthroughs section to README (#1766)
- feat(extensions): add Jira Integration to community catalog (#1764)
- Add Azure DevOps Integration extension to community catalog (#1734)
- Fix docs: update Antigravity link and add initialization example (#1748)
- fix: wire after_tasks and after_implement hook events into command templates (#1702)
- make c ignores consistent with c++ (#1747)

## [0.1.13] - 2026-03-03

### Changed

- feat: add kiro-cli and AGENT_CONFIG consistency coverage (#1690)
- feat: add verify extension to community catalog (#1726)
- Add Retrospective Extension to community catalog README table (#1741)
- fix(scripts): add empty description validation and branch checkout error handling (#1559)
- fix: correct Copilot extension command registration (#1724)
- fix(implement): remove Makefile from C ignore patterns (#1558)
- Add sync extension to community catalog (#1728)
- fix(checklist): clarify file handling behavior for append vs create (#1556)
- fix(clarify): correct conflicting question limit from 10 to 5 (#1557)

## [0.1.12] - 2026-03-02

### Changed

- fix: use RELEASE_PAT so tag push triggers release workflow (#1736)

## [0.1.11] - 2026-03-02

### Changed

- fix: release-trigger uses release branch + PR instead of direct push to main (#1733)
- fix: Split release process to sync pyproject.toml version with git tags (#1732)

## [0.1.10] - 2026-02-27

### Changed

- fix: prepend YAML frontmatter to Cursor .mdc files (#1699)

## [0.1.9] - 2026-02-28

### Changed

- chore(deps): bump astral-sh/setup-uv from 6 to 7 (#1709)

## [0.1.8] - 2026-02-28

### Changed

- chore(deps): bump actions/setup-python from 5 to 6 (#1710)

## [0.1.7] - 2026-02-27

### Changed

- chore: Update outdated GitHub Actions versions (#1706)
- docs: Document dual-catalog system for extensions (#1689)
- Fix version command in documentation (#1685)
- Add Cleanup Extension to README (#1678)
- Add retrospective extension to community catalog (#1681)

## [0.1.6] - 2026-02-23

### Changed

- Add Cleanup Extension to catalog (#1617)
- Fix parameter ordering issues in CLI (#1669)
- Update V-Model Extension Pack to v0.4.0 (#1665)
- docs: Fix doc missing step (#1496)
- Update V-Model Extension Pack to v0.3.0 (#1661)

## [0.1.5] - 2026-02-21

### Changed

- Fix #1658: Add commands_subdir field to support non-standard agent directory structures (#1660)
- feat: add GitHub issue templates (#1655)
- Update V-Model Extension Pack to v0.2.0 in community catalog (#1656)
- Add V-Model Extension Pack to catalog (#1640)
- refactor: remove OpenAPI/GraphQL bias from templates (#1652)

## [0.1.4] - 2026-02-20

### Changed

- fix: rename Qoder AGENT_CONFIG key from 'qoder' to 'qodercli' to match actual CLI executable (#1651)

## [0.1.3] - 2026-02-20

### Changed

- Add generic agent support with customizable command directories (#1639)

## [0.1.2] - 2026-02-20

### Changed

- fix: pin click>=8.1 to prevent Python 3.14/Homebrew env isolation crash (#1648)

## [0.0.102] - 2026-02-20

### Changed

- fix: include 'src/**' path in release workflow triggers (#1646)

## [0.0.101] - 2026-02-19

### Changed

- chore(deps): bump github/codeql-action from 3 to 4 (#1635)

## [0.0.100] - 2026-02-19

### Changed

- Add pytest and Python linting (ruff) to CI (#1637)
- feat: add pull request template for better contribution guidelines (#1634)

## [0.0.99] - 2026-02-19

### Changed

- Feat/ai skills (#1632)

## [0.0.98] - 2026-02-19

### Changed

- chore(deps): bump actions/stale from 9 to 10 (#1623)
- feat: add dependabot configuration for pip and GitHub Actions updates (#1622)

## [0.0.97] - 2026-02-18

### Changed

- Remove Maintainers section from README.md (#1618)

## [0.0.96] - 2026-02-17

### Changed

- fix: typo in plan-template.md (#1446)

## [0.0.95] - 2026-02-12

### Changed

- Feat: add a new agent: Google Anti Gravity (#1220)

## [0.0.94] - 2026-02-11

### Changed

- Add stale workflow for 180-day inactive issues and PRs (#1594)

## [0.0.93] - 2026-02-10

### Changed

- Add modular extension system (#1551)

## [0.0.92] - 2026-02-10

### Changed

- Fixes #1586 - .specify.specify path error (#1588)

## [0.0.91] - 2026-02-09

### Changed

- fix: preserve constitution.md during reinitialization (#1541) (#1553)
- fix: resolve markdownlint errors across documentation (#1571)

## [0.0.90] - 2025-12-04

### Changed

- Update Markdown formatting
- Update Markdown formatting
- docs: Add existing project initialization to getting started

## [0.0.89] - 2025-12-02

### Changed

- Update scripts/bash/create-new-feature.sh
- fix(scripts): prevent octal interpretation in feature number parsing
- fix: remove unused short_name parameter from branch numbering functions
- Update scripts/powershell/create-new-feature.ps1
- Update scripts/bash/create-new-feature.sh
- fix: use global maximum for branch numbering to prevent collisions

## [0.0.88] - 2025-12-01

### Changed

- fix the incorrect task-template file path

## [0.0.87] - 2025-12-01

### Changed

- Limit width and height to 200px to match the small logo
- docs: Switch readme logo to logo_large.webp
- fix:merge
- fix
- fix
- feat:qoder agent
- docs: Enhance quickstart guide with admonitions and examples
- docs: add constitution step to quickstart guide (fixes #906)
- Update supported AI agents in README.md
- cancel:test
- test
- fix:literal bug
- fix:test
- test
- fix:qoder url
- fix:download owner
- test
- feat:support Qoder CLI

## [0.0.86] - 2025-11-26

### Changed

- feat: add bob to new update-agent-context.ps1 + consistency in comments
- feat: add support for IBM Bob IDE

## [0.0.85] - 2025-11-14

### Changed

- Unset CDPATH while getting SCRIPT_DIR

## [0.0.84] - 2025-11-14

### Changed

- docs: fix broken link and improve agent reference
- docs: reorganize upgrade documentation structure
- docs: remove related documentation section from upgrading guide
- fix: remove broken link to existing project guide
- docs: Add comprehensive upgrading guide for Spec Kit
- Refactor ESLint configuration checks in implement.md to address deprecation

## [0.0.83] - 2025-11-14

### Changed

- feat: Add OVHcloud SHAI AI Agent

## [0.0.82] - 2025-11-14

### Changed

- fix: incorrect logic to create release packages with subset AGENTS or SCRIPTS

## [0.0.81] - 2025-11-14

### Changed

- Fix tasktoissues.md to use the 'github/github-mcp-server/issue_write' tool

## [0.0.80] - 2025-11-14

### Changed

- Refactor feature script logic and update agent context scripts
- Update templates/commands/taskstoissues.md
- Update CHANGELOG.md
- Update agent configuration
- Update scripts/powershell/create-new-feature.ps1
- Update src/specify_cli/__init__.py
- Create create-release-packages.ps1
- Script changes
- Update taskstoissues.md
- Create taskstoissues.md
- Update src/specify_cli/__init__.py
- Update CONTRIBUTING.md
- Potential fix for code scanning alert no. 3: Workflow does not contain permissions
- Update src/specify_cli/__init__.py
- Update CHANGELOG.md
- Fixes #970
- Fixes #975
- Support for version command
- Exclude generated releases
- Lint fixes
- Prompt updates
- Hand offs with prompts
- Chatmodes are back in vogue
- Let's switch to proper prompts
- Update prompts
- Update with prompt
- Testing hand-offs
- Use VS Code handoffs

## [0.0.79] - 2025-10-23

### Changed

- docs: restore important note about JSON output in specify command
- fix: improve branch number detection to check all sources
- feat: check remote branches to prevent duplicate branch numbers

## [0.0.78] - 2025-10-21

### Changed

- Update CONTRIBUTING.md
- docs: add steps for testing template and command changes locally
- update specify to make "short-name" argu for create-new-feature.sh in the right position

## [0.0.77] - 2025-10-21

### Changed

- fix: include the latest changelog in the `GitHub Release`'s  body

## [0.0.76] - 2025-10-21

### Changed

- Fix update-agent-context.sh to handle files without Active Technologies/Recent Changes sections

## [0.0.75] - 2025-10-21

### Changed

- Fixed indentation.
- Added correct `install_url` for Amp agent CLI script.
- Added support for Amp code agent.

## [0.0.74] - 2025-10-21

### Changed

- feat(ci): add markdownlint-cli2 for consistent markdown formatting

## [0.0.73] - 2025-10-21

### Changed

- revert vscode auto remove extra space
- fix: correct command references in implement.md
- fix regarding copilot suggestion
- fix: correct command references in speckit.analyze.md
- Support more lang/Devops of Common Patterns by Technology
- chore: replace `bun` by `node/npm` in the `devcontainer` (as many CLI-based agents actually require a `node` runtime)
- chore: add Claude Code extension to devcontainer configuration
- chore: add installation of `codebuddy` CLI in the `devcontainer`
- chore: fix path to powershell script in vscode settings
- fix: correct `run_command` exit behavior and improve installation instructions (for `Amazon Q`) in `post-create.sh` + fix typos in `CONTRIBUTING.md`
- chore: add `specify`'s github copilot chat settings to `devcontainer`
- chore: add `devcontainer` support  to ease developer workstation setup

## [0.0.72] - 2025-10-18

### Changed

- fix: correct argument parsing in create-new-feature.sh script

## [0.0.71] - 2025-10-18

### Changed

- fix: Skip CLI checks for IDE-based agents in check command
- Change loop condition to include last argument

## [0.0.70] - 2025-10-18

### Changed

- fix: broken media files
- Update README.md
- The function parameters lack type hints. Consider adding type annotations for better code clarity and IDE support.
- - **Smart JSON Merging for VS Code Settings**: `.vscode/settings.json` is now intelligently merged instead of being overwritten during `specify init --here` or `specify init .`   - Existing settings are preserved   - New Spec Kit settings are added   - Nested objects are merged recursively   - Prevents accidental loss of custom VS Code workspace configurations
- Fix: incorrect command formatting in agent context file, refix #895

## [0.0.69] - 2025-10-15

### Changed

- Update scripts/bash/create-new-feature.sh
- Update create-new-feature.sh
- Update files
- Update files
- Create .gitattributes
- Update wording
- Update logic for arguments
- Update script logic

## [0.0.68] - 2025-10-15

### Changed

- format content as copilot suggest
- Ruby, PHP, Rust, Kotlin, C, C++

## [0.0.67] - 2025-10-15

### Changed

- Use the number prefix to find the right spec

## [0.0.66] - 2025-10-15

### Changed

- Update CodeBuddy agent name to 'CodeBuddy CLI'
- Rename CodeBuddy to CodeBuddy CLI in update script
- Update AI coding agent references in installation guide
- Rename CodeBuddy to CodeBuddy CLI in AGENTS.md
- Update README.md
- Update CodeBuddy link in README.md
- update codebuddyCli

## [0.0.65] - 2025-10-15

### Changed

- Fix: Fix incorrect command formatting in agent context file
- docs: fix heading capitalization for consistency
- Update README.md

## [0.0.64] - 2025-10-14

### Changed

- Update tasks.md
- Update README.md

## [0.0.63] - 2025-10-14

### Changed

- fix: update CODEBUDDY file path in agent context scripts
- docs(readme): add /speckit.tasks step and renumber walkthrough

## [0.0.62] - 2025-10-11

### Changed

- A few more places to update from code review
- fix: align Cursor agent naming to use 'cursor-agent' consistently

## [0.0.61] - 2025-10-10

### Changed

- Update clarify.md
- add how to upgrade specify installation

## [0.0.60] - 2025-10-10

### Changed

- Update vscode-settings.json
- Update instructions and bug fix

## [0.0.59] - 2025-10-10

### Changed

- Update __init__.py
- Consolidate Cursor naming
- Update CHANGELOG.md
- Git errors are now highlighted.
- Update __init__.py
- Refactor agent configuration
- Update src/specify_cli/__init__.py
- Update scripts/powershell/update-agent-context.ps1
- Update AGENTS.md
- Update templates/commands/implement.md
- Update templates/commands/implement.md
- Update CHANGELOG.md
- Update changelog
- Update plan.md
- Add ignore file verification step to /speckit.implement command
- Escape backslashes in TOML outputs
- update CodeBuddy to international site
- feat: support codebuddy ai
- feat: support codebuddy ai

## [0.0.58] - 2025-10-08

### Changed

- Add escaping guidelines to command templates
- Update README.md
- Update README.md

## [0.0.57] - 2025-10-06

### Changed

- Update CHANGELOG.md
- Update command reference
- Package up VS Code settings for Copilot
- Update tasks-template.md
- Update templates/tasks-template.md
- Cleanup
- Update CLI changes
- Update template and docs
- Update checklist.md
- Update templates
- Cleanup redundancies
- Update checklist.md
- Codex CLI is now fully supported
- Update specify.md
- Prompt updates
- Update prompt prefix
- Update .github/workflows/scripts/create-release-packages.sh
- Consistency updates to commands
- Update commands.
- Update logs
- Template cleanup and reorganization
- Remove Codex named args limitation warning
- Remove Codex named args limitation from README.md

## [0.0.56] - 2025-10-02

### Changed

- docs(readme): link Amazon Q slash command limitation issue
- docs: clarify Amazon Q limitation and update init docstring
- feat(agent): Added Amazon Q Developer CLI Integration

## [0.0.55] - 2025-09-30

### Changed

- Update URLs to Contributing and Support Guides in Docs
- fix: add UTF-8 encoding to file read/write operations in update-agent-context.ps1
- Update __init__.py
- Update src/specify_cli/__init__.py
- docs: fix the paths of generated files (moved under a `.specify/` folder)
- Update src/specify_cli/__init__.py
- feat: support 'specify init .' for current directory initialization
- feat: Add emacs-style up/down keys

## [0.0.54] - 2025-09-25

### Changed

- Update CONTRIBUTING.md
- Refine `plan-template.md` with improved project type detection, clarified structure decision process, and enhanced research task guidance.
- Update __init__.py

## [0.0.53] - 2025-09-24

### Changed

- Update template path for spec file creation
- Update template path for spec file creation
- docs: remove constitution_update_checklist from README

## [0.0.52] - 2025-09-22

### Changed

- Update analyze.md
- Update templates/commands/analyze.md
- Update templates/commands/clarify.md
- Update templates/commands/plan.md
- Update with extra commands
- Update with --force flag
- feat: add uv tool install instructions to README

## [0.0.51] - 2025-09-21

### Changed

- Update with Roo Code support

## [0.0.50] - 2025-09-21

### Changed

- Update generate-release-notes.sh
- Update error messages
- Auggie folder fix

## [0.0.49] - 2025-09-21

### Changed

- Update scripts/powershell/update-agent-context.ps1
- Update templates/commands/implement.md
- Cleanup the check command
- Add support for Auggie
- Update AGENTS.md
- Updates with Kilo Code support
- Update README.md
- Update templates/commands/constitution.md
- Update templates/commands/implement.md
- Update templates/commands/plan.md
- Update templates/commands/specify.md
- Update templates/commands/tasks.md
- Update README.md
- Stop splitting the warning over multiple lines
- Update templates based on #419
- docs: Update README with codex in check command

## [0.0.48] - 2025-09-21

### Changed

- Update scripts/powershell/check-prerequisites.ps1
- Update CHANGELOG.md
- Update CHANGELOG.md
- Update changelog
- Update scripts/bash/update-agent-context.sh
- Fix script config
- Update scripts/bash/common.sh
- Update scripts/powershell/update-agent-context.ps1
- Update scripts/powershell/update-agent-context.ps1
- Clarification
- Update prompts
- Update update-agent-context.ps1
- Update CONTRIBUTING.md
- Update CONTRIBUTING.md
- Update CONTRIBUTING.md
- Update CONTRIBUTING.md
- Update CONTRIBUTING.md
- Update contribution guidelines.
- Root detection logic
- Update templates/plan-template.md
- Update scripts/bash/update-agent-context.sh
- Update scripts/powershell/create-new-feature.ps1
- Simplification
- Script and template tweaks
- Update config
- Update scripts/powershell/check-prerequisites.ps1
- Update scripts/bash/check-prerequisites.sh
- Fix script path
- Script cleanup
- Update scripts/bash/check-prerequisites.sh
- Update scripts/powershell/check-prerequisites.ps1
- Update script delegation from GitHub Action
- Cleanup the setup for generated packages
- Use proper line endings
- Consolidate scripts

## [0.0.47] - 2025-09-20

### Changed

- Updating agent context files

## [0.0.46] - 2025-09-20

### Changed

- Update update-agent-context.ps1
- Update package release
- Update config
- Update __init__.py
- Update __init__.py
- Remove Codex-specific logic in the initialization script
- Update version rev
- Update __init__.py
- Enhance Codex support by auto-syncing prompt files, allowing spec generation without git, and documenting clearer /specify usage.
- Consistency tweaks
- Consistent step coloring
- Update __init__.py
- Update __init__.py
- Quick UI tweak
- Update package release
- Limit workspace command seeding to Codex init and update Codex documentation accordingly.
- Clarify Codex-specific README note with rationale for its different workflow.
- Bump to 0.0.7 and document Codex support
- Normalize Codex command templates to the scripts-based schema and auto-upgrade generated commands.
- Fix remaining merge conflict markers in __init__.py
- Add Codex CLI support with AGENTS.md and commands bootstrap

## [0.0.45] - 2025-09-19

### Changed

- Update with Windsurf support
- expose token as an argument through cli --github-token
- add github auth headers if there are GITHUB_TOKEN/GH_TOKEN set

## [0.0.44] - 2025-09-18

### Changed

- Update specify.md
- Update __init__.py

## [0.0.43] - 2025-09-18

### Changed

- Update with support for /implement

## [0.0.42] - 2025-09-18

### Changed

- Update constitution.md

## [0.0.41] - 2025-09-18

### Changed

- Update constitution.md

## [0.0.40] - 2025-09-18

### Changed

- Update constitution command

## [0.0.39] - 2025-09-18

### Changed

- Cleanup
- fix: commands format for qwen

## [0.0.38] - 2025-09-18

### Changed

- Fix template path in update-agent-context.sh
- docs: fix grammar mistakes in markdown files

## [0.0.37] - 2025-09-17

### Changed

- fix: add missing Qwen support to release workflow and agent scripts

## [0.0.36] - 2025-09-17

### Changed

- feat: Add opencode ai agent
- Fix --no-git argument resolution.

## [0.0.35] - 2025-09-17

### Changed

- chore(release): bump version to 0.0.5 and update changelog
- chore: address review feedback - remove comment and fix numbering
- feat: add Qwen Code support to Spec Kit

## [0.0.34] - 2025-09-15

### Changed

- Update template.

## [0.0.33] - 2025-09-15

### Changed

- Update scripts

## [0.0.32] - 2025-09-15

### Changed

- Update template paths

## [0.0.31] - 2025-09-15

### Changed

- Update for Cursor rules & script path
- Update Specify definition
- Update README.md
- Update with video header
- fix(docs): remove redundant white space

## [0.0.30] - 2025-09-12

### Changed

- Update update-agent-context.ps1

## [0.0.29] - 2025-09-12

### Changed

- Update create-release-packages.sh
- Update with check changes

## [0.0.28] - 2025-09-12

### Changed

- Update wording
- Update release.yml

## [0.0.27] - 2025-09-12

### Changed

- Support Cursor

## [0.0.26] - 2025-09-12

### Changed

- Saner approach to scripts

## [0.0.25] - 2025-09-12

### Changed

- Update packaging

## [0.0.24] - 2025-09-12

### Changed

- Fix package logic

## [0.0.23] - 2025-09-12

### Changed

- Update config
- Update __init__.py
- Refactor with platform-specific constraints
- Update README.md
- Update CLI reference
- Update __init__.py
- refactor: extract Claude local path to constant for maintainability
- fix: support Claude CLI installed via migrate-installer

## [0.0.22] - 2025-09-11

### Changed

- Update release.yml
- Update create-release-packages.sh
- Update create-release-packages.sh
- Update release file

## [0.0.21] - 2025-09-11

### Changed

- Consolidate script creation
- Update how Copilot prompts are created
- Update local-development.md
- Local dev guide and script updates
- Update CONTRIBUTING.md
- Enhance HTTP client initialization with optional SSL verification and bump version to 0.0.3
- Complete Gemini CLI command instructions
- Refactor HTTP client usage to utilize truststore for SSL context
- docs: Update Commands sections renaming to match implementation
- docs: Fix formatting issues in README.md for consistency
- Update docs and release

## [0.0.20] - 2025-09-08

### Changed

- Update docs/quickstart.md
- Docs setup

## [0.0.19] - 2025-09-08

### Changed

- Update README.md

## [0.0.18] - 2025-09-08

### Changed

- Update README.md

## [0.0.17] - 2025-09-08

### Changed

- Remove trailing whitespace from tasks.md template

## [0.0.16] - 2025-09-07

### Changed

- Fix release workflow to work with repository rules

## [0.0.15] - 2025-09-07

### Changed

- Use `/usr/bin/env bash` instead of `/bin/bash` for shebang

## [0.0.14] - 2025-09-04

### Changed

- fix: correct typos in spec-driven.md

## [0.0.13] - 2025-09-04

### Changed

- Fix formatting in usage instructions

## [0.0.12] - 2025-09-04

### Changed

- Fix template path in plan command documentation

## [0.0.11] - 2025-09-04

### Changed

- fix: incorrect tree structure in examples

## [0.0.10] - 2025-09-04

### Changed

- fix minor typo in Article I

## [0.0.9] - 2025-09-03

### Changed

- Update CLI commands from '/spec' to '/specify'

## [0.0.8] - 2025-09-02

### Changed

- adding executable permission to the scripts so they execute when the coding agent launches them

## [0.0.7] - 2025-09-02

### Changed

- doco(spec-driven): Fix small typo in document

## [0.0.6] - 2025-08-25

### Changed

- Update README.md

## [0.0.5] - 2025-08-25

### Changed

- Update .github/workflows/release.yml
- Fix release workflow to work with repository rules

## [0.0.4] - 2025-08-25

### Changed

- Add John Lam as contributor and release badge

## [0.0.3] - 2025-08-22

### Changed

- Update requirements

## [0.0.2] - 2025-08-22

### Changed

- Update README.md

## [0.0.1] - 2025-08-22

### Changed

- Update release.yml

