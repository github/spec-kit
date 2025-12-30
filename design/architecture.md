# Architecture

The Specify CLI follows a modular architecture, separating concerns into Frontend (User Interface), Backend (Business Logic), and Data (Configuration).

## Directory Structure

```
src/specify_cli/
├── frontend/           # UI and CLI interaction layer
│   ├── cli.py          # Typer commands (init, check, version)
│   └── ui.py           # Rich components (StepTracker, Banner)
├── backend/            # Core logic implementation
│   ├── git.py          # Git repository operations
│   ├── github.py       # GitHub API interaction
│   ├── project.py      # Template download and extraction logic
│   └── system.py       # System checks and file permissions
└── data/               # Static data and configuration
    └── constants.py    # Agent configs, banner text
```

## Layers

### Frontend
Handles all user interaction using `typer` and `rich`.
- **CLI**: Defines the command structure and arguments.
- **UI**: Provides visual feedback (spinners, tables, banners).

### Backend
Contains the functional logic of the application.
- **GitHub**: Handles fetching release data and downloading assets.
- **Git**: Wraps `git` command-line operations.
- **Project**: Manages the project creation workflow (unzipping, merging).
- **System**: checks for installed tools and platform-specific settings.

### Data
Stores static configuration and constants used across the application.
