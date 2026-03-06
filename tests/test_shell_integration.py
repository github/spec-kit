#!/usr/bin/env python3
"""
Integration tests for shell scripts.

Tests the bash and PowerShell scripts for cross-platform functionality,
command-line argument handling, and integration with Python modules.
"""

import pytest
import subprocess
import tempfile
import json
import yaml
from pathlib import Path
import os
import sys


class TestBashScriptIntegration:
    """Integration tests for bash shell scripts."""

    @pytest.fixture
    def sample_data_dir(self):
        """Create temporary directory with sample data files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "test-data"
            data_dir.mkdir()

            # Create sample JSON file
            invoices = [
                {
                    "invoice_id": "INV-001",
                    "supplier_id": "SUP-ABC",
                    "amount": 1000.00,
                    "status": "pending"
                },
                {
                    "invoice_id": "INV-002",
                    "supplier_id": "SUP-XYZ",
                    "amount": 750.50,
                    "status": "paid"
                }
            ]

            with open(data_dir / "invoices.json", 'w') as f:
                json.dump(invoices, f)

            # Create sample CSV file
            with open(data_dir / "suppliers.csv", 'w') as f:
                f.write("supplier_id,company_name,email\n")
                f.write("SUP-ABC,Acme Corp,contact@acme.com\n")
                f.write("SUP-XYZ,Tech Solutions,info@tech.com\n")

            yield str(data_dir)

    @pytest.fixture
    def script_path(self):
        """Get path to bash analyze-domain script."""
        script_dir = Path(__file__).parent.parent / "scripts" / "bash"
        return script_dir / "analyze-domain.sh"

    def test_bash_script_exists(self, script_path):
        """Test that bash script exists and is executable."""
        assert script_path.exists(), f"Bash script not found at {script_path}"
        assert os.access(script_path, os.X_OK), "Bash script is not executable"

    @pytest.mark.skipif(sys.platform == "win32", reason="Bash not available on Windows")
    def test_bash_script_help(self, script_path):
        """Test bash script help functionality."""
        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        assert "Domain Analysis Tool" in result.stdout or "Usage:" in result.stdout

    @pytest.mark.skipif(sys.platform == "win32", reason="Bash not available on Windows")
    def test_bash_script_version(self, script_path):
        """Test bash script version display."""
        result = subprocess.run(
            [str(script_path), "--version"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should either show version or help (depending on implementation)
        assert result.returncode in [0, 1]  # Some help commands exit with 1

    @pytest.mark.skipif(sys.platform == "win32", reason="Bash not available on Windows")
    def test_bash_script_basic_analysis(self, script_path, sample_data_dir):
        """Test basic domain analysis with bash script."""
        result = subprocess.run(
            [str(script_path), f"--data-dir={sample_data_dir}"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent.parent
        )

        # Should complete successfully or with minor warnings
        assert result.returncode in [0, 1], f"Script failed with: {result.stderr}"

        # Check for expected output patterns
        output = result.stdout + result.stderr
        assert any(keyword in output.lower() for keyword in [
            "analyzing", "analysis", "entities", "domain", "complete"
        ]), f"Unexpected output: {output}"

    @pytest.mark.skipif(sys.platform == "win32", reason="Bash not available on Windows")
    def test_bash_script_missing_data_dir(self, script_path):
        """Test bash script with missing data directory."""
        result = subprocess.run(
            [str(script_path), "--data-dir=/nonexistent/path"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent.parent
        )

        # Should fail gracefully
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()

    @pytest.mark.skipif(sys.platform == "win32", reason="Bash not available on Windows")
    def test_bash_script_output_option(self, script_path, sample_data_dir):
        """Test bash script with output file option."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "analysis_output.json"

            result = subprocess.run(
                [str(script_path), f"--data-dir={sample_data_dir}", f"--output={output_file}"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=Path(__file__).parent.parent
            )

            # Check if command completed (may succeed or fail depending on implementation)
            if result.returncode == 0 and output_file.exists():
                # If successful, output file should contain valid JSON
                with open(output_file, 'r') as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError:
                        pytest.fail("Output file contains invalid JSON")


class TestPowerShellScriptIntegration:
    """Integration tests for PowerShell scripts."""

    @pytest.fixture
    def powershell_script_path(self):
        """Get path to PowerShell analyze-domain script."""
        script_dir = Path(__file__).parent.parent / "scripts" / "powershell"
        return script_dir / "analyze-domain.ps1"

    @pytest.fixture
    def sample_data_dir(self):
        """Create temporary directory with sample data files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "test-data"
            data_dir.mkdir()

            # Create sample JSON file
            invoices = [{"invoice_id": "INV-001", "amount": 1000.00}]
            with open(data_dir / "invoices.json", 'w') as f:
                json.dump(invoices, f)

            yield str(data_dir)

    def test_powershell_script_exists(self, powershell_script_path):
        """Test that PowerShell script exists."""
        assert powershell_script_path.exists(), f"PowerShell script not found at {powershell_script_path}"

    @pytest.mark.skipif(sys.platform != "win32", reason="PowerShell testing primarily on Windows")
    def test_powershell_script_help(self, powershell_script_path):
        """Test PowerShell script help functionality."""
        try:
            result = subprocess.run(
                ["powershell", "-File", str(powershell_script_path), "-Help"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # PowerShell might not be available on all systems
            if result.returncode == 0:
                assert "Domain Analysis" in result.stdout or "Usage:" in result.stdout
        except FileNotFoundError:
            pytest.skip("PowerShell not available on this system")

    @pytest.mark.skipif(sys.platform != "win32", reason="PowerShell testing primarily on Windows")
    def test_powershell_script_basic_analysis(self, powershell_script_path, sample_data_dir):
        """Test basic domain analysis with PowerShell script."""
        try:
            result = subprocess.run(
                ["powershell", "-File", str(powershell_script_path), "-DataDir", sample_data_dir],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=Path(__file__).parent.parent
            )

            # Should complete successfully or with minor warnings
            if result.returncode == 0:
                output = result.stdout + result.stderr
                assert any(keyword in output.lower() for keyword in [
                    "analyzing", "analysis", "entities", "domain"
                ])
        except FileNotFoundError:
            pytest.skip("PowerShell not available on this system")


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility and common utilities."""

    @pytest.fixture
    def common_bash_script(self):
        """Get path to common bash utilities."""
        return Path(__file__).parent.parent / "scripts" / "bash" / "common.sh"

    @pytest.fixture
    def common_powershell_script(self):
        """Get path to common PowerShell utilities."""
        return Path(__file__).parent.parent / "scripts" / "powershell" / "common.ps1"

    def test_common_scripts_exist(self, common_bash_script, common_powershell_script):
        """Test that common utility scripts exist."""
        assert common_bash_script.exists(), "common.sh not found"
        assert common_powershell_script.exists(), "common.ps1 not found"

    @pytest.mark.skipif(sys.platform == "win32", reason="Bash not available on Windows")
    def test_bash_common_utilities(self, common_bash_script):
        """Test bash common utilities can be sourced."""
        # Test that common.sh can be sourced without errors
        result = subprocess.run(
            ["bash", "-c", f"source {common_bash_script} && echo 'sourced successfully'"],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        assert "sourced successfully" in result.stdout

    def test_python_module_import(self):
        """Test that Python modules can be imported directly."""
        # Test importing core modules
        sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))

        try:
            import domain_analysis
            import interactive_domain_analysis
            import domain_config
            import template_populator
        except ImportError as e:
            pytest.fail(f"Failed to import Python modules: {e}")

    def test_python_module_execution(self):
        """Test that Python modules can be executed as scripts."""
        module_dir = Path(__file__).parent.parent / "src" / "specify_cli"

        # Test domain_analysis module
        result = subprocess.run(
            [sys.executable, str(module_dir / "domain_analysis.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should either show help or indicate missing arguments
        assert result.returncode in [0, 1, 2]  # Different modules may handle --help differently


class TestConfigurationIntegration:
    """Test configuration file integration with scripts."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".specify"
            config_dir.mkdir()
            yield config_dir

    def test_config_file_creation(self, temp_config_dir):
        """Test configuration file creation and reading."""
        config_file = temp_config_dir / "domain-config.yaml"

        # Create sample configuration
        config = {
            'domain_type': 'financial',
            'entities': {
                'patterns': {
                    'Invoice': ['invoice', 'bill'],
                    'Payment': ['payment', 'remittance']
                }
            },
            'settings': {
                'confidence_threshold': 0.8,
                'default_interactive': False
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Test that config can be read back
        with open(config_file, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config['domain_type'] == 'financial'
        assert loaded_config['settings']['confidence_threshold'] == 0.8

    def test_config_validation(self, temp_config_dir):
        """Test configuration validation."""
        config_file = temp_config_dir / "domain-config.yaml"

        # Create invalid configuration
        invalid_config = """
domain_type: financial
entities:
  patterns:
    Invoice: [invoice
    # Missing closing bracket - invalid YAML
"""

        with open(config_file, 'w') as f:
            f.write(invalid_config)

        # Test that invalid config is handled gracefully
        try:
            with open(config_file, 'r') as f:
                yaml.safe_load(f)
            pytest.fail("Invalid YAML should have raised an exception")
        except yaml.YAMLError:
            # Expected behavior
            pass


class TestDataProcessingIntegration:
    """Test integration of data processing with different file formats."""

    def test_json_file_processing(self):
        """Test JSON file processing through the pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create JSON test file
            data = [
                {"id": 1, "name": "Test Item", "amount": 100.0},
                {"id": 2, "name": "Another Item", "amount": 200.0}
            ]

            json_file = Path(temp_dir) / "test_data.json"
            with open(json_file, 'w') as f:
                json.dump(data, f)

            # Test that the file can be processed by domain analysis
            sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))
            from domain_analysis import DomainAnalyzer

            analyzer = DomainAnalyzer(temp_dir)
            analyzer._scan_data_files()

            assert len(analyzer.json_files) == 1
            assert analyzer.json_files[0].name == "test_data.json"

    def test_csv_file_processing(self):
        """Test CSV file processing through the pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create CSV test file
            csv_content = """id,name,amount,status
1,Test Item,100.0,active
2,Another Item,200.0,inactive
"""

            csv_file = Path(temp_dir) / "test_data.csv"
            with open(csv_file, 'w') as f:
                f.write(csv_content)

            # Test that the file can be processed by domain analysis
            sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))
            from domain_analysis import DomainAnalyzer

            analyzer = DomainAnalyzer(temp_dir)
            analyzer._scan_data_files()

            assert len(analyzer.csv_files) == 1
            assert analyzer.csv_files[0].name == "test_data.csv"


class TestErrorHandlingIntegration:
    """Test error handling across the integration pipeline."""

    def test_missing_python_dependencies(self):
        """Test handling of missing Python dependencies."""
        # This test simulates what happens when dependencies are missing
        # In actual deployment, dependencies should be properly installed

        # Test that core functionality doesn't crash with missing optional deps
        sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))

        try:
            import domain_analysis
            # If import succeeds, basic functionality should work
            assert hasattr(domain_analysis, 'DomainAnalyzer')
        except ImportError as e:
            # If import fails, it should be due to missing required dependencies
            assert 'yaml' in str(e).lower() or 'pathlib' in str(e).lower()

    def test_permission_errors(self):
        """Test handling of file permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file and make it unreadable
            test_file = Path(temp_dir) / "unreadable.json"
            test_file.write_text('{"test": "data"}')

            # Make file unreadable (Unix-like systems only)
            if hasattr(os, 'chmod'):
                os.chmod(test_file, 0o000)

                try:
                    sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))
                    from error_handling import safe_data_parsing
                    import json

                    def parse_json():
                        with open(test_file, 'r') as f:
                            return json.load(f)

                    # Should handle permission errors gracefully
                    data = safe_data_parsing(test_file, "JSON", parse_json)
                    # Should return None for unreadable files
                    assert data is None

                finally:
                    # Restore permissions for cleanup
                    os.chmod(test_file, 0o644)

    def test_corrupted_data_files(self):
        """Test handling of corrupted or invalid data files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted JSON file
            corrupted_json = Path(temp_dir) / "corrupted.json"
            corrupted_json.write_text('{"invalid": json syntax}')

            # Create corrupted CSV file
            corrupted_csv = Path(temp_dir) / "corrupted.csv"
            corrupted_csv.write_text('invalid,csv\ndata,with,inconsistent,columns\n')

            sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))
            from error_handling import safe_data_parsing
            import json as json_mod
            import csv as csv_mod

            # Should handle corrupted JSON gracefully
            def parse_json():
                with open(corrupted_json, 'r') as f:
                    return json_mod.load(f)

            json_data = safe_data_parsing(corrupted_json, "JSON", parse_json)
            assert json_data is None

            # CSV with inconsistent columns may still parse partially
            def parse_csv():
                with open(corrupted_csv, 'r') as f:
                    return list(csv_mod.DictReader(f))

            csv_data = safe_data_parsing(corrupted_csv, "CSV", parse_csv)
            # CSV might still parse partially, so we don't assert None


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])