"""Installed workflow calls are scoped execution handled by the engine."""

from ...base import StepBase, StepResult, StepStatus
from ...composition import validate_call


class WorkflowStep(StepBase):
    type_key = "workflow"

    def validate(self, config):
        return [*super().validate(config), *validate_call(config)]

    def execute(self, config, context):
        return StepResult(
            status=StepStatus.FAILED,
            error="Workflow calls require the workflow engine",
        )
