#!/usr/bin/env python3
"""Manage the repos listed in structure.json.

structure.json is an array of single-key objects. Each key is a folder of this workspace
(e.g. "mods"); its value is an array of repo entries:
    {"name": "<subfolder>", "url": "<git url>", "branch": "<branch>", "depth": 1 (optional)}

Usage:
    scripts/workspace.py clone   [--only X ...]   clone missing repos on their configured branch
    scripts/workspace.py update  [--only X ...]   clone missing, then fast-forward clean repos
    scripts/workspace.py status  [--only X ...]   branch / dirty / ahead-behind for every repo
    scripts/workspace.py push    [--only X ...] [-m MSG] [--dry-run]
                                                  commit + push the working state of the repos in
                                                  mods/ and prism-instances/ (never reference/)

--only takes folder names (mods, reference, ...) or repo names (ArsKingdom, ...).
"""
import argparse
import datetime
import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRUCTURE = ROOT / "structure.json"
PUSHABLE = {"mods", "prism-instances"}


class Repo:
    def __init__(self, folder, entry):
        self.folder = folder
        self.name = entry["name"]
        self.url = entry["url"]
        self.branch = entry["branch"]
        self.depth = entry.get("depth")
        self.path = ROOT / folder / self.name

    @property
    def label(self):
        return f"{self.folder}/{self.name}"


def load_structure():
    try:
        data = json.loads(STRUCTURE.read_text())
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: cannot read {STRUCTURE}: {e}")
    if not isinstance(data, list):
        sys.exit("error: structure.json must be an array of objects")
    repos, seen = [], set()
    for i, group in enumerate(data):
        if not isinstance(group, dict) or len(group) != 1:
            sys.exit(f"error: structure.json[{i}] must be an object with exactly one key (the folder name)")
        (folder, entries), = group.items()
        if not isinstance(entries, list):
            sys.exit(f"error: structure.json[{i}].{folder} must be an array")
        for j, entry in enumerate(entries):
            where = f"structure.json[{i}].{folder}[{j}]"
            if not isinstance(entry, dict):
                sys.exit(f"error: {where} must be an object")
            for key in ("name", "url", "branch"):
                if not isinstance(entry.get(key), str) or not entry[key]:
                    sys.exit(f"error: {where} needs a non-empty string '{key}'")
            if "depth" in entry and (not isinstance(entry["depth"], int) or entry["depth"] < 1):
                sys.exit(f"error: {where}.depth must be a positive integer")
            repo = Repo(folder, entry)
            if repo.label in seen:
                sys.exit(f"error: {repo.label} is listed twice")
            seen.add(repo.label)
            repos.append(repo)
    return repos


def git(repo_path, *args, check=True):
    """Run git in repo_path; return stdout. Raises RuntimeError on failure when check is set."""
    proc = subprocess.run(["git", *args], cwd=repo_path, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip() if check else proc


def is_repo(path):
    return (path / ".git").exists()


def current_branch(repo):
    branch = git(repo.path, "rev-parse", "--abbrev-ref", "HEAD")
    return None if branch == "HEAD" else branch


def is_dirty(repo):
    return bool(git(repo.path, "status", "--porcelain"))


def ahead_behind(repo):
    """(ahead, behind) relative to the upstream, or None when there is no upstream."""
    proc = git(repo.path, "rev-list", "--left-right", "--count", "HEAD...@{upstream}", check=False)
    if proc.returncode != 0:
        return None
    ahead, behind = proc.stdout.split()
    return int(ahead), int(behind)


def do_clone(repo):
    if is_repo(repo.path):
        return "exists, skipped"
    if repo.path.exists() and any(repo.path.iterdir()):
        raise RuntimeError(f"{repo.path} exists and is not a git repo")
    repo.path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["clone", "--branch", repo.branch]
    if repo.depth:
        cmd += ["--depth", str(repo.depth), "--single-branch"]
    git(ROOT, *cmd, repo.url, str(repo.path))
    return f"cloned ({repo.branch})"


def do_update(repo):
    if not is_repo(repo.path):
        return do_clone(repo)
    git(repo.path, "fetch", "--prune", "origin")
    branch = current_branch(repo)
    if branch != repo.branch:
        return f"WARN fetched only: on {branch or 'detached HEAD'}, structure.json says {repo.branch}"
    if is_dirty(repo):
        return "WARN fetched only: uncommitted changes"
    counts = ahead_behind(repo)
    if counts is None:
        return "WARN fetched only: no upstream branch"
    ahead, behind = counts
    if behind == 0:
        return "up to date" + (f" ({ahead} unpushed)" if ahead else "")
    if ahead:
        return f"WARN fetched only: diverged ({ahead} ahead, {behind} behind)"
    git(repo.path, "pull", "--ff-only")
    return f"fast-forwarded {behind} commit(s)"


def do_status(repo):
    if not is_repo(repo.path):
        return "not cloned"
    branch = current_branch(repo) or "detached HEAD"
    parts = [branch if branch == repo.branch else f"{branch} (config: {repo.branch})"]
    if is_dirty(repo):
        parts.append("dirty")
    counts = ahead_behind(repo)
    if counts is None:
        parts.append("no upstream")
    else:
        ahead, behind = counts
        if ahead:
            parts.append(f"{ahead} ahead")
        if behind:
            parts.append(f"{behind} behind")
    return ", ".join(parts)


def do_push(repo, message, dry_run):
    if repo.folder not in PUSHABLE:
        return "skipped (reference repos are never pushed)"
    if not is_repo(repo.path):
        return "not cloned, skipped"
    branch = current_branch(repo)
    if branch is None:
        raise RuntimeError("detached HEAD, not pushing")
    notes = []
    if branch != repo.branch:
        notes.append(f"WARN on {branch}, structure.json says {repo.branch}")
    if is_dirty(repo):
        if dry_run:
            changed = git(repo.path, "status", "--porcelain").splitlines()
            notes.append(f"would commit {len(changed)} change(s): {message!r}")
        else:
            git(repo.path, "add", "-A")
            git(repo.path, "commit", "-m", message)
            notes.append("committed")
    counts = ahead_behind(repo)
    needs_push = counts is None or counts[0] > 0 or (dry_run and is_dirty(repo))
    if needs_push:
        if dry_run:
            notes.append(f"would push {branch} to origin")
        else:
            git(repo.path, "push", "-u", "origin", branch)
            notes.append(f"pushed {branch}")
    if all(n.startswith("WARN") for n in notes):
        notes.append("nothing to push")
    return "; ".join(notes)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("clone", "update", "status", "push"):
        p = sub.add_parser(name)
        p.add_argument("--only", nargs="+", metavar="X", help="folder or repo names to limit to")
        if name == "push":
            p.add_argument("-m", "--message", help="commit message for uncommitted changes")
            p.add_argument("--dry-run", action="store_true", help="show what would happen")
    args = parser.parse_args()

    repos = load_structure()
    if args.only:
        wanted = set(args.only)
        repos = [r for r in repos if r.folder in wanted or r.name in wanted or r.label in wanted]
        if not repos:
            sys.exit(f"error: nothing in structure.json matches {' '.join(args.only)}")

    if args.command == "push":
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        message = args.message or f"WIP: save working state ({socket.gethostname()}, {stamp})"

    failures = 0
    width = max(len(r.label) for r in repos)
    for repo in repos:
        try:
            if args.command == "clone":
                result = do_clone(repo)
            elif args.command == "update":
                result = do_update(repo)
            elif args.command == "status":
                result = do_status(repo)
            else:
                result = do_push(repo, message, args.dry_run)
        except RuntimeError as e:
            failures += 1
            result = f"FAILED: {e}"
        print(f"{repo.label:<{width}}  {result}", flush=True)

    if failures:
        print(f"\n{failures} repo(s) failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
