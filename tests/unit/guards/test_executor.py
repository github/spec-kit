from specify_cli.guards.executor import GuardExecutor


def test_executor_success():
    executor = GuardExecutor("G001", "echo 'test passed'", timeout=5)
    result = executor.execute()
    
    assert result["exit_code"] == 0
    assert result["passed"] is True
    assert "test passed" in result["stdout"]
    assert result["timed_out"] is False
    assert result["duration_ms"] > 0


def test_executor_failure():
    executor = GuardExecutor("G001", "exit 1", timeout=5)
    result = executor.execute()
    
    assert result["exit_code"] == 1
    assert result["passed"] is False
    assert result["timed_out"] is False


def test_executor_timeout():
    executor = GuardExecutor("G001", "sleep 10", timeout=1)
    result = executor.execute()
    
    assert result["exit_code"] == 124
    assert result["passed"] is False
    assert result["timed_out"] is True


def test_parse_pytest_output():
    executor = GuardExecutor("G001", "echo test", timeout=5)
    
    stdout = "===== 5 passed, 2 failed in 1.23s ====="
    result = executor.parse_pytest_output(stdout, "")
    
    assert result["tests_run"] == 7
    assert result["tests_passed"] == 5
    assert result["tests_failed"] == 2
