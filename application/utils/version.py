"""
Git-based version utility for The Health Collective Inc.

Automatically generates version strings based on git commit information.
"""

import subprocess
from pathlib import Path


def get_git_version():
    """
    Get version string based on git commit information.

    Format: v1.0.{commit_count}[-dirty]

    Returns:
        str: Version string (e.g., "v1.0.222" or "v1.0.222-dirty")
             Falls back to "v1.0.dev" if git is not available
    """
    try:
        # Get the repository root directory (parent of application/)
        app_dir = Path(__file__).parent.parent
        repo_root = app_dir.parent

        # Get total commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return "v1.0.dev"

        commit_count = result.stdout.strip()

        # Check if working directory is dirty (has uncommitted changes)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )

        is_dirty = bool(result.stdout.strip())

        # Build version string
        version = f"v1.0.{commit_count}"
        if is_dirty:
            version += "-dirty"

        return version

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
        Exception,
    ):
        # Fallback if git is not available or any error occurs
        return "v1.0.dev"


def get_git_commit_info():
    """
    Get detailed git commit information.

    Returns:
        dict: {
            'short_hash': str,  # Short commit hash (e.g., "5bfd3ae")
            'full_hash': str,   # Full commit hash
            'date': str,        # Commit date (YYYY-MM-DD)
            'count': int,       # Total commit count
            'is_dirty': bool    # Has uncommitted changes
        }
        Returns None if git is not available
    """
    try:
        app_dir = Path(__file__).parent.parent
        repo_root = app_dir.parent

        # Get short hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        short_hash = result.stdout.strip() if result.returncode == 0 else "unknown"

        # Get full hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        full_hash = result.stdout.strip() if result.returncode == 0 else "unknown"

        # Get commit date
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_date = result.stdout.strip() if result.returncode == 0 else "unknown"

        # Get commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0

        # Check if dirty
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        is_dirty = bool(result.stdout.strip())

        return {
            "short_hash": short_hash,
            "full_hash": full_hash,
            "date": commit_date,
            "count": commit_count,
            "is_dirty": is_dirty,
        }

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
        Exception,
    ):
        return None


# Cache version on module import for performance
_cached_version = None


def get_version():
    """
    Get cached version string.

    Version is cached on first call to avoid repeated git subprocess calls.

    Returns:
        str: Version string
    """
    global _cached_version
    if _cached_version is None:
        _cached_version = get_git_version()
    return _cached_version
