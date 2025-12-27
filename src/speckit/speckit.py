"""
Main SpecKit orchestrator class.

This module provides the primary interface for spec-driven development,
coordinating LLM providers, storage, and workflow phases.

Example:
    >>> from speckit import SpecKit
    >>> kit = SpecKit("./my-project")
    >>> spec = kit.specify("Add user authentication")
    >>> plan = kit.plan(spec)
    >>> tasks = kit.tasks(plan)
"""

from pathlib import Path
from typing import Optional

from speckit.config import LLMConfig, SpecKitConfig
from speckit.llm import LiteLLMProvider
from speckit.schemas import (
    AnalysisReport,
    APIContract,
    ClarificationQuestion,
    Constitution,
    DataModel,
    QualityChecklist,
    QuickstartGuide,
    ResearchFindings,
    Specification,
    TaskBreakdown,
    TechStack,
    TechnicalPlan,
)
from speckit.storage.file_storage import FileStorage


class SpecKit:
    """
    Main orchestrator for spec-driven development workflow.

    Provides access to all workflow phases:
    - constitution(): Create project principles
    - specify(): Generate feature specifications
    - clarify(): Identify clarification questions
    - plan(): Generate technical plans
    - tasks(): Generate implementation tasks
    - analyze(): Check artifact consistency

    Example:
        >>> kit = SpecKit("./my-project")
        >>> spec = kit.specify("Add user authentication")
        >>> print(spec.to_markdown())
    """

    def __init__(
        self,
        project_path: str | Path,
        config: Optional[SpecKitConfig] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        """
        Initialize SpecKit.

        Args:
            project_path: Root directory of the project
            config: Full configuration (optional)
            llm_config: LLM-specific configuration (optional, overrides config.llm)

        The configuration is loaded with this precedence:
        1. Explicit config/llm_config arguments
        2. .speckit/config.yaml in project directory
        3. Environment variables
        4. Default values
        """
        project_path = Path(project_path).resolve()

        # Load or create configuration
        if config is not None:
            self.config = config
        else:
            self.config = SpecKitConfig.from_project(project_path)

        # Override LLM config if provided
        if llm_config is not None:
            self.config.llm = llm_config

        # Ensure project path is set
        self.config.project_path = project_path

        # Initialize components
        self._llm: Optional[LiteLLMProvider] = None
        self._storage: Optional[FileStorage] = None

        # Lazy-load core modules
        self._constitution_manager = None
        self._specification_builder = None
        self._clarification_engine = None
        self._technical_planner = None
        self._task_generator = None
        self._implementation_tracker = None
        self._consistency_analyzer = None
        self._artifact_generator = None

    @property
    def llm(self) -> LiteLLMProvider:
        """Get the LLM provider (lazy initialization)."""
        if self._llm is None:
            self._llm = LiteLLMProvider(self.config.llm)
        return self._llm

    @property
    def storage(self) -> FileStorage:
        """Get the storage backend (lazy initialization)."""
        if self._storage is None:
            self._storage = FileStorage(
                self.config.project_path,
                specs_dir=self.config.storage.specs_dir,
                base_dir=self.config.storage.base_dir,
            )
        return self._storage

    # =========================================================================
    # Constitution Phase
    # =========================================================================

    def constitution(
        self,
        project_name: str,
        principles: Optional[list[str]] = None,
        interactive: bool = False,
    ) -> Constitution:
        """
        Create or update project constitution.

        Args:
            project_name: Name for the project
            principles: Optional seed principles (LLM generates if not provided)
            interactive: If True, prompts for principle refinement

        Returns:
            Constitution model with project principles
        """
        from speckit.core.constitution import ConstitutionManager

        if self._constitution_manager is None:
            self._constitution_manager = ConstitutionManager(self.llm, self.storage)

        return self._constitution_manager.create(
            project_name=project_name,
            seed_principles=principles,
            interactive=interactive,
        )

    # =========================================================================
    # Specification Phase
    # =========================================================================

    def specify(
        self,
        feature_description: str,
        feature_id: Optional[str] = None,
    ) -> Specification:
        """
        Generate a feature specification from natural language.

        Args:
            feature_description: Natural language description of the feature
            feature_id: Optional custom ID (auto-generated if not provided)

        Returns:
            Specification model with user stories, requirements, etc.

        Example:
            >>> spec = kit.specify('''
            ...     Add user authentication with:
            ...     - Email/password login
            ...     - Password reset via email
            ...     - Session management with JWT
            ... ''')
        """
        from speckit.core.specification import SpecificationBuilder

        if self._specification_builder is None:
            self._specification_builder = SpecificationBuilder(self.llm, self.storage)

        # Load constitution for context if available
        constitution = self.storage.load_constitution()

        return self._specification_builder.generate(
            feature_description=feature_description,
            feature_id=feature_id,
            constitution=constitution,
            language=self.config.language,
        )

    async def specify_async(
        self,
        feature_description: str,
        feature_id: Optional[str] = None,
    ) -> Specification:
        """Async version of specify()."""
        from speckit.core.specification import SpecificationBuilder

        if self._specification_builder is None:
            self._specification_builder = SpecificationBuilder(self.llm, self.storage)

        constitution = self.storage.load_constitution()

        return await self._specification_builder.generate_async(
            feature_description=feature_description,
            feature_id=feature_id,
            constitution=constitution,
            language=self.config.language,
        )

    # =========================================================================
    # Clarification Phase
    # =========================================================================

    def clarify(
        self,
        specification: Specification,
        max_questions: int = 5,
    ) -> tuple[Specification, list[ClarificationQuestion]]:
        """
        Identify ambiguities and generate clarification questions.

        Args:
            specification: Specification to analyze
            max_questions: Maximum questions to generate

        Returns:
            Tuple of (updated spec, questions needing answers)
        """
        from speckit.core.clarifier import ClarificationEngine

        if self._clarification_engine is None:
            self._clarification_engine = ClarificationEngine(self.llm)

        return self._clarification_engine.clarify(
            specification=specification,
            max_questions=max_questions,
        )

    def apply_clarification(
        self,
        specification: Specification,
        question_id: str,
        answer: str,
    ) -> Specification:
        """
        Apply an answer to a clarification question.

        Args:
            specification: Specification to update
            question_id: ID of the question being answered
            answer: The answer to apply

        Returns:
            Updated specification with the clarification resolved
        """
        from speckit.core.clarifier import ClarificationEngine

        if self._clarification_engine is None:
            self._clarification_engine = ClarificationEngine(self.llm)

        return self._clarification_engine.apply_answer(
            specification=specification,
            question_id=question_id,
            answer=answer,
        )

    # =========================================================================
    # Planning Phase
    # =========================================================================

    def plan(
        self,
        specification: Specification,
        tech_stack: Optional[TechStack] = None,
    ) -> TechnicalPlan:
        """
        Generate technical implementation plan.

        Args:
            specification: Specification to plan for
            tech_stack: Optional constraints on technology choices

        Returns:
            TechnicalPlan model with architecture and components
        """
        from speckit.core.planner import TechnicalPlanner

        if self._technical_planner is None:
            self._technical_planner = TechnicalPlanner(self.llm, self.storage)

        # Load constitution for context
        constitution = self.storage.load_constitution()

        return self._technical_planner.plan(
            specification=specification,
            constitution=constitution,
            tech_stack=tech_stack,
            language=self.config.language,
        )

    async def plan_async(
        self,
        specification: Specification,
        tech_stack: Optional[TechStack] = None,
    ) -> TechnicalPlan:
        """Async version of plan()."""
        from speckit.core.planner import TechnicalPlanner

        if self._technical_planner is None:
            self._technical_planner = TechnicalPlanner(self.llm, self.storage)

        constitution = self.storage.load_constitution()

        return await self._technical_planner.plan_async(
            specification=specification,
            constitution=constitution,
            tech_stack=tech_stack,
            language=self.config.language,
        )

    # =========================================================================
    # Task Generation Phase
    # =========================================================================

    def tasks(
        self,
        plan: TechnicalPlan,
        parallel_friendly: bool = True,
    ) -> TaskBreakdown:
        """
        Generate implementation tasks from plan.

        Args:
            plan: Technical plan to break down
            parallel_friendly: If True, maximizes parallel task opportunities

        Returns:
            TaskBreakdown model with ordered tasks
        """
        from speckit.core.tasker import TaskGenerator

        if self._task_generator is None:
            self._task_generator = TaskGenerator(self.llm, self.storage)

        # Load specification for context
        spec = self.storage.load_specification(plan.feature_id)

        return self._task_generator.generate(
            plan=plan,
            specification=spec,
            parallel_friendly=parallel_friendly,
            language=self.config.language,
        )

    async def tasks_async(
        self,
        plan: TechnicalPlan,
        parallel_friendly: bool = True,
    ) -> TaskBreakdown:
        """Async version of tasks()."""
        from speckit.core.tasker import TaskGenerator

        if self._task_generator is None:
            self._task_generator = TaskGenerator(self.llm, self.storage)

        spec = self.storage.load_specification(plan.feature_id)

        return await self._task_generator.generate_async(
            plan=plan,
            specification=spec,
            parallel_friendly=parallel_friendly,
            language=self.config.language,
        )

    # =========================================================================
    # Analysis Phase
    # =========================================================================

    def analyze(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        tasks: TaskBreakdown,
    ) -> AnalysisReport:
        """
        Check consistency across all artifacts.

        Args:
            specification: Source specification
            plan: Implementation plan
            tasks: Task breakdown

        Returns:
            AnalysisReport with issues and recommendations
        """
        from speckit.core.analyzer import ConsistencyAnalyzer

        if self._consistency_analyzer is None:
            self._consistency_analyzer = ConsistencyAnalyzer(self.llm)

        return self._consistency_analyzer.analyze(
            specification=specification,
            plan=plan,
            tasks=tasks,
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def save(
        self,
        artifact: Constitution | Specification | TechnicalPlan | TaskBreakdown,
        feature_id: Optional[str] = None,
    ) -> Path:
        """
        Save an artifact to storage.

        Args:
            artifact: The artifact to save
            feature_id: Feature ID (required for spec/plan/tasks)

        Returns:
            Path to the saved file
        """
        if isinstance(artifact, Constitution):
            return self.storage.save_constitution(artifact)
        elif isinstance(artifact, Specification):
            fid = feature_id or artifact.feature_id
            return self.storage.save_specification(artifact, fid)
        elif isinstance(artifact, TechnicalPlan):
            fid = feature_id or artifact.feature_id
            return self.storage.save_plan(artifact, fid)
        elif isinstance(artifact, TaskBreakdown):
            fid = feature_id or artifact.feature_id
            return self.storage.save_tasks(artifact, fid)
        else:
            raise TypeError(f"Unknown artifact type: {type(artifact)}")

    def load_specification(self, feature_id: str) -> Optional[Specification]:
        """Load a specification by feature ID."""
        return self.storage.load_specification(feature_id)

    def load_plan(self, feature_id: str) -> Optional[TechnicalPlan]:
        """Load a plan by feature ID."""
        return self.storage.load_plan(feature_id)

    def load_tasks(self, feature_id: str) -> Optional[TaskBreakdown]:
        """Load tasks by feature ID."""
        return self.storage.load_tasks(feature_id)

    def list_features(self) -> list[str]:
        """List all features in the project."""
        return self.storage.list_features()

    # =========================================================================
    # Extended Artifacts Generation
    # =========================================================================

    def generate_data_model(
        self,
        specification: Specification,
        plan: TechnicalPlan,
    ) -> DataModel:
        """
        Generate database schema and data model.

        Args:
            specification: Feature specification
            plan: Technical implementation plan

        Returns:
            DataModel with entities and fields

        Example:
            >>> spec = kit.load_specification("001-user-auth")
            >>> plan = kit.load_plan("001-user-auth")
            >>> data_model = kit.generate_data_model(spec, plan)
            >>> kit.storage.save_data_model(data_model, "001-user-auth")
        """
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return self._artifact_generator.generate_data_model(
            specification=specification,
            plan=plan,
            language=self.config.language,
        )

    async def generate_data_model_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
    ) -> DataModel:
        """Async version of generate_data_model()."""
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return await self._artifact_generator.generate_data_model_async(
            specification=specification,
            plan=plan,
            language=self.config.language,
        )

    def generate_research(
        self,
        plan: TechnicalPlan,
    ) -> ResearchFindings:
        """
        Generate technology research and decision documentation.

        Args:
            plan: Technical implementation plan

        Returns:
            ResearchFindings with technology decisions

        Example:
            >>> plan = kit.load_plan("001-user-auth")
            >>> research = kit.generate_research(plan)
            >>> kit.storage.save_research(research, "001-user-auth")
        """
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return self._artifact_generator.generate_research(
            plan=plan,
            language=self.config.language,
        )

    async def generate_research_async(
        self,
        plan: TechnicalPlan,
    ) -> ResearchFindings:
        """Async version of generate_research()."""
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return await self._artifact_generator.generate_research_async(
            plan=plan,
            language=self.config.language,
        )

    def generate_api_contract(
        self,
        specification: Specification,
        plan: TechnicalPlan,
    ) -> APIContract:
        """
        Generate API specification with endpoints and schemas.

        Args:
            specification: Feature specification
            plan: Technical implementation plan

        Returns:
            APIContract with endpoint definitions

        Example:
            >>> spec = kit.load_specification("001-user-auth")
            >>> plan = kit.load_plan("001-user-auth")
            >>> contract = kit.generate_api_contract(spec, plan)
            >>> kit.storage.save_api_contract(contract, "001-user-auth")
        """
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return self._artifact_generator.generate_api_contract(
            specification=specification,
            plan=plan,
            language=self.config.language,
        )

    async def generate_api_contract_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
    ) -> APIContract:
        """Async version of generate_api_contract()."""
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return await self._artifact_generator.generate_api_contract_async(
            specification=specification,
            plan=plan,
            language=self.config.language,
        )

    def generate_checklist(
        self,
        specification: Specification,
    ) -> QualityChecklist:
        """
        Generate quality validation checklist for specification.

        Args:
            specification: Feature specification to validate

        Returns:
            QualityChecklist with validation items

        Example:
            >>> spec = kit.load_specification("001-user-auth")
            >>> checklist = kit.generate_checklist(spec)
            >>> kit.storage.save_checklist(checklist, "001-user-auth")
        """
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return self._artifact_generator.generate_checklist(
            specification=specification,
            language=self.config.language,
        )

    async def generate_checklist_async(
        self,
        specification: Specification,
    ) -> QualityChecklist:
        """Async version of generate_checklist()."""
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return await self._artifact_generator.generate_checklist_async(
            specification=specification,
            language=self.config.language,
        )

    def generate_quickstart(
        self,
        specification: Specification,
        plan: TechnicalPlan,
    ) -> QuickstartGuide:
        """
        Generate quickstart guide for developers.

        Args:
            specification: Feature specification
            plan: Technical implementation plan

        Returns:
            QuickstartGuide with setup instructions

        Example:
            >>> spec = kit.load_specification("001-user-auth")
            >>> plan = kit.load_plan("001-user-auth")
            >>> quickstart = kit.generate_quickstart(spec, plan)
            >>> kit.storage.save_quickstart(quickstart, "001-user-auth")
        """
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return self._artifact_generator.generate_quickstart(
            specification=specification,
            plan=plan,
            language=self.config.language,
        )

    async def generate_quickstart_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
    ) -> QuickstartGuide:
        """Async version of generate_quickstart()."""
        from speckit.core.artifacts import ArtifactGenerator

        if self._artifact_generator is None:
            self._artifact_generator = ArtifactGenerator(self.llm, self.storage)

        return await self._artifact_generator.generate_quickstart_async(
            specification=specification,
            plan=plan,
            language=self.config.language,
        )
