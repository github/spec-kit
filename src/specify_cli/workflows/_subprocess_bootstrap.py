"""Standalone stdlib-only entry, run by the selected interpreter with -I -S -B."""
import importlib.util
import json
from pathlib import Path
import sys


def verify_packages(package, handles=None):
    """Check package directories, including search paths, rather than leaf files."""
    if handles is None:
        from specify_cli import _file_handles as handles
    for name, module in tuple(sys.modules.items()):
        if name != "specify_cli" and not name.startswith("specify_cli."):
            continue
        spec = getattr(module, "__spec__", None)
        if spec is None or spec.name != name or not spec.has_location:
            raise RuntimeError(f"Startup package identity: invalid spec for {name}")
        is_package = spec.submodule_search_locations is not None
        parts = name.split(".")[1:]
        expected = package.joinpath(*(parts if is_package else parts[:-1]))
        for location in (getattr(module, "__file__", None), spec.origin):
            if (not isinstance(location, str) or not Path(location).is_absolute()
                    or not handles.same_installation_directory(Path(location).parent, expected)):
                raise RuntimeError(f"Startup package identity differs for {name}")
        paths = getattr(module, "__path__", None)
        if is_package:
            if not paths or not spec.submodule_search_locations:
                raise RuntimeError(f"Startup package search paths missing for {name}")
            for location in [*paths, *spec.submodule_search_locations]:
                if (not isinstance(location, str) or not Path(location).is_absolute()
                        or not handles.same_installation_directory(Path(location), expected)):
                    raise RuntimeError(f"Startup package search directory differs for {name}")
        elif paths is not None or name == "specify_cli":
            raise RuntimeError(f"Startup package metadata inconsistent for {name}")


def _load_handles():
    """Load only the selected adjacent stdlib-only helper, without package init."""
    filename = Path(__file__)
    if not filename.is_absolute():
        raise RuntimeError("Startup requires an absolute bootstrap location")
    helper = filename.parent.parent / "_file_handles.py"
    spec = importlib.util.spec_from_file_location("_specify_workflow_file_handles", helper)
    if spec is None or spec.loader is None:
        raise RuntimeError("Startup cannot load selected native helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    return module


def main():
    handles = _load_handles()
    with handles.worker_stdio() as control:
        source = Path(sys.argv[1])
        dependencies = json.loads(sys.argv[2])
        if (not source.is_absolute() or not handles.installation_directory_exists(source)
                or not isinstance(dependencies, list)
                or any(not isinstance(p, str) or not Path(p).is_absolute() for p in dependencies)):
            raise RuntimeError("Startup requires absolute directory-backed source and dependencies")
        package = source / "specify_cli"
        verify_packages(package, handles)
        sys.path[:0] = [str(source), *dependencies]
        from specify_cli.workflows._subprocess_worker import run
        from specify_cli.workflows import _subprocess
        _subprocess._dependency_paths = tuple(dependencies)
        verify_packages(package, handles)
        run(control.incoming, control.outgoing, lambda: verify_packages(package, handles))


if __name__ == "__main__":
    main()
