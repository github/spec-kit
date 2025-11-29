-- =============================================================================
-- SPECTRENA LINEAGE SCHEMA
-- =============================================================================
-- Run with: surreal import --conn file://.spectrena/lineage.db schema.surql

-- -----------------------------------------------------------------------------
-- NODE TABLES (Entities)
-- -----------------------------------------------------------------------------

-- Specifications
DEFINE TABLE spec SCHEMAFULL;
DEFINE FIELD id ON spec TYPE string;          -- GUIDANCE-001-task-capture
DEFINE FIELD title ON spec TYPE string;
DEFINE FIELD component ON spec TYPE option<string>;
DEFINE FIELD status ON spec TYPE string DEFAULT 'draft';
    -- draft | approved | in_progress | completed | archived
DEFINE FIELD weight ON spec TYPE string DEFAULT 'STANDARD';
    -- LIGHTWEIGHT | STANDARD | FORMAL
DEFINE FIELD spec_path ON spec TYPE string;
DEFINE FIELD created_at ON spec TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON spec TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_spec_component ON spec FIELDS component;
DEFINE INDEX idx_spec_status ON spec FIELDS status;


-- Implementation Plans
DEFINE TABLE plan SCHEMAFULL;
DEFINE FIELD id ON plan TYPE string;          -- GUIDANCE-001-task-capture-plan
DEFINE FIELD plan_path ON plan TYPE string;
DEFINE FIELD tech_stack ON plan TYPE option<array<string>>;
DEFINE FIELD estimated_hours ON plan TYPE option<float>;
DEFINE FIELD created_at ON plan TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_plan_created ON plan FIELDS created_at;


-- Tasks (atomic units of work)
DEFINE TABLE task SCHEMAFULL;
DEFINE FIELD id ON task TYPE string;          -- GUIDANCE-001-T01
DEFINE FIELD title ON task TYPE string;
DEFINE FIELD description ON task TYPE option<string>;
DEFINE FIELD status ON task TYPE string DEFAULT 'pending';
    -- pending | active | blocked | completed | skipped
DEFINE FIELD phase ON task TYPE option<string>;
    -- setup | core | integration | testing | docs
DEFINE FIELD estimated_minutes ON task TYPE option<int>;
DEFINE FIELD actual_minutes ON task TYPE option<int>;
DEFINE FIELD started_at ON task TYPE option<datetime>;
DEFINE FIELD completed_at ON task TYPE option<datetime>;
DEFINE FIELD created_at ON task TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_task_status ON task FIELDS status;
DEFINE INDEX idx_task_phase ON task FIELDS phase;


-- Code Symbols (functions, classes, files)
DEFINE TABLE symbol SCHEMAFULL;
DEFINE FIELD fqn ON symbol TYPE string;       -- src/spectrena/config.py::Config.load
DEFINE FIELD name ON symbol TYPE string;      -- load
DEFINE FIELD kind ON symbol TYPE string;      -- function | class | method | file | module
DEFINE FIELD file_path ON symbol TYPE string;
DEFINE FIELD line_start ON symbol TYPE option<int>;
DEFINE FIELD line_end ON symbol TYPE option<int>;
DEFINE FIELD signature ON symbol TYPE option<string>;
DEFINE FIELD docstring ON symbol TYPE option<string>;
DEFINE FIELD created_at ON symbol TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON symbol TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_symbol_fqn ON symbol FIELDS fqn UNIQUE;
DEFINE INDEX idx_symbol_file ON symbol FIELDS file_path;
DEFINE INDEX idx_symbol_kind ON symbol FIELDS kind;


-- Worktree Sessions (parallel development tracking)
DEFINE TABLE session SCHEMAFULL;
DEFINE FIELD id ON session TYPE string;       -- UUID
DEFINE FIELD branch ON session TYPE string;
DEFINE FIELD worktree_path ON session TYPE string;
DEFINE FIELD started_at ON session TYPE datetime DEFAULT time::now();
DEFINE FIELD ended_at ON session TYPE option<datetime>;
DEFINE FIELD status ON session TYPE string DEFAULT 'active';
    -- active | paused | completed | abandoned

DEFINE INDEX idx_session_branch ON session FIELDS branch;
DEFINE INDEX idx_session_status ON session FIELDS status;


-- Code Changes (time-series events)
DEFINE TABLE change SCHEMAFULL;
DEFINE FIELD id ON change TYPE string;        -- UUID or sequential
DEFINE FIELD change_type ON change TYPE string;
    -- create | modify | delete | rename | move
DEFINE FIELD file_path ON change TYPE string;
DEFINE FIELD diff_summary ON change TYPE option<string>;
DEFINE FIELD lines_added ON change TYPE option<int>;
DEFINE FIELD lines_removed ON change TYPE option<int>;
DEFINE FIELD commit_sha ON change TYPE option<string>;
DEFINE FIELD created_at ON change TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_change_time ON change FIELDS created_at;
DEFINE INDEX idx_change_file ON change FIELDS file_path;


-- Phase State (singleton for current context)
DEFINE TABLE phase_state SCHEMAFULL;
DEFINE FIELD current_phase ON phase_state TYPE string DEFAULT 'constitution';
    -- constitution | specify | plan | implement | review
DEFINE FIELD updated_at ON phase_state TYPE datetime DEFAULT time::now();


-- -----------------------------------------------------------------------------
-- EDGE TABLES (Relationships)
-- -----------------------------------------------------------------------------

-- Spec depends on Spec (DAG)
DEFINE TABLE depends_on SCHEMAFULL TYPE RELATION IN spec OUT spec;
DEFINE FIELD dependency_type ON depends_on TYPE string DEFAULT 'hard';
    -- hard (blocks) | soft (should have) | optional
DEFINE FIELD created_at ON depends_on TYPE datetime DEFAULT time::now();


-- Spec blocks Spec (inverse view, computed)
-- Query: SELECT <-depends_on<-spec FROM spec:X gives "what blocks X"
-- Query: SELECT ->depends_on->spec FROM spec:X gives "what X blocks"


-- Plan implements Spec
DEFINE TABLE implements SCHEMAFULL TYPE RELATION IN plan OUT spec;
DEFINE FIELD created_at ON implements TYPE datetime DEFAULT time::now();


-- Task belongs to Plan
DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN task OUT plan;
DEFINE FIELD order ON belongs_to TYPE int DEFAULT 0;
DEFINE FIELD created_at ON belongs_to TYPE datetime DEFAULT time::now();


-- Task depends on Task (within or across plans)
DEFINE TABLE task_depends SCHEMAFULL TYPE RELATION IN task OUT task;
DEFINE FIELD created_at ON task_depends TYPE datetime DEFAULT time::now();


-- Task modifies Symbol
DEFINE TABLE modifies SCHEMAFULL TYPE RELATION IN task OUT symbol;
DEFINE FIELD change_type ON modifies TYPE string;  -- create | modify | delete
DEFINE FIELD created_at ON modifies TYPE datetime DEFAULT time::now();


-- Change records modification (time-series link)
DEFINE TABLE records SCHEMAFULL TYPE RELATION IN change OUT symbol;
DEFINE FIELD created_at ON records TYPE datetime DEFAULT time::now();


-- Change performed in Task
DEFINE TABLE performed_in SCHEMAFULL TYPE RELATION IN change OUT task;
DEFINE FIELD created_at ON performed_in TYPE datetime DEFAULT time::now();


-- Symbol references Symbol (call graph)
DEFINE TABLE references SCHEMAFULL TYPE RELATION IN symbol OUT symbol;
DEFINE FIELD reference_type ON references TYPE string;
    -- calls | imports | inherits | uses | instantiates
DEFINE FIELD created_at ON references TYPE datetime DEFAULT time::now();


-- Session works on Spec
DEFINE TABLE works_on SCHEMAFULL TYPE RELATION IN session OUT spec;
DEFINE FIELD created_at ON works_on TYPE datetime DEFAULT time::now();


-- Session activates Task
DEFINE TABLE activates SCHEMAFULL TYPE RELATION IN session OUT task;
DEFINE FIELD activated_at ON activates TYPE datetime DEFAULT time::now();
DEFINE FIELD deactivated_at ON activates TYPE option<datetime>;


-- Phase State references current context
DEFINE TABLE current_spec SCHEMAFULL TYPE RELATION IN phase_state OUT spec;
DEFINE TABLE current_task SCHEMAFULL TYPE RELATION IN phase_state OUT task;
DEFINE TABLE current_session SCHEMAFULL TYPE RELATION IN phase_state OUT session;


-- -----------------------------------------------------------------------------
-- EVENTS (for audit trail / time-travel)
-- -----------------------------------------------------------------------------

-- Track all status changes for analytics
DEFINE TABLE status_change SCHEMAFULL;
DEFINE FIELD entity_type ON status_change TYPE string;  -- spec | task | session
DEFINE FIELD entity_id ON status_change TYPE string;
DEFINE FIELD old_status ON status_change TYPE option<string>;
DEFINE FIELD new_status ON status_change TYPE string;
DEFINE FIELD changed_at ON status_change TYPE datetime DEFAULT time::now();
DEFINE FIELD changed_by ON status_change TYPE option<string>;  -- user or "claude"

DEFINE INDEX idx_status_change_time ON status_change FIELDS changed_at;
DEFINE INDEX idx_status_change_entity ON status_change FIELDS entity_type, entity_id;
