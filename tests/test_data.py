from specify_cli.data.constants import AGENT_CONFIG, SCRIPT_TYPE_CHOICES

def test_agent_config():
    """Test that agent config contains expected keys."""
    assert "claude" in AGENT_CONFIG
    assert AGENT_CONFIG["claude"]["requires_cli"] is True

def test_script_type_choices():
    """Test that script type choices are correct."""
    assert "sh" in SCRIPT_TYPE_CHOICES
    assert "ps" in SCRIPT_TYPE_CHOICES
