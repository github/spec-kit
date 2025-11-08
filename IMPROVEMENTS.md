# Future Improvements

This document tracks all planned improvements and known limitations for the Spec Kit project.

**⚠️ IMPORTANT:** Never add TODO comments to prompt files or templates! They can confuse AI agents. Always add improvements here instead.

---

## 🔴 High Priority

### Scripts (create-new-feature.sh / .ps1)

- [ ] Add automated tests for regex patterns and edge cases
- [ ] Add environment variable for enforcing Jira requirement (`REQUIRE_JIRA=true`)
- [ ] Improve error messages with examples and suggestions
- [ ] Add validation examples to help text

### Interactive Prompts

- [ ] Add validation of interactive input format with clear error messages
  - Constitution: Validate PRINCIPLES/PROJECT METADATA structure
  - Specify: Validate JIRA:/FEATURE: line format
- [ ] Add retry logic if user input is malformed
- [ ] Add feature description quality checks (minimum length, keyword detection)
- [ ] Add confirmation step showing what will be created before proceeding

---

## 🟡 Medium Priority

### Testing & Quality

- [ ] Create test suite for branch detection regex patterns
- [ ] Add integration tests for script execution with various inputs
- [ ] Add smoke tests for common scenarios
- [ ] Test edge cases:
  - Very long branch names (near 244 char limit)
  - Special characters in Jira numbers
  - Empty/whitespace inputs
  - Concurrent branch creation

### Documentation

- [ ] Replace `[PLACEHOLDER_CONSTITUTION_EXAMPLES_LINK]` with real URL
- [ ] Add inline constitution examples (remove external dependency)
- [ ] Create troubleshooting guide for common errors
- [ ] Document branch naming convention in README

### User Experience

- [ ] Add progress indicators for long-running operations
- [ ] Improve error messages with actionable suggestions
- [ ] Add `--dry-run` flag to preview branch creation
- [ ] Add `--force` flag to override validations when needed

---

## 🟢 Low Priority / Nice to Have

### AGENTS.md Enforcement

- [ ] Explore technical enforcement alternatives (currently guidance-only)
- [ ] Add verification token system (if feasible)
- [ ] IDE plugin to auto-inject AGENTS.md into context
- [ ] Add reminder if AGENTS.md exists but not acknowledged

### Interactive Mode Enhancements

- [ ] Add autocomplete for common patterns
- [ ] Add interactive help/examples on demand
- [ ] Support multiple input formats (JSON, YAML, key-value)
- [ ] Add template library for common project types

### Branch Management

- [ ] Add command to list all feature branches
- [ ] Add command to cleanup old/merged branches
- [ ] Add branch naming validation before creation

### Corporate Guidelines - Future Enhancements

**Note**: Phase 1-4 completed. See "Completed Improvements" section below.

Additional nice-to-have features:

- [ ] Interactive guideline compliance checker
- [ ] Guideline diff tool (compare project vs template)
- [ ] Auto-fix common guideline violations
- [ ] Guideline analytics (compliance metrics)
- [ ] Enhanced CI/CD integration for guideline checking
- [ ] Guideline version management and migration tools
- [ ] Team-specific guideline overrides

### PowerShell Script

- [ ] Improve regex matching (mirror bash improvements)
- [ ] Add better error handling for Windows-specific issues
- [ ] Test on PowerShell Core (cross-platform)

### Reverse Engineering & Modernization Feature

**Current Status**: v1.0.0-alpha (EXPERIMENTAL) - Working implementation complete (~4,564 LOC Python)

**Note**: Phases 1-4 complete. See "Completed Improvements" section below.

**Phase 2 - Language-Specific Analyzers** ✅ COMPLETE:

- [x] JavaScript/Node.js analyzer (framework detection, build tools) - `languages/javascript.py` (661 lines)
- [x] Python analyzer (virtual env, framework detection) - `languages/python.py` (524 lines)
- [x] Java analyzer (Maven/Gradle, Spring Boot) - `languages/java.py` (423 lines)
- [x] .NET analyzer (NuGet, project type) - `languages/dotnet.py` (~400 lines)
- [ ] Ruby analyzer (Rails, Bundler) - Deferred (low priority)
- [ ] PHP analyzer (Composer, Laravel/Symfony) - Deferred (low priority)

**Phase 3 - Incremental Analysis** ✅ COMPLETE:

- [x] Checkpoint system for large codebases - `checkpoint.py` implemented
- [x] Resume capability from last checkpoint
- [x] Progress indicators and streaming reports
- [x] Support for 500K+ LOC projects

**Phase 4 - Advanced Features** ✅ COMPLETE:

- [x] CI/CD integration templates (GitHub Actions, GitLab CI, Jenkins)
- [ ] Baseline comparison (track improvements over time) - Deferred to Phase 6
- [ ] Plugin architecture for custom analyzers - Deferred to Phase 6
- [ ] Export formats (PDF, JSON, HTML, CSV) - Partial (JSON exists)
- [ ] Architecture diagram generation - Deferred to Phase 6

**Phase 5 - Enterprise Features** (Deferred):

- [ ] Multi-project/monorepo analysis
- [x] Customizable scoring weights - `config.py` with ScoringWeights dataclass
- [ ] Team capacity assessment
- [ ] Historical analytics and trending

---

### Phase 6 - Production Readiness (v1.0.0-alpha → v1.0.0)

**Goal**: Move from EXPERIMENTAL to PRODUCTION-READY status

**Current Blockers**:

- ❌ No unit tests (0% coverage)
- ❌ Not tested on real-world projects (0 validations)
- ❌ AI-guided workflow requires manual intervention
- ❌ No beta testing or user feedback
- ❌ No security audit completed

**Timeline**: 4-6 months (16-23 weeks) with 1-2 FTE developers

#### 6.1 Testing & Validation (4-6 weeks) - HIGH PRIORITY

**Unit Tests**:

- [ ] Create `tests/` directory structure
- [ ] Write unit tests for all Python modules:
  - [ ] `test_scanner.py` - Tech stack detection, metrics
  - [ ] `test_dependency_analyzer.py` - npm/pip parsing
  - [ ] `test_scoring_engine.py` - Feasibility algorithms
  - [ ] `test_report_generator.py` - Report generation
  - [ ] `test_security.py` - Path validation edge cases
  - [ ] `test_config.py` - Configuration validation
- [ ] Add pytest configuration (`pytest.ini`, `pyproject.toml`)
- [ ] Add coverage reporting (`pytest-cov`)
- [ ] Achieve 85%+ code coverage
- [ ] Add CI/CD workflow for automated testing

**Integration Tests**:

- [ ] Test against 10+ real-world projects:
  - [ ] 3x Node.js projects (React, Vue, Express)
  - [ ] 2x Python projects (Django, Flask)
  - [ ] 2x Java projects (Spring Boot)
  - [ ] 2x .NET projects (ASP.NET Core)
  - [ ] 1x Go project
  - [ ] 1x Rust project
- [ ] Validate analysis accuracy vs manual audits (target: 95%+)
- [ ] Document edge cases and failure modes
- [ ] Add regression tests for discovered issues

**Performance Testing**:

- [ ] Test varying project sizes:
  - [ ] Small (< 10K LOC)
  - [ ] Medium (10K-100K LOC)
  - [ ] Large (100K-500K LOC)
  - [ ] Very Large (500K+ LOC)
- [ ] Measure and document:
  - [ ] Analysis time vs project size
  - [ ] Memory usage
  - [ ] CPU utilization
- [ ] Fix performance bottlenecks
- [ ] Add timeout handling for very large projects
- [ ] Target: < 30 minutes for 500K LOC, < 2GB RAM

**Error Handling**:

- [ ] Test error scenarios:
  - [ ] Missing/corrupted package.json
  - [ ] Inaccessible files/directories
  - [ ] Mixed language projects
  - [ ] Monorepos
  - [ ] Binary files in codebase
- [ ] Improve error messages with actionable guidance
- [ ] Add graceful degradation for all failure modes
- [ ] Log errors with context for debugging

#### 6.2 Automation Improvements (3-4 weeks) - HIGH PRIORITY

**Reduce AI Manual Intervention**:

- [ ] Implement full automated report generation
- [ ] Auto-populate all template sections from analysis data
- [ ] Add CLI mode for non-interactive execution:

  ```bash
  python -m analyzer.main --project /path --depth STANDARD --output json
  ```

- [ ] Implement automated decision-making:
  - [ ] Auto-recommend inline vs greenfield based on scores
  - [ ] Auto-prioritize issues by severity
  - [ ] Auto-generate upgrade roadmap
- [ ] Target: Complete analysis without AI agent intervention

**External Tool Integration**:

- [ ] Add automatic tool detection and installation suggestions
- [ ] Improve fallback analysis quality (< 10% difference)
- [ ] Add support for more package managers:
  - [ ] Cargo (Rust) - full support
  - [ ] Go modules - full support
  - [ ] Composer (PHP) - full support
  - [ ] Bundler (Ruby) - full support
  - [ ] NuGet (.NET) - upgrade from "unsupported"
  - [ ] Maven/Gradle (Java) - upgrade from "unsupported"
- [ ] Add CVE database integration (offline mode)

**Structured Output Formats**:

- [x] JSON output format - Already exists
- [ ] YAML output format
- [ ] HTML report generation
- [ ] PDF export (optional)
- [ ] CSV for metrics

#### 6.3 User Validation (6-8 weeks) - MEDIUM PRIORITY

**Beta Testing Program**:

- [ ] Recruit 20+ beta testers:
  - [ ] Enterprise developers
  - [ ] Open source maintainers
  - [ ] Consultants/agencies
  - [ ] Individual developers
- [ ] Provide testing guidelines and feedback forms
- [ ] Collect structured feedback:
  - [ ] Analysis accuracy
  - [ ] Report usefulness
  - [ ] Time savings
  - [ ] Missing features
  - [ ] Bugs/issues
- [ ] Iterate based on feedback (minimum 2 cycles)
- [ ] Target: 80%+ satisfaction, < 5 critical bugs

**Case Studies**:

- [ ] Create 5+ detailed case studies:
  - [ ] Legacy Node.js app modernization
  - [ ] Java monolith assessment
  - [ ] Python Django upgrade
  - [ ] .NET framework → .NET 8 migration
  - [ ] React 16 → React 18 upgrade
- [ ] Document before/after metrics
- [ ] Create video walkthroughs (optional)
- [ ] Publish case studies with real data

#### 6.4 Production Hardening (2-3 weeks) - MEDIUM PRIORITY

**Security Audit**:

- [ ] Security review of path validation logic
- [ ] Test against malicious inputs:
  - [ ] Path traversal attacks
  - [ ] Symlink attacks
  - [ ] Command injection via subprocess
  - [ ] Resource exhaustion (DoS)
- [ ] Add rate limiting for subprocess calls
- [ ] Implement sandboxing for untrusted projects
- [ ] Add security scanning to CI/CD (Bandit, Safety)
- [ ] Target: Pass audit with 0 high/critical findings

**Dependency Management**:

- [ ] Create `requirements.txt` with pinned versions
- [ ] Create `requirements-dev.txt` for dev tools
- [ ] Test with minimum supported Python versions
- [ ] Document Python version compatibility (3.10+)
- [ ] Add dependency vulnerability scanning (Dependabot, Snyk)
- [ ] Add `setup.py` or `pyproject.toml` for distribution

**Cross-Platform Testing**:

- [ ] Test on Linux (Ubuntu, Debian, Fedora, Arch)
- [ ] Test on macOS (Intel + Apple Silicon)
- [ ] Test on Windows (10, 11)
- [ ] Test on Python versions (3.10, 3.11, 3.12)
- [ ] Fix platform-specific issues
- [ ] Document compatibility matrix

#### 6.5 Documentation & Support (2 weeks) - MEDIUM PRIORITY

**Documentation**:

- [ ] API documentation for Python modules (Sphinx)
- [ ] Developer guide for contributors
- [ ] Detailed troubleshooting guide
- [ ] FAQ based on beta testing feedback
- [ ] Architecture diagrams (system design, data flow)
- [ ] Performance tuning guide
- [ ] Migration guide (alpha → v1.0)

**Support Infrastructure**:

- [ ] Create GitHub issue templates:
  - [ ] Bug report
  - [ ] Feature request
  - [ ] Analysis accuracy issue
- [ ] Set up GitHub Discussions for Q&A
- [ ] Update contributing guidelines
- [ ] Add code of conduct
- [ ] Set up automated issue triage

#### 6.6 Release Engineering (1 week) - LOW PRIORITY

**Version Management**:

- [ ] Update version: v1.0.0-alpha → v1.0.0-beta1 (after 6.1)
- [ ] Update version: v1.0.0-beta1 → v1.0.0-rc1 (after 6.2-6.3)
- [ ] Update version: v1.0.0-rc1 → v1.0.0 (after 6.4-6.5)
- [ ] Update all documentation references
- [ ] Create release notes for each version
- [ ] Tag releases in Git
- [ ] Publish to PyPI (optional)
- [ ] Update README badges

**Success Criteria for v1.0.0**:

- ✅ 85%+ unit test coverage
- ✅ 95%+ accuracy on 10+ real projects
- ✅ Full automation (no AI intervention)
- ✅ 80%+ beta tester satisfaction
- ✅ 5+ published case studies
- ✅ Pass security audit
- ✅ Cross-platform compatibility verified
- ✅ Complete documentation

---

### Quick Wins (Can Start Immediately)

**Week 1-2**:

- [ ] Create `tests/` directory + basic test structure
- [ ] Add pytest + pytest-cov to project
- [ ] Create `requirements.txt` with pinned dependencies
- [ ] Set up GitHub Actions for CI/CD
- [ ] Test on 3 diverse real projects

**Week 3-4**:

- [ ] Write unit tests for scanner.py, scoring_engine.py
- [ ] Improve error messages with examples
- [ ] Add CLI mode for non-interactive execution
- [ ] Create troubleshooting guide
- [ ] Add security scanning (Bandit)

**Impact**: These 10 items enable **v1.0.0-beta1** release

---

## 🐛 Known Limitations

### By Design

- **Jira number is optional:** Can be made required via env var (future)
- **AGENTS.md enforcement is guidance-only:** Technical enforcement not feasible with current architecture
- **Interactive mode detection fragile:** Relies on literal `$ARGUMENTS` string matching
- **Branch numbering race condition:** Possible if multiple users create branches simultaneously

### Technical Constraints

- **No real-time validation:** Can't validate input until agent processes it
- **IDE-dependent behavior:** Some IDEs may not support interactive prompts well
- **Git fetch required:** Branch detection needs network access to check remote branches

---

## 📝 Maintenance

### Review Schedule

- **Monthly:** Review this document and prioritize items
- **Per sprint:** Pick 1-2 high priority items to implement
- **As needed:** Add new items as they're discovered

### Adding New Items

When adding improvements:

1. Choose priority level (🔴 High / 🟡 Medium / 🟢 Low)
2. Add checkbox with clear description
3. Include why it's needed and impact if not done
4. Link to related issues/PRs if applicable

### Completing Items

When completing improvements:

1. Mark checkbox as complete: `- [x]`
2. Add completion date and PR link
3. Move to "Completed" section at bottom (optional)
4. Update related documentation

---

## ✅ Completed Improvements

Track completed items here for reference.

### 2025-01-15

- [x] Add Jira number validation (regex format check) - PR #X
- [x] Fix branch detection regex to be more precise - PR #X
- [x] Clarify interactive input formats with templates - PR #X
- [x] Fix all markdownlint errors (multiple PRs) - PR #X
- [x] Create centralized improvements document - PR #X
- [x] Fix interactive mode detection in prompts (plan, implement, tasks, analyze) - PR #X
- [x] Implement Corporate Guidelines Phase 1 (Foundation) - PR #X
  - Created 7 guideline template files
  - Integrated guidelines into plan/implement/analyze/tasks prompts
  - Added tech stack auto-detection
  - Implemented multi-stack support
  - Added non-compliance handling
  - Updated AGENTS.md with guidelines documentation
- [x] Implement Corporate Guidelines Phase 2 (Configurable Branch Naming) - PR #18 (commit 98195d8)
  - Created `branch-config.json` schema
  - Refactored `create-new-feature.sh` to read from config file
  - Refactored `create-new-feature.ps1` to read from config file
  - Made Jira format configurable with regex patterns
  - Made Jira optional for teams without ticket systems
  - Maintained backward compatibility with defaults
  - Added documentation for branch configuration
- [x] Implement Corporate Guidelines Phase 3 (Multi-Stack Coordination) - PR #19 (commit 8f51529)
  - Implemented guideline precedence rules for multi-stack projects
  - Created `stack-mapping.json` for file-to-stack mapping
  - Added contextual guideline application logic
  - Optimized token usage with selective loading
  - Updated templates for multi-stack detection
  - Added examples for common combinations (React+Java, etc.)
- [x] Implement Corporate Guidelines Phase 4 (Advanced Features) - PR #21 (commit 13fd910)
  - Enhanced analysis capabilities
  - Added comprehensive testing suite for critical paths
  - Implemented advanced guideline features
  - Completed full corporate customization system
- [x] Implement Reverse Engineering Phase 1 (Core Implementation) - (commits f0eff30, 9f5629a)
  - Created scoring_engine.py for feasibility scoring (inline/greenfield) - 423 lines
  - Created dependency_analyzer.py for npm/pip security analysis - 524 lines
  - Created scanner.py for tech stack detection and metrics - 661 lines
  - Created report_generator.py for markdown report generation - ~800 lines
  - Created security.py for path validation - 118 lines
  - Created config.py for configuration management - 99 lines
  - Created analyze-project.sh bash orchestration script
  - Created analyze-project-setup.sh for cross-platform setup
  - Created analyze-project-setup.ps1 for PowerShell support
  - Full end-to-end analysis workflow operational
  - Total implementation: ~4,564 lines of Python + orchestration scripts
- [x] Implement Reverse Engineering Phase 2 (Language Analyzers) - (commit c414e65)
  - Created languages/javascript.py for Node.js/JavaScript analysis - ~661 lines
  - Created languages/python.py for Python-specific analysis - ~524 lines
  - Created languages/java.py for Java/Maven/Gradle analysis - ~423 lines
  - Created languages/dotnet.py for .NET/NuGet analysis - ~400 lines
  - 4 core language analyzers complete (Ruby/PHP deferred to Phase 6)
  - Framework detection, build tool detection, version detection
  - Graceful degradation when package managers unavailable
- [x] Implement Reverse Engineering Phase 3 (Checkpointing) - (commit verified 2025-11-08)
  - Created checkpoint.py for incremental analysis
  - Resume capability for interrupted analysis
  - Progress tracking and ETA estimation
  - Streaming report generation
  - Support for 500K+ LOC projects
- [x] Implement Reverse Engineering Phase 4 (CI/CD & Advanced Features) - (commit verified 2025-11-08)
  - Created GitHub Actions workflow template
  - Created GitLab CI configuration template
  - Created Jenkins pipeline template
  - Implemented customizable scoring weights (config.py)
  - JSON output format support
  - Complete documentation in templates
- [x] Deep analysis and documentation accuracy update - (commit c18c770, 2025-11-08)
  - Analyzed complete implementation (~4,564 LOC Python)
  - Updated reverse-engineering.md with accurate status
  - Clarified EXPERIMENTAL status with transparent reasons
  - Added comprehensive parameter documentation to README
  - Fixed Mermaid diagram rendering errors

---

## 📚 Historical Records

### Corporate Guidelines Implementation (2025-01-06 to 2025-11-06)

**Original Planning Document**: `GUIDELINES-IMPLEMENTATION-PLAN.md` (archived - content preserved below)

**Purpose**: Enable corporate customization of Spec Kit through configurable guidelines for tech stack standards, branch naming conventions, and multi-stack project support.

**Implementation Approach**: 4-phase rollout with clear deliverables and success criteria at each phase.

**Final Status**: ✅ **FULLY IMPLEMENTED** - All 4 phases completed successfully.

**Key Deliverables**:

1. `.guidelines/` directory with comprehensive templates (ReactJS, Java, .NET, Node.js, Python)
2. `branch-config.json` for configurable branch naming patterns
3. `stack-mapping.json` for multi-stack project coordination
4. Integration into all command templates (plan, implement, analyze, tasks)
5. Tech stack auto-detection and contextual guideline application
6. Priority system: Constitution > Corporate Guidelines > Spec Kit Defaults

**Results**:

- Teams can now customize Spec Kit to match corporate standards
- Supports corporate package registries (Artifactory, Nexus)
- Configurable branch naming without code changes
- Multi-stack projects (React+Java, etc.) properly supported
- Backward compatible - works with existing projects

**Lessons Learned**:

- Phased approach worked well for managing complexity
- Template-based guidelines provided good flexibility
- JSON configuration files easier than hardcoded scripts
- Token usage optimization critical for multi-stack support
- Clear priority hierarchy (Constitution > Guidelines > Defaults) prevented conflicts

**Reference PRs**:

- Phase 1: Foundation - TBD
- Phase 2: Branch Configuration - PR #18 (commit 98195d8)
- Phase 3: Multi-Stack Coordination - PR #19 (commit 8f51529)
- Phase 4: Advanced Features - PR #21 (commit 13fd910)

**Implementation Plan Archive**: For detailed phase breakdown, technical architecture, and original planning rationale, see Git history: `GUIDELINES-IMPLEMENTATION-PLAN.md` (removed 2025-11-07 after completion).

---

## 🤝 Contributing

To propose a new improvement:

1. Add it to the appropriate priority section above
2. Create a GitHub issue for discussion (for major changes)
3. Submit PR with implementation
4. Update this document when merged

**Remember:** Never add TODOs directly in prompt files!
