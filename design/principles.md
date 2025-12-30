# Design Principles

The following principles guide the development of the Specify CLI.

## Core Values

1.  **Maintainability** (Highest Priority)
    *   Code should be easy to understand, modify, and correct.
    *   Use clear variable names and follow PEP 8 style guidelines.
    *   Refactor complex logic into smaller, reusable functions.

2.  **Extendability**
    *   The system should be designed to allow the addition of new features (e.g., new AI agents, new template sources) without modifying existing core logic significantly.
    *   Use interfaces or base classes where appropriate.

3.  **Debuggability & Observability**
    *   Errors should be caught and handled gracefully with informative messages.
    *   Use logging (via `rich` console or standard logging) to track execution flow.
    *   Include a `--debug` flag for verbose output.

4.  **Reliability**
    *   The tool should perform consistently and handle edge cases (e.g., network failures, missing permissions).
    *   Use defensive programming techniques.

5.  **Modularity**
    *   Code should be grouped by type and responsibility (Frontend, Backend, Data).
    *   Avoid monolithic files; split logic into focused modules.

## coding Standards

*   **Unit Testing**: Every contribution must include unit tests.
*   **Docstrings**: Every module, class, and function must have a docstring explaining its purpose, arguments, and return values.
*   **Linking**: Docstrings should link to relevant specs or issues where applicable.
*   **Readability**: Prioritize readable code over clever one-liners.
