"""Interactive questionnaire for collecting user requirements.

This module implements an interactive questionnaire system that collects user preferences,
requirements, and configuration details for Bicep template generation.
"""

import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import json
import logging

from .models.project_analysis import ProjectAnalysisResult, ProjectType, FrameworkType
from .models.resource_requirement import ResourceRequirement, ResourceType, PriorityLevel
from .models.deployment_config import (
    DeploymentConfiguration, EnvironmentConfig, AzureLocation,
    DeploymentTarget, DeploymentMode, ParameterValue
)

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of questions that can be asked."""
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    TEXT_INPUT = "text_input"
    NUMBER_INPUT = "number_input"
    BOOLEAN = "boolean"
    LOCATION_SELECT = "location_select"
    CONFIRMATION = "confirmation"


@dataclass
class QuestionOption:
    """Represents an option for choice questions."""
    value: str
    display_text: str
    description: Optional[str] = None
    recommended: bool = False
    
    def __str__(self) -> str:
        prefix = "🌟 " if self.recommended else "   "
        suffix = f" - {self.description}" if self.description else ""
        return f"{prefix}{self.display_text}{suffix}"


@dataclass
class Question:
    """Represents a single question in the questionnaire."""
    id: str
    question_text: str
    question_type: QuestionType
    options: List[QuestionOption] = field(default_factory=list)
    default_value: Any = None
    required: bool = True
    depends_on: Optional[Dict[str, Any]] = None  # Conditional questions
    validation_fn: Optional[Callable[[Any], bool]] = None
    error_message: Optional[str] = None
    help_text: Optional[str] = None
    
    def is_applicable(self, answers: Dict[str, Any]) -> bool:
        """Check if this question should be asked based on previous answers."""
        if not self.depends_on:
            return True
        
        for key, expected_value in self.depends_on.items():
            if key not in answers:
                return False
            
            actual_value = answers[key]
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    def validate_answer(self, answer: Any) -> bool:
        """Validate an answer against this question's constraints."""
        if self.required and (answer is None or answer == ""):
            return False
        
        if self.validation_fn:
            return self.validation_fn(answer)
        
        if self.question_type == QuestionType.SINGLE_CHOICE:
            valid_values = [opt.value for opt in self.options]
            return answer in valid_values
        
        if self.question_type == QuestionType.MULTI_CHOICE:
            if not isinstance(answer, list):
                return False
            valid_values = [opt.value for opt in self.options]
            return all(val in valid_values for val in answer)
        
        return True


class UserRequirementsQuestionnaire:
    """Interactive questionnaire for collecting user requirements and preferences."""
    
    def __init__(self, analysis_result: ProjectAnalysisResult):
        """Initialize questionnaire with project analysis results."""
        self.analysis_result = analysis_result
        self.answers: Dict[str, Any] = {}
        self.questions: List[Question] = []
        self._setup_questions()
    
    def _setup_questions(self) -> None:
        """Set up the questionnaire based on project analysis."""
        
        # Project confirmation
        self.questions.append(Question(
            id="project_confirmation",
            question_text=f"We detected your project as: {self.analysis_result.project_type.value} using {', '.join([f.value for f in self.analysis_result.detected_frameworks])}. Is this correct?",
            question_type=QuestionType.BOOLEAN,
            default_value=True,
            help_text="This affects which Azure resources we'll recommend."
        ))
        
        # Project type override if needed
        self.questions.append(Question(
            id="project_type_override",
            question_text="What type of project is this?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption(ptype.value, ptype.value.replace('_', ' ').title(), 
                             recommended=(ptype == self.analysis_result.project_type))
                for ptype in ProjectType
            ],
            depends_on={"project_confirmation": False}
        ))
        
        # Environment configuration
        self.questions.append(Question(
            id="environments",
            question_text="Which environments do you want to set up?",
            question_type=QuestionType.MULTI_CHOICE,
            options=[
                QuestionOption("dev", "Development", "Development and testing environment", True),
                QuestionOption("staging", "Staging", "Pre-production environment for final testing"),
                QuestionOption("prod", "Production", "Live production environment", True)
            ],
            default_value=["dev", "prod"]
        ))
        
        # Azure location
        locations = AzureLocation.get_common_locations()
        self.questions.append(Question(
            id="primary_location",
            question_text="Which Azure region should be your primary location?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption(loc.name, loc.display_name, loc.regional_display_name,
                             recommended=(loc.name == "eastus"))
                for loc in locations
            ],
            default_value="eastus"
        ))
        
        # Multi-region deployment
        self.questions.append(Question(
            id="multi_region",
            question_text="Do you need multi-region deployment for high availability?",
            question_type=QuestionType.BOOLEAN,
            default_value=False,
            help_text="This increases cost but provides better disaster recovery."
        ))
        
        # Secondary location
        self.questions.append(Question(
            id="secondary_location",
            question_text="Choose a secondary region:",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption(loc.name, loc.display_name, loc.regional_display_name)
                for loc in locations
            ],
            depends_on={"multi_region": True}
        ))
        
        # Database requirements
        if self._needs_database():
            self.questions.append(Question(
                id="database_type",
                question_text="What type of database do you need?",
                question_type=QuestionType.SINGLE_CHOICE,
                options=[
                    QuestionOption("sql", "Azure SQL Database", "Managed SQL Server database", True),
                    QuestionOption("postgresql", "Azure Database for PostgreSQL", "Managed PostgreSQL database"),
                    QuestionOption("mysql", "Azure Database for MySQL", "Managed MySQL database"),
                    QuestionOption("cosmos", "Azure Cosmos DB", "NoSQL database with global distribution"),
                    QuestionOption("none", "No database needed", "Skip database setup")
                ],
                default_value="sql"
            ))
        
        # Caching requirements
        self.questions.append(Question(
            id="enable_caching",
            question_text="Do you need caching for better performance?",
            question_type=QuestionType.BOOLEAN,
            default_value=True,
            help_text="Azure Cache for Redis improves application performance."
        ))
        
        # Monitoring and diagnostics
        self.questions.append(Question(
            id="enable_monitoring",
            question_text="Enable Application Insights for monitoring and diagnostics?",
            question_type=QuestionType.BOOLEAN,
            default_value=True,
            help_text="Recommended for production applications."
        ))
        
        # Security requirements
        self.questions.append(Question(
            id="security_level",
            question_text="What security level do you need?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption("basic", "Basic", "Standard security features"),
                QuestionOption("enhanced", "Enhanced", "Additional security hardening", True),
                QuestionOption("enterprise", "Enterprise", "Maximum security with compliance features")
            ],
            default_value="enhanced"
        ))
        
        # SSL/TLS configuration
        self.questions.append(Question(
            id="ssl_configuration",
            question_text="How do you want to handle SSL certificates?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption("managed", "Azure Managed Certificates", "Free SSL certificates from Azure", True),
                QuestionOption("custom", "Custom Certificate", "Upload your own SSL certificate"),
                QuestionOption("none", "No SSL", "HTTP only (not recommended for production)")
            ],
            default_value="managed"
        ))
        
        # Scaling requirements
        self.questions.append(Question(
            id="auto_scaling",
            question_text="Do you need automatic scaling based on load?",
            question_type=QuestionType.BOOLEAN,
            default_value=True,
            help_text="Automatically adjusts resources based on traffic."
        ))
        
        # Backup requirements
        self.questions.append(Question(
            id="backup_retention",
            question_text="How long should backups be retained?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption("7", "7 days", "Short-term backup retention"),
                QuestionOption("30", "30 days", "Standard backup retention", True),
                QuestionOption("90", "90 days", "Extended backup retention"),
                QuestionOption("365", "1 year", "Long-term backup retention")
            ],
            default_value="30"
        ))
        
        # Cost optimization
        self.questions.append(Question(
            id="cost_optimization",
            question_text="What's your priority for cost optimization?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=[
                QuestionOption("low_cost", "Minimize Cost", "Optimize for lowest cost"),
                QuestionOption("balanced", "Balanced", "Balance cost and performance", True),
                QuestionOption("performance", "Maximize Performance", "Optimize for best performance")
            ],
            default_value="balanced"
        ))
        
        # Compliance requirements
        self.questions.append(Question(
            id="compliance_frameworks",
            question_text="Do you need to comply with specific frameworks?",
            question_type=QuestionType.MULTI_CHOICE,
            options=[
                QuestionOption("none", "No specific requirements", "Standard configuration"),
                QuestionOption("gdpr", "GDPR", "General Data Protection Regulation"),
                QuestionOption("hipaa", "HIPAA", "Health Insurance Portability and Accountability Act"),
                QuestionOption("sox", "SOX", "Sarbanes-Oxley Act"),
                QuestionOption("pci", "PCI DSS", "Payment Card Industry Data Security Standard")
            ],
            default_value=["none"],
            required=False
        ))
        
        # Custom domain
        self.questions.append(Question(
            id="custom_domain",
            question_text="Do you have a custom domain name?",
            question_type=QuestionType.TEXT_INPUT,
            required=False,
            help_text="e.g., www.myapp.com (leave empty if you don't have one)"
        ))
        
        # Final confirmation
        self.questions.append(Question(
            id="final_confirmation",
            question_text="Ready to generate your Azure Bicep templates?",
            question_type=QuestionType.CONFIRMATION,
            default_value=True
        ))
    
    def _needs_database(self) -> bool:
        """Check if the project likely needs a database."""
        backend_frameworks = [FrameworkType.ASP_NET_CORE, FrameworkType.DJANGO, 
                            FrameworkType.SPRING_BOOT, FrameworkType.EXPRESS_JS,
                            FrameworkType.FLASK, FrameworkType.FASTAPI]
        
        return (self.analysis_result.project_type in [ProjectType.WEB_APPLICATION, 
                                                     ProjectType.FULL_STACK_APPLICATION, 
                                                     ProjectType.API_SERVICE] or
                any(fw in self.analysis_result.detected_frameworks for fw in backend_frameworks))
    
    async def run_interactive_questionnaire(self, 
                                          input_handler: Optional[Callable[[str], str]] = None,
                                          output_handler: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Run the interactive questionnaire."""
        if not input_handler:
            input_handler = input
        if not output_handler:
            output_handler = print
        
        output_handler("\n🚀 Azure Bicep Template Configuration")
        output_handler("=" * 50)
        output_handler(f"Project: {self.analysis_result.project_path.name}")
        output_handler(f"Type: {self.analysis_result.project_type.value}")
        output_handler(f"Frameworks: {', '.join([f.value for f in self.analysis_result.detected_frameworks])}")
        output_handler(f"Confidence: {self.analysis_result.confidence_score:.1%}")
        output_handler("")
        
        for i, question in enumerate(self.questions, 1):
            if not question.is_applicable(self.answers):
                continue
            
            output_handler(f"\n📋 Question {i}/{len(self.questions)}")
            output_handler("-" * 30)
            
            if question.help_text:
                output_handler(f"ℹ️  {question.help_text}")
            
            answer = await self._ask_question(question, input_handler, output_handler)
            self.answers[question.id] = answer
        
        output_handler("\n✅ Configuration complete!")
        return self.answers
    
    async def _ask_question(self, 
                          question: Question, 
                          input_handler: Callable[[str], str],
                          output_handler: Callable[[str], None]) -> Any:
        """Ask a single question and get the answer."""
        while True:
            output_handler(f"\n{question.question_text}")
            
            if question.question_type == QuestionType.SINGLE_CHOICE:
                return await self._handle_single_choice(question, input_handler, output_handler)
            
            elif question.question_type == QuestionType.MULTI_CHOICE:
                return await self._handle_multi_choice(question, input_handler, output_handler)
            
            elif question.question_type == QuestionType.BOOLEAN:
                return await self._handle_boolean(question, input_handler, output_handler)
            
            elif question.question_type == QuestionType.TEXT_INPUT:
                return await self._handle_text_input(question, input_handler, output_handler)
            
            elif question.question_type == QuestionType.NUMBER_INPUT:
                return await self._handle_number_input(question, input_handler, output_handler)
            
            elif question.question_type == QuestionType.CONFIRMATION:
                return await self._handle_confirmation(question, input_handler, output_handler)
            
            else:
                output_handler(f"❌ Unsupported question type: {question.question_type}")
                return question.default_value
    
    async def _handle_single_choice(self, 
                                  question: Question, 
                                  input_handler: Callable[[str], str],
                                  output_handler: Callable[[str], None]) -> str:
        """Handle single choice questions."""
        for i, option in enumerate(question.options, 1):
            output_handler(f"  {i}. {option}")
        
        default_index = None
        if question.default_value:
            for i, option in enumerate(question.options):
                if option.value == question.default_value:
                    default_index = i + 1
                    break
        
        prompt = f"\nEnter choice (1-{len(question.options)})"
        if default_index:
            prompt += f" [default: {default_index}]"
        prompt += ": "
        
        while True:
            try:
                response = input_handler(prompt).strip()
                
                if not response and default_index:
                    return question.options[default_index - 1].value
                
                choice_index = int(response) - 1
                if 0 <= choice_index < len(question.options):
                    return question.options[choice_index].value
                else:
                    output_handler(f"❌ Please enter a number between 1 and {len(question.options)}")
            except ValueError:
                output_handler("❌ Please enter a valid number")
    
    async def _handle_multi_choice(self, 
                                 question: Question, 
                                 input_handler: Callable[[str], str],
                                 output_handler: Callable[[str], None]) -> List[str]:
        """Handle multiple choice questions."""
        for i, option in enumerate(question.options, 1):
            output_handler(f"  {i}. {option}")
        
        output_handler(f"\nEnter multiple choices separated by commas (e.g., 1,3,5)")
        if question.default_value:
            default_display = []
            for val in question.default_value:
                for i, option in enumerate(question.options):
                    if option.value == val:
                        default_display.append(str(i + 1))
                        break
            output_handler(f"Default: {','.join(default_display)}")
        
        while True:
            try:
                response = input_handler("Your choices: ").strip()
                
                if not response and question.default_value:
                    return question.default_value
                
                if not response:
                    return []
                
                indices = [int(x.strip()) - 1 for x in response.split(',')]
                if all(0 <= i < len(question.options) for i in indices):
                    return [question.options[i].value for i in indices]
                else:
                    output_handler(f"❌ Please enter numbers between 1 and {len(question.options)}")
            except ValueError:
                output_handler("❌ Please enter valid numbers separated by commas")
    
    async def _handle_boolean(self, 
                            question: Question, 
                            input_handler: Callable[[str], str],
                            output_handler: Callable[[str], None]) -> bool:
        """Handle boolean questions."""
        default_text = "Y" if question.default_value else "N"
        prompt = f"(y/N) [default: {default_text}]: "
        
        while True:
            response = input_handler(prompt).strip().lower()
            
            if not response:
                return question.default_value
            
            if response in ['y', 'yes', 'true', '1']:
                return True
            elif response in ['n', 'no', 'false', '0']:
                return False
            else:
                output_handler("❌ Please enter 'y' for yes or 'n' for no")
    
    async def _handle_text_input(self, 
                               question: Question, 
                               input_handler: Callable[[str], str],
                               output_handler: Callable[[str], None]) -> str:
        """Handle text input questions."""
        prompt = "Enter text"
        if question.default_value:
            prompt += f" [default: {question.default_value}]"
        prompt += ": "
        
        while True:
            response = input_handler(prompt).strip()
            
            if not response and question.default_value:
                return question.default_value
            
            if question.validate_answer(response):
                return response
            else:
                error_msg = question.error_message or "Invalid input"
                output_handler(f"❌ {error_msg}")
    
    async def _handle_number_input(self, 
                                 question: Question, 
                                 input_handler: Callable[[str], str],
                                 output_handler: Callable[[str], None]) -> Union[int, float]:
        """Handle number input questions."""
        prompt = "Enter number"
        if question.default_value is not None:
            prompt += f" [default: {question.default_value}]"
        prompt += ": "
        
        while True:
            try:
                response = input_handler(prompt).strip()
                
                if not response and question.default_value is not None:
                    return question.default_value
                
                # Try int first, then float
                try:
                    value = int(response)
                except ValueError:
                    value = float(response)
                
                if question.validate_answer(value):
                    return value
                else:
                    error_msg = question.error_message or "Invalid number"
                    output_handler(f"❌ {error_msg}")
            except ValueError:
                output_handler("❌ Please enter a valid number")
    
    async def _handle_confirmation(self, 
                                 question: Question, 
                                 input_handler: Callable[[str], str],
                                 output_handler: Callable[[str], None]) -> bool:
        """Handle confirmation questions."""
        output_handler("\n📋 Configuration Summary:")
        output_handler("-" * 40)
        
        # Show summary of answers
        for key, value in self.answers.items():
            if key != "final_confirmation":
                display_key = key.replace('_', ' ').title()
                display_value = value
                if isinstance(value, list):
                    display_value = ", ".join(str(v) for v in value)
                elif isinstance(value, bool):
                    display_value = "Yes" if value else "No"
                
                output_handler(f"  {display_key}: {display_value}")
        
        return await self._handle_boolean(question, input_handler, output_handler)
    
    def create_deployment_configuration(self) -> DeploymentConfiguration:
        """Create deployment configuration from questionnaire answers."""
        # Basic configuration
        config = DeploymentConfiguration(
            configuration_name=f"{self.analysis_result.project_path.name}-deployment",
            project_name=self.analysis_result.project_path.name,
            target=DeploymentTarget.RESOURCE_GROUP,
            deployment_mode=DeploymentMode.INCREMENTAL,
            main_template_path=Path("main.bicep")
        )
        
        # Add environments
        environments = self.answers.get("environments", ["dev", "prod"])
        primary_location = self.answers.get("primary_location", "eastus")
        
        for env_name in environments:
            env_config = EnvironmentConfig(
                name=env_name,
                display_name=env_name.title(),
                location=primary_location
            )
            
            # Environment-specific settings
            if env_name == "prod":
                env_config.enable_backup = True
                env_config.enable_auto_scaling = self.answers.get("auto_scaling", True)
            
            # Security settings
            security_level = self.answers.get("security_level", "enhanced")
            env_config.require_https = security_level != "basic"
            env_config.enable_rbac = security_level in ["enhanced", "enterprise"]
            
            # Compliance
            compliance = self.answers.get("compliance_frameworks", [])
            if "none" not in compliance:
                env_config.compliance_frameworks = compliance
            
            config.add_environment(env_config)
        
        # Set default environment
        if "dev" in environments:
            config.default_environment = "dev"
        else:
            config.default_environment = environments[0]
        
        return config
    
    def get_resource_requirements_override(self) -> List[ResourceRequirement]:
        """Get modified resource requirements based on user answers."""
        requirements = []
        
        # Database requirements
        db_type = self.answers.get("database_type")
        if db_type and db_type != "none":
            db_resource_map = {
                "sql": ResourceType.SQL_DATABASE,
                "postgresql": ResourceType.POSTGRESQL,
                "mysql": ResourceType.MYSQL,
                "cosmos": ResourceType.COSMOS_DB
            }
            
            if db_type in db_resource_map:
                requirements.append(ResourceRequirement(
                    resource_type=db_resource_map[db_type],
                    name=f"{db_type}-database",
                    priority=PriorityLevel.HIGH,
                    justification="User-selected database type"
                ))
        
        # Caching
        if self.answers.get("enable_caching", True):
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.REDIS_CACHE,
                name="redis-cache",
                priority=PriorityLevel.MEDIUM,
                justification="User requested caching"
            ))
        
        # Monitoring
        if self.answers.get("enable_monitoring", True):
            requirements.append(ResourceRequirement(
                resource_type=ResourceType.APPLICATION_INSIGHTS,
                name="app-insights",
                priority=PriorityLevel.HIGH,
                justification="User requested monitoring"
            ))
        
        return requirements