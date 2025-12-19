"""
Configuration management for spec-kit.

This module provides configuration models using Pydantic Settings,
supporting environment variables, YAML config files, and programmatic overrides.

Configuration precedence (highest to lowest):
1. Programmatic overrides (passed to constructor)
2. Config file (.speckit/config.yaml)
3. Environment variables
4. Default values
"""

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM provider configuration via Pydantic Settings."""

    model_config = SettingsConfigDict(
        env_prefix="SPECKIT_",
        env_file=".env",
        extra="ignore",
    )

    model: str = Field(default="gpt-4o-mini", description="LiteLLM model identifier")
    api_key: Optional[str] = Field(default=None, description="API key override (uses env vars by default)")
    api_base: Optional[str] = Field(default=None, description="Custom API endpoint")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, gt=0, description="Maximum tokens in response")
    timeout: int = Field(default=120, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    fallback_models: list[str] = Field(
        default_factory=lambda: ["gpt-4o-mini", "claude-3-haiku-20240307"],
        description="Fallback models to try on failure",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for LiteLLM."""
        d = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }
        if self.api_key:
            d["api_key"] = self.api_key
        if self.api_base:
            d["api_base"] = self.api_base
        return d


class StorageConfig(BaseSettings):
    """Artifact storage configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SPECKIT_STORAGE_",
        extra="ignore",
    )

    backend: Literal["file"] = Field(default="file", description="Storage backend type")
    base_dir: str = Field(default=".speckit", description="Project-relative config directory")
    specs_dir: str = Field(default="specs", description="Feature specifications directory")


class SpecKitConfig(BaseSettings):
    """Main configuration container."""

    model_config = SettingsConfigDict(
        env_prefix="SPECKIT_",
        extra="ignore",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    project_path: Path = Field(default_factory=Path.cwd)
    language: str = Field(default="en", description="Output language preference")
    verbose: bool = Field(default=False, description="Enable verbose output")
    debug: bool = Field(default=False, description="Enable debug mode")

    @classmethod
    def from_project(cls, project_path: str | Path) -> "SpecKitConfig":
        """
        Load configuration from a project directory.

        Looks for .speckit/config.yaml in the project directory.
        Falls back to environment variables and defaults if not found.
        """
        project_path = Path(project_path).resolve()
        config_file = project_path / ".speckit" / "config.yaml"

        config_data: dict = {"project_path": project_path}

        if config_file.exists():
            with open(config_file) as f:
                file_config = yaml.safe_load(f) or {}

            # Merge LLM config
            if "llm" in file_config:
                config_data["llm"] = LLMConfig(**file_config["llm"])

            # Merge storage config
            if "storage" in file_config:
                config_data["storage"] = StorageConfig(**file_config["storage"])

            # Top-level settings
            for key in ["language", "verbose", "debug"]:
                if key in file_config:
                    config_data[key] = file_config[key]

        return cls(**config_data)

    def save(self, config_file: Optional[Path] = None) -> None:
        """
        Save configuration to YAML file.

        Args:
            config_file: Path to save to. Defaults to .speckit/config.yaml in project.
        """
        if config_file is None:
            config_dir = self.project_path / self.storage.base_dir
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "config.yaml"

        config_data = {
            "llm": {
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
                "fallback_models": self.llm.fallback_models,
            },
            "storage": {
                "backend": self.storage.backend,
                "base_dir": self.storage.base_dir,
                "specs_dir": self.storage.specs_dir,
            },
            "language": self.language,
            "verbose": self.verbose,
            "debug": self.debug,
        }

        # Don't save sensitive data
        if self.llm.api_key:
            config_data["llm"]["api_key"] = "*** SET VIA ENVIRONMENT VARIABLE ***"

        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    @property
    def specs_path(self) -> Path:
        """Get the full path to the specs directory."""
        return self.project_path / self.storage.specs_dir

    @property
    def config_path(self) -> Path:
        """Get the full path to the .speckit config directory."""
        return self.project_path / self.storage.base_dir

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.specs_path.mkdir(parents=True, exist_ok=True)
