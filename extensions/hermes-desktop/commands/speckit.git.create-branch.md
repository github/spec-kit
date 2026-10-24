# /speckit.git.create-branch

Create a feature branch for the new specification.

## Trigger

Runs before `/speckit.specify` via extension hook.

## Usage

```bash
/speckit.git.create-branch <feature_name> [--prefix=feat/]
```

## Options

- `--prefix` — Branch prefix (default: feat/)

## Process

1. Generate branch name: `<prefix><feature_name>` (kebab-case)
2. Create branch from main/trunk
3. Switch to new branch
4. Output branch name for subsequent commands

## Output

```json
{
  "branch": "feat/user-authentication",
  "base": "main"
}
```
