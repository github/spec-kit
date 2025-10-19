import subprocess
import time
from typing import Dict, Any, Optional


class GuardExecutor:
    
    def __init__(self, guard_id: str, command: str, timeout: int = 300, registry=None):
        self.guard_id = guard_id
        self.command = command
        self.timeout = timeout
        self.registry = registry
    
    def execute(self) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            passed = result.returncode == 0
            
            output_data = {
                "exit_code": result.returncode,
                "passed": passed,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_ms": duration_ms,
                "timed_out": False
            }
            
            if self.registry:
                result_status = "pass" if passed else "fail"
                combined_output = result.stdout + "\n" + result.stderr
                self.registry.record_execution(
                    guard_id=self.guard_id,
                    result=result_status,
                    exit_code=result.returncode,
                    duration_ms=duration_ms,
                    output=combined_output
                )
            
            return output_data
        
        except subprocess.TimeoutExpired as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            output_data = {
                "exit_code": 124,
                "passed": False,
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": e.stderr.decode() if e.stderr else "",
                "duration_ms": duration_ms,
                "timed_out": True
            }
            
            if self.registry:
                combined_output = output_data["stdout"] + "\n" + output_data["stderr"]
                self.registry.record_execution(
                    guard_id=self.guard_id,
                    result="timeout",
                    exit_code=124,
                    duration_ms=duration_ms,
                    output=combined_output
                )
            
            return output_data
    
    def parse_pytest_output(self, stdout: str, stderr: str) -> Dict:
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        for line in stdout.split('\n'):
            if 'passed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part.lower() and i > 0:
                        try:
                            tests_passed = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
            
            if 'failed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'failed' in part.lower() and i > 0:
                        try:
                            tests_failed = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        tests_run = tests_passed + tests_failed
        
        return {
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed
        }
