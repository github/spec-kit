"""
Ollama detection and setup utility.

Checks Ollama availability and model installation.
"""

import subprocess
import shutil
from typing import Optional, Dict
from pathlib import Path

from ..logging import get_logger


class OllamaChecker:
    """Checks Ollama availability and helps with setup."""

    def __init__(self):
        """Initialize Ollama checker."""
        self.logger = get_logger()
        self.ollama_url = "http://localhost:11434"
        self.required_model = "mxbai-embed-large"

    def is_ollama_installed(self) -> bool:
        """Check if Ollama CLI is installed.

        Returns:
            True if Ollama command exists
        """
        return shutil.which("ollama") is not None

    def is_ollama_running(self) -> bool:
        """Check if Ollama server is running.

        Returns:
            True if Ollama API responds
        """
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def is_model_available(self, model: str) -> bool:
        """Check if specific model is available.

        Args:
            model: Model name to check

        Returns:
            True if model is available
        """
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name", "") == model for m in models)
        except Exception:
            pass

        return False

    def check_availability(self) -> Dict[str, any]:
        """Check complete Ollama availability status.

        Returns:
            Dict with availability details
        """
        status = {
            "installed": self.is_ollama_installed(),
            "running": self.is_ollama_running(),
            "model_available": self.is_model_available(self.required_model),
            "model": self.required_model
        }

        status["available"] = (
            status["installed"] and
            status["running"] and
            status["model_available"]
        )

        return status

    def setup_instructions(self) -> str:
        """Get setup instructions for Ollama.

        Returns:
            Setup instructions string
        """
        instructions = """
# Ollama Setup Instructions

Ollama is required for vector memory features (optional).

## Installation

### Windows
1. Download Ollama for Windows from https://ollama.ai
2. Run installer
3. Start Ollama from Start Menu

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### macOS
```bash
brew install ollama
```

## Pull Required Model

```bash
ollama pull mxbai-embed-large
```

## Verify Installation

```bash
ollama list
ollama run mxbai-embed-large "test"
```

## Graceful Degradation

If Ollama is unavailable:
- System works with file-based memory only
- Vector memory features disabled
- No errors or crashes
"""
        return instructions.strip()

    def test_embedding(self, text: str = "test") -> Optional[Dict]:
        """Test embedding generation.

        Args:
            text: Text to embed

        Returns:
            Embedding result or None
        """
        try:
            import requests
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.required_model, "input": text},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "embedding": data.get("embedding"),
                    "model": self.required_model,
                    "dimensions": len(data.get("embedding", []))
                }
        except Exception as e:
            self.logger.error(f"Embedding test failed: {e}")

        return None
