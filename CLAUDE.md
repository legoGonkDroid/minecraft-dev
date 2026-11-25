# Minecraft Projects (`minecraft-dev` workspace)

This folder (`~/Projects/minecraft`) is the workspace repo `git@github.com:legoGonkDroid/minecraft-dev.git`. It
pulls together all the code for our Minecraft projects, plus reference source for the mods we depend on, so we can
read it locally instead of going out to GitHub.

**This repo tracks only scripts, configuration, the empty holder folders and `prism-instances/instgroups.json`.**
Every project inside `mods/`, `prism-instances/` and `reference/` is its own git repo, listed in `structure.json`
and cloned by `scripts/workspace.py`; the root `.gitignore` hides their contents.

```
minecraft/
├── CLAUDE.md
├── structure.json         # which repos live where, and on which branch
├── scripts/workspace.py   # clone / update / status / push the repos in structure.json
├── .idea/                 # JetBrains IDE project files (ignored)
├── mods/                  # our own mods, one repo per folder
├── prism-instances/       # Prism Launcher instances folder (instgroups.json is tracked here)
└── reference/             # read-only source of mods we depend on (shallow clones)
```

All paths below are relative to this project root unless stated otherwise.

## Setting up on a new machine
1. `git clone git@github.com:legoGonkDroid/minecraft-dev.git ~/Projects/minecraft` (GitHub account `legoGonkDroid`,
   formerly `jarroyer`; our own repos use SSH, reference repos HTTPS).
2. `cd ~/Projects/minecraft && scripts/workspace.py clone` — clones every repo on its configured branch.
3. Point Prism at the instances: `InstanceDir=<home>/Projects/minecraft/prism-instances` in
   `~/.local/share/PrismLauncher/prismlauncher.cfg` (Prism closed), then follow `prism-instances/MagicMod/CLAUDE.md`
   "Setting up on a new machine" (instance.cfg, jars, dev mods, saves).
4. Each repo's own `CLAUDE.md` has its setup and a "Current state" section saying where work left off.

## `structure.json` and `scripts/workspace.py`
`structure.json` is an array of single-key objects. The key is a folder of this workspace; the value is an array of
repo entries: `{"name": "<subfolder>", "url": "<git url>", "branch": "<branch>", "depth": 1}` (`depth` optional,
used for reference repos so they are shallow, single-branch clones).

`scripts/workspace.py <command> [--only <folder|name> ...]` (Python 3 stdlib):
- `clone` — clone missing repos on their configured branch; existing repos are left alone.
- `update` — clone missing repos, `git fetch` the rest and fast-forward those that are clean and on their configured
  branch. Dirty, diverged or off-branch repos are only fetched, with a warning (it never stashes, resets or merges).
- `status` — current vs configured branch, dirty, ahead/behind, for every repo.
- `push [-m MSG] [--dry-run]` — for the repos in `mods/` and `prism-instances/` only: commit all uncommitted changes
  (`git add -A`, default message `WIP: save working state (<host>, <date>)`) and push the current branch. Reference
  repos are never pushed. Run it before leaving a machine; run `update` when arriving.

Rules:
- **Keep `structure.json` current.** When a repo's working branch changes (e.g. ArsKingdom moves from
  `structure-rework` back to `main`), update its `branch`. New projects get an entry, never an untracked clone.
- **Every other Minecraft mod we depend on goes into `reference/`:** clone it on the branch for our Minecraft version
  (1.21.1 — check the branch's `gradle.properties`, branch names are misleading, see below) with `"depth": 1`, and add
  it to `structure.json`. Read `reference/` before looking anything up on GitHub; for a closed-source mod (e.g.
  Archwood Colonies, All Rights Reserved) read the jar in the MagicMod instance instead.
- Changes to this repo (scripts, structure.json, CLAUDE.md, instgroups.json) are committed here; changes inside a
  project are committed in that project's repo.

## Reference source (`reference/`)
Read-only, shallow clones (`git log`/`blame` show only the tip). All on Minecraft 1.21.1.

| Folder | Upstream | Branch | Notes |
|--------|----------|--------|-------|
| `ArsNouveau` | `baileyholl/Ars-Nouveau` | `main` | 5.13.5 = MagicMod's version. The `1.21.x` branch is the old 1.21.0 / 5.1 line. |
| `MineColonies` | `ldtteam/minecolonies` | `version/1.21` | `version/main` is 1.20.1. `release/1.21` = released builds. |
| `ArsDeco` | `LambdaMagus/Ars-Deco` | `main` | Only branch. Not a public API: only ArsKingdom's `compat/ArsDecoBridge` may touch it. |
| `Structurize` | `ldtteam/Structurize` | `version/1.21` | `version/main` is 1.20.1. |
| `BlockUI` | `ldtteam/BlockUI` | `version/main` | `version/main` *is* 1.21.1 here; `version/26` is newer. |
| `DomumOrnamentum` | `ldtteam/Domum-Ornamentum` | `version/1.21` | `version/1.21.1` is not the 1.21.1 line, despite its name. |
| `GeckoLib` | `bernie-g/geckolib` | `1.21.1` | |
| `Curios` | `TheIllusiveC4/Curios` | `1.21.1` | |

## Mods (`mods/`)

Each subfolder of `mods/` is one mod we develop (source project, not a built jar). To test a mod in an instance, build it and copy the jar into that instance's `prism-instances/<Instance>/minecraft/mods/` — but note MagicMod's mods are tracked via packwiz `.pw.toml` files (see `prism-instances/MagicMod/CLAUDE.md`). A mod must target the instance's Minecraft version and loader (e.g. MagicMod: 1.21.1 / NeoForge, Java 21).

| Mod | Folder | Mod id | Notes |
|-----|--------|--------|-------|
| Ars ReSources | `mods/ArsReSources` | `resources` | NeoForge 1.21.1, requires Ars Nouveau; Ars Deco optional. The Source Vessel copies a configured item using source from nearby jars and sends the copies into a Dominion-Wand-linked inventory. Build with `./gradlew build`; test with `./gradlew runGameTestServer`. Maven group `fun.dungeon.debauchery`. GitHub: `legoGonkDroid/ArsReSources`; pushing a `v*` tag publishes to CurseForge (`ars-resources`) via GitHub Actions. Details in `mods/ArsReSources/CLAUDE.md`. |
| Ars Kingdom | `mods/ArsKingdom` | `ars_kingdom` | NeoForge 1.21.1 Ars Nouveau × MineColonies addon, **in development** (work through the checklist in `mods/ArsKingdom/PLAN.md` chunk by chunk). Requires Ars Nouveau, Ars Deco, MineColonies, Structurize and Archwood Colonies (its Archwood Collective style pack is used for every hut it provides; our huts get matching blueprints). Build with `./gradlew build`; test with `./gradlew runGameTestServer`. GitHub: `legoGonkDroid/ArsKingdom`; pushing a `v*` tag publishes to CurseForge via GitHub Actions (same workflow as Ars ReSources). Details in `mods/ArsKingdom/CLAUDE.md`. |

## Prism Launcher instances (`prism-instances/`)

`prism-instances/` is the **instances folder for Prism Launcher** (`InstanceDir` in
`~/.local/share/PrismLauncher/prismlauncher.cfg`). Every top-level folder in it (other than dot-folders) is one
Minecraft instance; `instgroups.json` (Prism's UI groups) is the only file of it tracked by this repo.

Prism's own data (accounts, Java runtimes, asset cache, icons, meta) stays in `~/.local/share/PrismLauncher/`, not here.

### Layout

```
prism-instances/
├── instgroups.json        # Prism instance groups (which instances sit in which UI group)
├── .tmp/                  # Prism scratch space for downloads/imports — safe to ignore
└── <InstanceName>/        # one folder per instance
    ├── instance.cfg       # Prism per-instance settings (INI): name, Java path, memory, JVM args, play time
    ├── mmc-pack.json      # component list: Minecraft version, mod loader + version, LWJGL
    ├── patches/           # (optional) custom component overrides / JSON patches
    └── minecraft/         # the actual .minecraft game directory
        ├── mods/          # mod jars (.jar; disabled mods end in .jar.disabled)
        ├── config/        # mod and loader configs
        ├── defaultconfigs/# configs copied into new worlds (Forge/NeoForge)
        ├── saves/         # worlds
        ├── resourcepacks/, shaderpacks/
        ├── options.txt    # vanilla client options
        └── logs/          # latest.log, debug.log — first place to look for crashes
```

### Current instances

| Instance  | Minecraft | Loader          | Notes |
|-----------|-----------|-----------------|-------|
| MagicMod  | 1.21.1    | NeoForge 21.1.267 | Magic pack (Ars Nouveau + ~30 addons, Cataclysm, MineColonies + Archwood Colonies, Waystones, Xaero's, EMI, Jade, FTB Quests, KubeJS, Starter Kit). Java: Prism-managed `java-runtime-delta` (Java 21). Its folder is its own git repo (`legoGonkDroid/MagicMod`) laid out like ATM-10: mods tracked as `minecraft/mods/.index/*.pw.toml`, CI builds a packwiz pack + CurseForge zip on `v*` tags. **Everything about it — KubeJS scripts and Rhino quirks, datapacks, Starter Kit, removed mods, and the generated FTB Quests book (`questgen/`) — is in `prism-instances/MagicMod/CLAUDE.md`.** |

Keep this table updated when instances are added, removed, or their versions change (and add them to `structure.json`).

### Working with instances

- **Close Prism (or at least don't run the instance) before editing** `instance.cfg` / `mmc-pack.json` — Prism rewrites these files and may clobber changes made while it's open.
- **Changing Minecraft or loader versions**: prefer doing it through Prism's "Edit → Version" UI. If editing `mmc-pack.json` by hand, update `version` (the `cached*` fields are just caches Prism refreshes) and keep the loader's `cachedRequires` Minecraft version consistent.
- **Mods** must match the instance's Minecraft version *and* loader (Forge vs NeoForge vs Fabric/Quilt jars are not interchangeable). 1.21.x needs Java 21.
- **Memory / JVM args** live in `instance.cfg` (`OverrideMemory=true`, `MinMemAlloc`, `MaxMemAlloc` in MB, `OverrideJavaArgs`, `JvmArgs`). Without overrides the global Prism settings apply.
- **Crash debugging**: check `<instance>/minecraft/logs/latest.log` and `<instance>/minecraft/crash-reports/`.
- Do not touch `~/.local/share/PrismLauncher/accounts.json` (contains Microsoft auth tokens).
- Worlds in `saves/` are irreplaceable user data — back up before any operation that could affect them, and never delete them without asking.
- Per-instance `CLAUDE.md` files (e.g. `prism-instances/MagicMod/CLAUDE.md`) hold instance-specific notes.
