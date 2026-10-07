"""Pin project-local implementations throughout command and skill rendering."""

from __future__ import annotations

import inspect
from functools import wraps


def project_registration(handler):
    signature = inspect.signature(handler)

    @wraps(handler)
    def invoke(*args, **kwargs):
        from .installer import project_integrations

        values = signature.bind(*args, **kwargs).arguments
        root = (
            values["project_root"] if "project_root" in signature.parameters
            else values["self"].project_root
        )
        with project_integrations(root):
            return handler(*args, **kwargs)

    return invoke
