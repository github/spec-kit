import os
import subprocess
import sys
import shutil

def run_command(command, cwd=None, capture_output=True):
    """Run a shell command."""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.stdout.strip()
        else:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                check=True
            )
            return None
    except subprocess.CalledProcessError as e:
        if capture_output:
            # Re-raise with stderr info
            raise subprocess.CalledProcessError(e.returncode, e.cmd, output=e.stdout, stderr=e.stderr)
        raise

def get_git_status():
    """Get the status of the current git repository."""
    status_output = run_command("git status --porcelain")
    return status_output

def generate_commit_message(status_output):
    """
    Generate a commit message based on the status.
    """
    if not status_output:
        return None

    lines = status_output.split('\n')
    modified = []
    added = []
    deleted = []
    renamed = []

    for line in lines:
        code = line[:2]
        path = line[3:].strip()
        
        # Simplified parsing
        if 'M' in code:
            modified.append(path)
        elif '?' in code or 'A' in code:
            added.append(path)
        elif 'D' in code:
            deleted.append(path)
        elif 'R' in code:
            renamed.append(path)

    parts = []
    
    # Helper to format file lists
    def format_list(label, files):
        if not files:
            return ""
        if len(files) <= 3:
            return f"{label} {', '.join(files)}"
        return f"{label} {len(files)} files"

    if modified:
        parts.append(format_list("Update", modified))
    if added:
        parts.append(format_list("Add", added))
    if deleted:
        parts.append(format_list("Delete", deleted))
    if renamed:
        parts.append(format_list("Rename", renamed))

    if not parts:
        return "Update repository"
    
    # Combined message
    title = "; ".join(parts)
    # Truncate title if too long
    if len(title) > 72:
        # Fallback to counts if title is too long
        short_parts = []
        if modified: short_parts.append(f"Update {len(modified)} files")
        if added: short_parts.append(f"Add {len(added)} files")
        if deleted: short_parts.append(f"Delete {len(deleted)} files")
        if renamed: short_parts.append(f"Rename {len(renamed)} files")
        title = ", ".join(short_parts)

    return title

def main():
    if not shutil.which("git"):
        print("Error: Git is not installed.")
        sys.exit(1)

    try:
        # Check if we are in a git repo
        run_command("git rev-parse --is-inside-work-tree")
    except subprocess.CalledProcessError:
        print("Error: Not a git repository.")
        sys.exit(1)

    try:
        status = get_git_status()
        if not status:
            print("No changes to sync.")
            sys.exit(0)

        print("Detected changes:")
        print(status)

        message = generate_commit_message(status)
        print(f"\nGenerated commit message: {message}")

        # Add all changes
        print("Adding changes...")
        run_command("git add .")

        # Commit
        print("Committing...")
        # Use single quotes for command to wrap message in double quotes, escape internal double quotes
        safe_message = message.replace('"', '\\"')
        run_command(f'git commit -m "{safe_message}"')

        # Push
        print("Pushing...")
        # Get current branch
        branch = run_command("git rev-parse --abbrev-ref HEAD")
        
        try:
            run_command(f"git push origin {branch}")
        except subprocess.CalledProcessError:
            print("Push failed, trying to set upstream...")
            run_command(f"git push --set-upstream origin {branch}")

        print("Sync complete!")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError during git operation: {e}")
        if e.stderr:
            print(f"Details: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
