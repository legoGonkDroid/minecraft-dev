# minecraft-dev

A workspace that brings together everything needed to develop our Minecraft projects in one folder:

- our mods (`mods/`): Ars Kingdom and Ars ReSources;
- our Prism Launcher instance (`prism-instances/`): the MagicMod modpack;
- reference source for the mods we depend on (`reference/`): Ars Nouveau, MineColonies, Ars Deco,
  Structurize, BlockUI, Domum Ornamentum, GeckoLib and Curios, all on their Minecraft 1.21.1 branches.

Each project is its own git repo. This repo only holds the list of projects (`structure.json`), the script that
manages them (`scripts/workspace.py`) and the empty folders they're cloned into.

## Getting started

```sh
git clone git@github.com:legoGonkDroid/minecraft-dev.git ~/Projects/minecraft
cd ~/Projects/minecraft
scripts/workspace.py clone
```

To play or test in MagicMod, point Prism Launcher's instances folder at `prism-instances/`
(`InstanceDir` in `~/.local/share/PrismLauncher/prismlauncher.cfg`), then follow
`prism-instances/MagicMod/CLAUDE.md`.

Needs `git` and Python 3. Our own repos are cloned over SSH, so you need a GitHub SSH key that can access them.

## Using the script

| Command | What it does |
|---|---|
| `scripts/workspace.py clone` | Clones any project that's missing, on its configured branch. |
| `scripts/workspace.py update` | Fetches every project and fast-forwards the clean ones on their configured branch. Projects with uncommitted changes or on another branch are only fetched, with a warning. |
| `scripts/workspace.py status` | Shows each project's branch, uncommitted changes and commits ahead/behind. |
| `scripts/workspace.py push [-m MSG] [--dry-run]` | Commits all changes and pushes the current branch for `mods/` and `prism-instances/`. Reference projects are never pushed. |

Every command takes `--only <folder or name>` (e.g. `--only mods`, `--only ArsKingdom`).

Typical routine: `push` before leaving a machine, `update` when you sit down at another.

## Adding a project

Add an entry to `structure.json` under its folder, then run `scripts/workspace.py clone`:

```json
{"name": "FolderName", "url": "https://github.com/owner/repo.git", "branch": "1.21.1", "depth": 1}
```

`depth` is optional. Reference projects use `"depth": 1`, so only the latest commit is cloned. For a reference
project, check the branch's `gradle.properties` to make sure it targets Minecraft 1.21.1, because branch names can be
misleading. When the branch you're working on changes, update its `branch` here too.
