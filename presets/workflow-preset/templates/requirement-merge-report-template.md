# Requirement Merge Report

Purpose: normalize Product Requirement and Design Requirement merge decisions for baseline `spec.md`.

## Product Requirement Inputs

- Source:
- Intake artifact:
- Confirmed product facts:
- Open product gaps:

## Design Requirement Inputs

- Source:
- Intake artifact:
- Confirmed design facts:
- Open design gaps:

## Merge Rules

Product Requirement owns:

- business goals
- user roles and permissions
- data semantics
- validation rules
- interface semantics
- exception handling
- non-functional requirements

Design Requirement owns:

- page structure
- information hierarchy
- interaction paths
- component states
- visual tokens
- layout and responsive behavior
- motion behavior
- visual acceptance requirements

## Design Requirement Promotion Rules

- Promote observed design facts with source refs to design requirements.
- Promote confirmed design facts to design requirements.
- Inferred design facts remain assumptions or `[NEEDS CLARIFICATION]`.
- Missing design facts remain `[NEEDS CLARIFICATION]`.
- Promote screenshot-supported visual facts only as visual requirements with screenshot refs.
- Screenshot-implied business rules must remain `[NEEDS CLARIFICATION]`.

## Conflict Resolution

- Conflict ID:
- Product requirement source:
- Design requirement source:
- Resolution:
- Clarification needed:

## Clarification Outputs

- Item:
- Target `spec.md` section:
- Marker: `[NEEDS CLARIFICATION]`
- Blocking impact:

## Baseline Spec Handoff

- `spec.md` sections to create or update:
- Confirmed requirements:
- Unresolved requirement ambiguities:
- Source refs required in `spec.md`:
