# 06 — Rollout & Testing plan

## Goal
Introduce ticket-mode in Spec Kit safely, with clear docs and validation.

---

## Phased rollout

### Phase 1: Templates and scripts only (no analysis)
- Add `templates/ticket-mode/*`
- Add `create-new-ticket` scripts
- Add `/speckit.ticket` command template

Validation:
- Windows PowerShell path correctness
- rerun safety (no destructive overwrites)

### Phase 2: Planning + reviews commands
- Add `/speckit.ticket-plan`
- Add `/speckit.ticket-reviews`
- Add optional `/speckit.ticket-step`

Validation:
- Works for existing ticket folders
- Creates missing files only

### Phase 3: Read-only analysis
- Add `/speckit.ticket-analyze`

Validation:
- Does not modify files
- Produces deterministic report on TOUR-7328 samples

---

## Test matrix

### OS
- Windows (PowerShell) — required
- Bash script parity (optional but should stay consistent)

### Scenarios
1) Fresh ticket init
- no existing folder
- confirm structure created

2) Existing ticket folder with partial files
- ensure missing files created, existing preserved

3) Ticket with reviews
- ensure review files are created but not overwritten

4) Ticket analyze on TOUR-7328 content
- ensure it finds:
  - any missing closure logs
  - any missing AC mapping

---

## Documentation updates

- `spec-kit/docs/quickstart.md`: add “Ticket-mode” as an alternate path
- `spec-kit/docs/index.md`: mention enterprise/brownfield ticket workflows
- `spec-kit/spec-driven.md`: briefly explain how ticket-mode complements feature-mode

---

## Acceptance criteria (for this initiative)

- Ticket mode commands work end-to-end on Windows
- No existing feature-mode commands are impacted
- Rerunning commands is safe
- Analysis is read-only
