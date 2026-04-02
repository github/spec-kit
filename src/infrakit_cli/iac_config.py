"""
IaC (Infrastructure as Code) tool configurations for infrakit-cli.

Defines the supported IaC tools and their metadata, used during
`infrakit init` to generate tool-specific commands and templates.
"""

IAC_CONFIG = {
    "crossplane": {
        "name": "Crossplane",
        "description": "Kubernetes-native infrastructure as code",
        "requires_tools": ["kubectl"],
        "optional_tools": ["crossplane", "docker"],
        "output_format": "yaml",
        "resource_term": "composition",
        "generic_commands": [
            "setup",
            "status",
            "analyze",
            "implement",
            "architect-review",
            "security-review",
            "tasks",
        ],
        "iac_commands": [
            "new_composition",
            "update_composition",
            "review",
            "plan",
        ],
    },
    # Future IaC tools:
    # "terraform": {
    #     "name": "Terraform",
    #     "description": "Infrastructure as code by HashiCorp",
    #     "requires_tools": ["terraform"],
    #     "optional_tools": [],
    #     "output_format": "hcl",
    #     "resource_term": "module",
    # },
    # "cloudformation": {
    #     "name": "AWS CloudFormation",
    #     "description": "AWS-native infrastructure as code",
    #     "requires_tools": ["aws"],
    #     "optional_tools": [],
    #     "output_format": "yaml",
    #     "resource_term": "stack",
    # },
    # "pulumi": {
    #     "name": "Pulumi",
    #     "description": "Infrastructure as code with general-purpose languages",
    #     "requires_tools": ["pulumi"],
    #     "optional_tools": [],
    #     "output_format": "code",
    #     "resource_term": "component",
    # },
}


def get_iac_choices() -> dict[str, str]:
    """Return {tool_key: display_name} for interactive selection."""
    return {key: cfg["name"] for key, cfg in IAC_CONFIG.items()}


def get_iac_commands(iac_tool: str) -> list[str]:
    """Return the full list of commands for an IaC tool (generic + IaC-native)."""
    cfg = IAC_CONFIG.get(iac_tool, {})
    return cfg.get("generic_commands", []) + cfg.get("iac_commands", [])
