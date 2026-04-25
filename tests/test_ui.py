from specify_cli._ui import StepTracker, BannerGroup, show_banner, select_with_arrows

def test_step_tracker_add_and_complete():
    t = StepTracker("test")
    t.add("step1", "Step One")
    t.complete("step1", "done")
    assert t.steps[0]["status"] == "done"

def test_step_tracker_render_returns_tree():
    from rich.tree import Tree
    t = StepTracker("test")
    t.add("s", "S")
    result = t.render()
    assert isinstance(result, Tree)

def test_step_tracker_error():
    t = StepTracker("test")
    t.add("s", "S")
    t.error("s", "failed")
    assert t.steps[0]["status"] == "error"

def test_banner_group_is_typer_group():
    from typer.core import TyperGroup
    assert issubclass(BannerGroup, TyperGroup)

def test_symbols_re_exported_from_package():
    import specify_cli
    assert hasattr(specify_cli, 'StepTracker')
    assert hasattr(specify_cli, 'BannerGroup')
    assert hasattr(specify_cli, 'show_banner')
