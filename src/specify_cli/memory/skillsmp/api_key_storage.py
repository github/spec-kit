"""
API key storage for SkillsMP.

Securely stores API keys using platform-specific credential storage.
"""

import json
import os
from typing import Optional
from pathlib import Path
from platform import system

from ..logging import get_logger


class APIKeyStorage:
    """Secure API key storage."""

    def __init__(self, service_name: str = "skillsmp"):
        """Initialize API key storage.

        Args:
            service_name: Name of service (for keyring identification)
        """
        self.logger = get_logger()
        self.service_name = service_name
        self.platform = system()

        # Fallback storage directory
        self.storage_dir = Path.home() / ".claude" / "memory" / "credentials"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def store_api_key(self, api_key: str) -> bool:
        """Store API key securely.

        Args:
            api_key: API key to store

        Returns:
            True if successful
        """
        try:
            # Try keyring first (most secure)
            try:
                import keyring
                keyring.set_password(
                    self.service_name,
                    "api_key",
                    api_key
                )
                self.logger.info("API key stored in system keyring")
                return True
            except ImportError:
                self.logger.debug("keyring not available, using fallback storage")
            except Exception as e:
                self.logger.warning(f"keyring failed: {e}")

            # Fallback: encrypted file storage
            return self._store_fallback(api_key)

        except Exception as e:
            self.logger.error(f"Failed to store API key: {e}")
            return False

    def get_api_key(self) -> Optional[str]:
        """Retrieve stored API key.

        Returns:
            API key or None
        """
        try:
            # Try keyring first
            try:
                import keyring
                key = keyring.get_password(
                    self.service_name,
                    "api_key"
                )
                if key:
                    return key
            except ImportError:
                pass
            except Exception:
                pass

            # Fallback to file storage
            return self._get_fallback()

        except Exception:
            return None

    def _store_fallback(self, api_key: str) -> bool:
        """Store API key in encrypted file (fallback).

        Args:
            api_key: API key

        Returns:
            True if successful
        """
        try:
            import base64

            # Simple encoding (not encryption, but obfuscation)
            # For production, use cryptography library
            encoded = base64.b64encode(api_key.encode()).decode()

            storage_file = self.storage_dir / f"{self.service_name}.key"

            # Set restrictive permissions
            storage_file.write_text(encoded)

            # Set file permissions (Unix only)
            if self.platform != "Windows":
                os.chmod(storage_file, 0o600)

            self.logger.info(f"API key stored in {storage_file}")
            return True

        except Exception as e:
            self.logger.error(f"Fallback storage failed: {e}")
            return False

    def _get_fallback(self) -> Optional[str]:
        """Retrieve API key from fallback storage.

        Returns:
            API key or None
        """
        try:
            import base64

            storage_file = self.storage_dir / f"{self.service_name}.key"

            if not storage_file.exists():
                return None

            encoded = storage_file.read_text()
            decoded = base64.b64decode(encoded).decode()

            return decoded

        except Exception:
            return None

    def delete_api_key(self) -> bool:
        """Delete stored API key.

        Returns:
            True if successful
        """
        try:
            # Try keyring
            try:
                import keyring
                keyring.delete_password(
                    self.service_name,
                    "api_key"
                )
            except:
                pass

            # Remove fallback file
            storage_file = self.storage_dir / f"{self.service_name}.key"
            if storage_file.exists():
                storage_file.unlink()

            self.logger.info("API key deleted")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete API key: {e}")
            return False

    def has_api_key(self) -> bool:
        """Check if API key is stored.

        Returns:
            True if API key exists
        """
        return self.get_api_key() is not None
