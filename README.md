# GoldSrc Mapping SDK

A Linux-first workspace for authoring Half-Life 1 and Counter-Strike 1.6 maps using your own Steam assets and native J.A.C.K. installation.

**Status: M0 toolchain investigation implemented; manual editor/game acceptance remains open.** The compiler builds and compiles an original room fixture. This is not yet the `goldsrc` CLI described in [PLAN.md](PLAN.md). M1 discovery/bootstrap and M2–M4 integrations remain future work.

## Try the M0 tools

Requirements: Linux, Python **3.11+**, Git, CMake **3.21+**, a C/C++17 toolchain and Make. Building the compiler requires network access for its source and two hash-checked dependencies. No global Python packages, root install, Docker or GPU compiler is required.

```bash
mkdir -p .local
cp config/user.example.toml .local/user.toml
# Edit .local/user.toml with your own paths before continuing.
python3 tools/m0.py probe
python3 tools/build_compiler.py
python3 tools/m0.py smoke
python3 tools/m0.py editor --dry-run --map fixtures/m0/sdk_m0_room.map
# Launch JACK when ready (the command waits until JACK exits):
python3 tools/m0.py editor
python3 -m unittest discover -s tests -v
```

Do not overwrite an existing `.local/user.toml` when repeating setup. The current workstation already has its supplied paths saved there. Configuration and downloaded sources are ignored by Git; artifacts and logs go into `build/m0/`. Smoke runs create separate directories and never install anything into Steam. The probe is read only; all commands have `--help` and return nonzero on failure.

## Flexible paths

Every `probe`, `editor` and `smoke` invocation accepts these overrides:

| Option / TOML key | Meaning |
| --- | --- |
| `--editor-path` / `editor_path` | JACK installation directory, `Jack`, or `Jack.sh`. The launcher resolves symlinks, sets its working directory to the executable's directory, and adds that directory to `LD_LIBRARY_PATH`. |
| `--steam-root` / `steam_root` | Steam **data directory**, containing `steamapps/`; distinct from its executable. |
| `--steam-executable` / `steam_executable` | Executable path or command on PATH. Defaults to `steam` on PATH, then `<steam_root>/steam.sh`. |
| `--half-life-dir` / `half_life_dir` | Root containing `valve/` and `cstrike/`, including a game on another mounted Steam library. |
| `--valve-fgd`, `--cstrike-fgd` | Installed FGD overrides. Defaults are described in [editor setup](docs/editor-jack.md). |

Precedence: command line → `GOLDSRC_` environment variable (e.g. `GOLDSRC_EDITOR_PATH`, `GOLDSRC_HALF_LIFE_DIR`) → `[paths]` in `.local/user.toml` → defaults. `--config` selects a different TOML file. Relative configured paths resolve from the current working directory; `~` is supported. Shell variables inside TOML strings are not expanded.

Without a Steam root override, M0 checks the common native and Flatpak locations, deduplicates symlinks, and refuses multiple roots. Automatic `libraryfolders.vdf` traversal belongs to M1: **use `--half-life-dir` for other libraries now**. JACK has no hard-coded home-directory default; supply its location unless it is on PATH.

```bash
python3 tools/m0.py probe --editor-path "$HOME/Applications/jack" \
  --steam-root "$HOME/.local/share/Steam" \
  --half-life-dir "/mnt/My Games/steamapps/common/Half-Life"
```

See [tested results and remaining acceptance steps](docs/m0-verification.md), [JACK configuration](docs/editor-jack.md), [asset inventory](docs/assets-and-licenses.md), and [compiler recipe](tools/README.md). Proprietary editor/game files and FGDs are not included.
