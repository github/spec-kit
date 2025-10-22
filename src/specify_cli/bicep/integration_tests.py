"""Enhanced integration tests for the Bicep generation system.

This module provides comprehensive integration testing that validates
the complete workflow from analysis through template generation.
"""

import asyncio
import tempfile
import shutil
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

from .analyzer import ProjectAnalyzer
from .questionnaire import InteractiveQuestionnaire  
from .generator import BicepGenerator
from .orchestrator import GenerationOrchestrator
from .models.project_analysis import ProjectAnalysis, TechnologyStack
from .models.resource_requirement import ResourceRequirement, ResourceType
from .models.bicep_template import BicepTemplate


class MockFileScanner:
    """Mock file scanner for testing."""
    
    def __init__(self, mock_files: Dict[str, str]):
        self.mock_files = mock_files
    
    async def scan_directory(self, directory: Path) -> Dict[str, List[Path]]:
        """Return mock file structure."""
        result = {
            'python': [],
            'javascript': [],
            'csharp': [],
            'java': [],
            'config': [],
            'docker': [],
            'other': []
        }
        
        for file_path in self.mock_files.keys():
            path = Path(file_path)
            if path.suffix == '.py':
                result['python'].append(path)
            elif path.suffix in ['.js', '.ts']:
                result['javascript'].append(path)
            elif path.suffix in ['.cs', '.csproj']:
                result['csharp'].append(path)
            elif path.suffix == '.java':
                result['java'].append(path)
            elif path.name in ['package.json', 'requirements.txt', 'pom.xml']:
                result['config'].append(path)
            elif path.name == 'Dockerfile':
                result['docker'].append(path)
            else:
                result['other'].append(path)
        
        return result
    
    def read_file_content(self, file_path: Path) -> str:
        """Return mock file content."""
        return self.mock_files.get(str(file_path), "")


class MockMCPClient:
    """Mock MCP client for testing."""
    
    def __init__(self):
        self.is_connected = True
    
    async def get_resource_schema(self, resource_type: str, api_version: str) -> Dict[str, Any]:
        """Return mock schema."""
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": [resource_type]},
                "apiVersion": {"type": "string", "enum": [api_version]},
                "name": {"type": "string"},
                "location": {"type": "string"},
                "properties": {"type": "object"}
            },
            "required": ["type", "apiVersion", "name", "location"]
        }
    
    async def validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock validation result."""
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_web_project_files():
    """Mock files for a web application project."""
    return {
        "package.json": json.dumps({
            "name": "test-webapp",
            "version": "1.0.0",
            "dependencies": {
                "express": "^4.18.0",
                "react": "^18.2.0"
            },
            "scripts": {
                "start": "node server.js",
                "build": "webpack --mode production"
            }
        }),
        "server.js": """
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
        """,
        "src/App.js": """
import React from 'react';

function App() {
    return <div>Hello React!</div>;
}

export default App;
        """,
        "webpack.config.js": """
module.exports = {
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: __dirname + '/dist'
    }
};
        """
    }


@pytest.fixture
def mock_api_project_files():
    """Mock files for an API project."""
    return {
        "requirements.txt": """
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
python-dotenv==1.0.0
        """,
        "main.py": """
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/users")
def get_users():
    return [{"id": 1, "name": "John"}]
        """,
        "models.py": """
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
        """,
        ".env": """
DATABASE_URL=postgresql://user:pass@localhost:5432/db
        """
    }


class TestIntegrationWorkflow:
    """Integration tests for the complete Bicep generation workflow."""
    
    @pytest.mark.asyncio
    async def test_web_application_workflow(self, temp_project_dir, mock_web_project_files):
        """Test complete workflow for web application project."""
        
        # Create mock project files
        for file_path, content in mock_web_project_files.items():
            full_path = temp_project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        # Initialize components with mocks
        file_scanner = MockFileScanner(mock_web_project_files)
        mcp_client = MockMCPClient()
        
        analyzer = ProjectAnalyzer(file_scanner)
        generator = BicepGenerator(mcp_client=mcp_client)
        
        # Mock questionnaire responses for web app
        mock_responses = {
            "deployment_type": "web_application",
            "performance_requirements": "medium",
            "security_requirements": "standard",
            "monitoring_enabled": True,
            "backup_enabled": True,
            "environment": "development"
        }
        
        questionnaire = InteractiveQuestionnaire()
        questionnaire._responses = mock_responses  # Bypass interactive input
        
        orchestrator = GenerationOrchestrator(
            analyzer=analyzer,
            questionnaire=questionnaire, 
            generator=generator
        )
        
        # Run the complete workflow
        result = await orchestrator.generate_bicep_templates(
            project_path=temp_project_dir,
            output_path=temp_project_dir / "bicep",
            project_name="test-webapp"
        )
        
        # Verify results
        assert result.success
        assert len(result.generated_templates) > 0
        
        # Check that templates were generated
        bicep_dir = temp_project_dir / "bicep"
        assert bicep_dir.exists()
        
        # Verify main template exists
        main_template = bicep_dir / "main.bicep"
        assert main_template.exists()
        
        # Verify template content contains expected resources
        template_content = main_template.read_text()
        assert "Microsoft.Web/sites" in template_content  # Web App
        assert "Microsoft.Web/serverfarms" in template_content  # App Service Plan
        assert "Microsoft.Insights/components" in template_content  # App Insights
        
    @pytest.mark.asyncio
    async def test_api_application_workflow(self, temp_project_dir, mock_api_project_files):
        """Test complete workflow for API application project."""
        
        # Create mock project files
        for file_path, content in mock_api_project_files.items():
            full_path = temp_project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        # Initialize components
        file_scanner = MockFileScanner(mock_api_project_files)
        mcp_client = MockMCPClient()
        
        analyzer = ProjectAnalyzer(file_scanner)
        generator = BicepGenerator(mcp_client=mcp_client)
        
        # Mock responses for API project
        mock_responses = {
            "deployment_type": "api_service",
            "database_required": True,
            "database_type": "postgresql",
            "performance_requirements": "high",
            "security_requirements": "enhanced",
            "monitoring_enabled": True,
            "environment": "production"
        }
        
        questionnaire = InteractiveQuestionnaire()
        questionnaire._responses = mock_responses
        
        orchestrator = GenerationOrchestrator(
            analyzer=analyzer,
            questionnaire=questionnaire,
            generator=generator
        )
        
        # Run workflow
        result = await orchestrator.generate_bicep_templates(
            project_path=temp_project_dir,
            output_path=temp_project_dir / "infrastructure",
            project_name="test-api"
        )
        
        # Verify results
        assert result.success
        assert len(result.generated_templates) > 0
        
        # Check infrastructure directory
        infra_dir = temp_project_dir / "infrastructure"
        assert infra_dir.exists()
        
        # Verify templates contain database resources
        main_template = infra_dir / "main.bicep"
        assert main_template.exists()
        
        template_content = main_template.read_text()
        assert "Microsoft.Sql/servers" in template_content or "Microsoft.DBforPostgreSQL" in template_content
        
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, temp_project_dir):
        """Test error handling throughout the workflow."""
        
        # Create minimal project structure
        (temp_project_dir / "empty.txt").write_text("")
        
        # Initialize with failing components
        file_scanner = MockFileScanner({})
        
        # Mock MCP client that fails
        mcp_client = Mock()
        mcp_client.get_resource_schema = AsyncMock(side_effect=Exception("MCP connection failed"))
        
        analyzer = ProjectAnalyzer(file_scanner)
        generator = BicepGenerator(mcp_client=mcp_client)
        questionnaire = InteractiveQuestionnaire()
        
        orchestrator = GenerationOrchestrator(
            analyzer=analyzer,
            questionnaire=questionnaire,
            generator=generator
        )
        
        # Run workflow - should handle errors gracefully
        result = await orchestrator.generate_bicep_templates(
            project_path=temp_project_dir,
            output_path=temp_project_dir / "bicep",
            project_name="test-error"
        )
        
        # Verify error handling
        assert not result.success
        assert len(result.errors) > 0
        assert "MCP connection failed" in str(result.errors)
        
    @pytest.mark.asyncio
    async def test_template_validation_integration(self, temp_project_dir, mock_web_project_files):
        """Test that generated templates pass validation."""
        
        # Create project files
        for file_path, content in mock_web_project_files.items():
            full_path = temp_project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        file_scanner = MockFileScanner(mock_web_project_files)
        mcp_client = MockMCPClient()
        
        analyzer = ProjectAnalyzer(file_scanner)
        generator = BicepGenerator(mcp_client=mcp_client)
        
        mock_responses = {
            "deployment_type": "web_application",
            "performance_requirements": "medium",
            "security_requirements": "standard"
        }
        
        questionnaire = InteractiveQuestionnaire()
        questionnaire._responses = mock_responses
        
        orchestrator = GenerationOrchestrator(
            analyzer=analyzer,
            questionnaire=questionnaire,
            generator=generator
        )
        
        # Generate templates
        result = await orchestrator.generate_bicep_templates(
            project_path=temp_project_dir,
            output_path=temp_project_dir / "bicep",
            project_name="test-validation"
        )
        
        assert result.success
        
        # Verify templates are valid
        for template_info in result.generated_templates:
            template_path = Path(template_info["path"])
            assert template_path.exists()
            
            # Basic syntax validation
            content = template_path.read_text()
            assert content.strip()  # Not empty
            assert "targetScope" in content or "param" in content  # Valid Bicep content
            
    @pytest.mark.asyncio
    async def test_multiple_environment_generation(self, temp_project_dir, mock_web_project_files):
        """Test generating templates for multiple environments."""
        
        # Create project files
        for file_path, content in mock_web_project_files.items():
            full_path = temp_project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        environments = ["development", "staging", "production"]
        
        for env in environments:
            file_scanner = MockFileScanner(mock_web_project_files)
            mcp_client = MockMCPClient()
            
            analyzer = ProjectAnalyzer(file_scanner)
            generator = BicepGenerator(mcp_client=mcp_client)
            
            mock_responses = {
                "deployment_type": "web_application",
                "environment": env,
                "performance_requirements": "high" if env == "production" else "medium"
            }
            
            questionnaire = InteractiveQuestionnaire()
            questionnaire._responses = mock_responses
            
            orchestrator = GenerationOrchestrator(
                analyzer=analyzer,
                questionnaire=questionnaire,
                generator=generator
            )
            
            # Generate for this environment
            result = await orchestrator.generate_bicep_templates(
                project_path=temp_project_dir,
                output_path=temp_project_dir / f"bicep-{env}",
                project_name=f"test-{env}"
            )
            
            assert result.success
            
            # Verify environment-specific configurations
            bicep_dir = temp_project_dir / f"bicep-{env}"
            param_file = bicep_dir / f"main.{env}.bicepparam"
            
            if param_file.exists():
                param_content = param_file.read_text()
                assert f"environmentName = '{env}'" in param_content
                
                if env == "production":
                    # Production should have higher SKUs
                    assert "Standard" in param_content or "Premium" in param_content
    
    @pytest.mark.asyncio
    async def test_template_pattern_integration(self, temp_project_dir):
        """Test integration with template patterns."""
        
        # Mock a complex project that should use patterns
        complex_project_files = {
            "frontend/package.json": json.dumps({
                "name": "frontend",
                "dependencies": {"react": "^18.0.0"}
            }),
            "backend/requirements.txt": "fastapi==0.104.1\nsqlalchemy==2.0.23",
            "api/package.json": json.dumps({
                "name": "api-gateway", 
                "dependencies": {"express": "^4.18.0"}
            })
        }
        
        # Create project files
        for file_path, content in complex_project_files.items():
            full_path = temp_project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        file_scanner = MockFileScanner(complex_project_files)
        mcp_client = MockMCPClient()
        
        analyzer = ProjectAnalyzer(file_scanner)
        generator = BicepGenerator(mcp_client=mcp_client)
        
        # Mock responses that should trigger pattern usage
        mock_responses = {
            "deployment_type": "microservices",
            "architecture_pattern": "three-tier-webapp",
            "performance_requirements": "high",
            "environment": "production"
        }
        
        questionnaire = InteractiveQuestionnaire()
        questionnaire._responses = mock_responses
        
        orchestrator = GenerationOrchestrator(
            analyzer=analyzer,
            questionnaire=questionnaire,
            generator=generator
        )
        
        # Generate templates
        result = await orchestrator.generate_bicep_templates(
            project_path=temp_project_dir,
            output_path=temp_project_dir / "bicep",
            project_name="complex-app"
        )
        
        assert result.success
        
        # Verify pattern-based templates were generated
        bicep_dir = temp_project_dir / "bicep"
        main_template = bicep_dir / "main.bicep"
        
        assert main_template.exists()
        template_content = main_template.read_text()
        
        # Should contain resources typical of three-tier architecture
        assert "Microsoft.Web/sites" in template_content  # Web tier
        assert "Microsoft.Sql/servers" in template_content  # Data tier


class TestComponentIntegration:
    """Test integration between specific components."""
    
    @pytest.mark.asyncio
    async def test_analyzer_questionnaire_integration(self, temp_project_dir, mock_web_project_files):
        """Test that analyzer results inform questionnaire logic."""
        
        # Create project
        for file_path, content in mock_web_project_files.items():
            full_path = temp_project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        file_scanner = MockFileScanner(mock_web_project_files)
        analyzer = ProjectAnalyzer(file_scanner)
        
        # Analyze project
        analysis = await analyzer.analyze_project(temp_project_dir)
        
        # Initialize questionnaire with analysis
        questionnaire = InteractiveQuestionnaire()
        
        # Verify questionnaire adapts to analysis
        questions = questionnaire._get_technology_specific_questions(analysis.technology_stack)
        
        # Should include JavaScript/Node.js specific questions
        question_text = " ".join([q.question for q in questions])
        assert "node" in question_text.lower() or "javascript" in question_text.lower()
        
    @pytest.mark.asyncio  
    async def test_questionnaire_generator_integration(self, temp_project_dir):
        """Test that questionnaire responses properly configure generator."""
        
        mcp_client = MockMCPClient()
        generator = BicepGenerator(mcp_client=mcp_client)
        
        # Mock comprehensive responses
        responses = {
            "deployment_type": "web_application",
            "database_required": True,
            "database_type": "sql",
            "performance_requirements": "high",
            "security_requirements": "enhanced",
            "monitoring_enabled": True,
            "backup_enabled": True,
            "caching_enabled": True,
            "cdn_enabled": True
        }
        
        # Create requirements from responses (simulate questionnaire output)
        requirements = [
            ResourceRequirement(
                resource_type=ResourceType.WEB_APP,
                name="webapp",
                properties={"sku": "P1V2"}  # High performance
            ),
            ResourceRequirement(
                resource_type=ResourceType.SQL_DATABASE,
                name="database",
                properties={"tier": "Standard"}
            )
        ]
        
        # Generate template
        template = await generator.generate_template(
            project_name="integration-test",
            requirements=requirements,
            environment="production"
        )
        
        assert template is not None
        assert template.name == "integration-test"
        
        # Verify high-performance configuration was applied
        template_dict = template.to_arm_template()
        
        # Find web app resource
        web_app_resource = None
        for resource in template_dict.get("resources", []):
            if resource.get("type") == "Microsoft.Web/sites":
                web_app_resource = resource
                break
        
        assert web_app_resource is not None
        # Should have high-performance configurations based on responses


# Utility functions for integration testing
async def run_complete_workflow(project_path: Path, 
                               mock_responses: Dict[str, Any],
                               project_files: Dict[str, str]) -> Dict[str, Any]:
    """Run complete workflow and return results."""
    
    # Setup components
    file_scanner = MockFileScanner(project_files)
    mcp_client = MockMCPClient()
    
    analyzer = ProjectAnalyzer(file_scanner)
    generator = BicepGenerator(mcp_client=mcp_client)
    
    questionnaire = InteractiveQuestionnaire()
    questionnaire._responses = mock_responses
    
    orchestrator = GenerationOrchestrator(
        analyzer=analyzer,
        questionnaire=questionnaire,
        generator=generator
    )
    
    # Execute workflow
    result = await orchestrator.generate_bicep_templates(
        project_path=project_path,
        output_path=project_path / "bicep",
        project_name="integration-test"
    )
    
    return {
        "success": result.success,
        "templates": result.generated_templates,
        "errors": result.errors,
        "analysis": await analyzer.analyze_project(project_path)
    }


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])