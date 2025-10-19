.PHONY: test test-guards test-guards-unit test-guards-integration

test:
	uv run pytest tests/

test-guards:
	uv run pytest tests/unit/guards/ tests/integration/guards/ -v

test-guards-unit:
	uv run pytest tests/unit/guards/ -v

test-guards-integration:
	uv run pytest tests/integration/guards/ -v

test-guard-G002:
	uv run pytest /home/royceld/Programming/Personal/spec-kit/tests/unit/guards/G002_test-commands.py -v

test-guard-G003:
	uv run pytest /home/royceld/Programming/Personal/spec-kit/tests/api/guards/G003_user-endpoints.py -v

test-guard-G004:
	uv run pytest /home/royceld/Programming/Personal/spec-kit/tests/unit/guards/G004_guard-unit-tests.py -v

test-guard-G006:
	uv run pytest /home/royceld/Programming/Personal/spec-kit/tests/unit/guards/G006_smoke-test.py -v
