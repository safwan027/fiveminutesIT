"""
publisher.py — Push rendered HTML to website repo via git
Daily brief always pushes. Para A and changelog only push when changed.
"""

import os
import subprocess
from pathlib import Path
from datetime import date


def _run(cmd: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {cmd}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


def publish(output_path: Path, para_a_changed: bool):
    site_path = output_path / "site"

    # Check for a separate website repo path in env, else use site dir itself
    website_repo = Path(os.environ.get("WEBSITE_REPO_PATH", str(site_path)))

    if not (website_repo / ".git").exists():
        print(f"  No git repo found at {website_repo} — skipping publish.")
        print(f"  To publish: copy files from {site_path} to your website directory.")
        print(f"  Files ready: index.html, para-a.html, changelog.html")
        return

    today = date.today().isoformat()

    # Copy rendered files to website repo
    import shutil
    for fname in ["index.html", "para-a.html", "changelog.html"]:
        src = site_path / fname
        dst = website_repo / fname
        if src.exists():
            shutil.copy2(src, dst)

    # Check what actually changed
    changed = _run("git diff --name-only", website_repo, check=False).stdout.strip()
    changed_files = changed.splitlines() if changed else []

    print(f"  Changed files: {changed_files or 'none'}")

    if not changed_files:
        print("  Nothing to commit — all files identical.")
        return

    # Always stage and commit index.html
    files_to_commit = ["index.html"]

    # Conditionally stage Para A and changelog only if they changed
    if "para-a.html" in changed_files and para_a_changed:
        files_to_commit.append("para-a.html")
    if "changelog.html" in changed_files:
        files_to_commit.append("changelog.html")

    files_str = " ".join(files_to_commit)
    commit_msg = f"brief: {today}"
    if para_a_changed:
        commit_msg += " (Para A updated)"

    try:
        _run(f"git add {files_str}", website_repo)
        _run(f'git commit -m "{commit_msg}"', website_repo)
        _run("git push", website_repo)
        print(f"  Published: {', '.join(files_to_commit)}")
    except RuntimeError as e:
        print(f"  Publish failed: {e}")
        raise
