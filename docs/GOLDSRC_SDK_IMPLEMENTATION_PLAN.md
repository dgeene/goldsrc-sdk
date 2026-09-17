# GoldSrc mapping SDK: implementation plan

Status: handoff specification, 2026-09-17. Paste this file into the root of a new Git repository as `PLAN.md` and give the agent the instruction in [Agent handoff](#agent-handoff). This plan is for reproducible **map authoring on a Linux workstation**, with legitimate Steam game installations providing the proprietary assets. The developer's graphical editor and game run on the host GPU; compilation can run locally or in a headless container.

## 1. Goal and boundaries

Build a repository that lets a new developer clone it, discover or specify their Half-Life / Counter-Strike installation, validate dependencies, open a configured editor, compile an example Valve 220 `.map`, inspect the resulting `.bsp`, install the map into a selected game, and launch it. A rebuild on another Linux machine must use the same recorded compiler source and options. The repo must also document how to preserve its setup and assets for years.

Initial target: Ubuntu 24.04 x86_64 with the standard native Steam installation in its default location, supporting **both Half-Life (`valve`) and Counter-Strike 1.6 (`cstrike`) in v1**. Primary editor: native Linux J.A.C.K. Fallback for unsupported editor configuration automation: documented manual J.A.C.K. configuration with generated values and a verification checklist. Hammer 3.x under a dedicated Wine prefix is a later option. BSPGuy / a standalone BSP viewer are optional inspection tools; they do not replace the source map editor.

**Definition of done:** a fresh clone on a second Ubuntu 24.04 user account can complete the happy path for both `valve` and `cstrike` with legitimate Half-Life 1, Counter-Strike 1.6 and J.A.C.K. installs, plus stated system prerequisites; no paths from the first developer's machine are checked into Git. The agent records any steps that cannot genuinely be automated.

Out of scope for the first release: shipping Valve or paid editor assets, reverse engineering an editor's private configuration, automatically decompiling others' BSPs, running GUI editors in Docker or Proxmox, remote server deployment, a universal package manager, or claiming bit-for-bit reproducible BSP output without measuring it.

## 2. Decisions and assumptions

| Topic | Initial decision | Validation / escape hatch |
| --- | --- | --- |
| Host OS | Ubuntu 24.04 x86_64 desktop; native Steam at its default Linux install location | Support other Steam libraries by discovery/override; document another distro only after testing it. |
| Games | Both Half-Life 1 `valve` and Counter-Strike 1.6 `cstrike` required in v1 | Each target validates its own game and asset files; support explicit override. |
| J.A.C.K. | Native Linux J.A.C.K. is the required primary editor; user installs a licensed copy | Discover executable or accept `--editor-path`; never redistribute it. Hammer under Wine is later. |
| Map format | Valve 220 `.map` as canonical source | Preserve `.rmf` too if the chosen editor uses it; verify round trips before conversion. |
| Compiler | Evaluate pinned `hltools` on a minimal fixture; CPU path | It is currently marked work in progress by upstream. If a real test fails, choose and pin a proven Linux compatible alternative, documenting the reason. |
| CLI | Python 3 standard library for parsing VDF, paths, TOML, subprocesses and diagnostics; thin `./goldsrc` launcher | Avoid third party Python requirements unless a concrete need appears. Require and document a supported Python version. |
| Build isolation | Local compiler is sufficient for v1; container and CI come later | No Docker requirement for day one. Compiler does not need a GPU. |
| Initial content | Tooling and the two original example projects | Add real map projects and custom assets later. |
| Embedded source | Disable embedded `.map` source in distributable BSPs by default | Verify the selected compiler's flag and resulting BSP; preserve `.map` in Git. |
| Configuration | Versioned project TOML and user local config generated from an example | Local file is ignored by Git; no absolute host paths in tracked config. |
| Install | Explicit opt-in copying of generated files to a selected Steam mod | Provide dry run, overwrite backup or confirmation, and exact file list. |

These are defaults for implementation, not guesses about upstream APIs. Verify the current executable flags, game layout, J.A.C.K. settings behavior, and compiler output locations on a working machine before coding to them.

## 3. User experience contract

The README should support the following flow (exact syntax can be adjusted once implemented, then consistently documented):

```bash
git clone <repository-url> goldsrc-sdk
cd goldsrc-sdk
./goldsrc bootstrap --game valve
./goldsrc doctor --game valve
./goldsrc configure-editor jack --game valve
./goldsrc configure-editor jack --game cstrike
./goldsrc build projects/example --profile fast
./goldsrc inspect projects/example
./goldsrc install projects/example --game valve --dry-run
./goldsrc install projects/example --game valve
./goldsrc run projects/example --game valve
./goldsrc doctor --game cstrike
./goldsrc build projects/example-cstrike --profile fast
./goldsrc install projects/example-cstrike --game cstrike
./goldsrc run projects/example-cstrike --game cstrike
```

`bootstrap` may ask for a path when discovery is ambiguous, but must also work noninteractively with `--half-life-dir` or an environment variable. `doctor` is read only and reports actionable errors. `build` never writes into Steam. `install` is the only command that copies build output to Steam. `run` uses the installed native game and prints a manual launch command if Steam invocation cannot be verified. Every command supports `--help`, has meaningful exit codes, and prints the resolved paths and selected versions where useful.

Example targets: `projects/example` is a tiny, sealed Half-Life room with a light and player spawn; `projects/example-cstrike` is a small Counter-Strike test arena with appropriate team spawns and any other entities needed to start a playable test. Keep game-specific projects separate even if some geometry can be shared. The fixtures use permitted textures from the user's installed games or original custom assets; they never copy proprietary textures into Git.

## 4. Proposed repository

```text
goldsrc-sdk/
├── PLAN.md
├── AGENTS.md
├── README.md
├── LICENSE
├── .gitignore
├── goldsrc                     # executable CLI entry point
├── src/goldsrc_sdk/            # discovery, config, validation, build, install
├── config/
│   ├── user.example.toml
│   ├── games/valve.toml
│   └── games/cstrike.toml
├── projects/example/
│   ├── project.toml
│   ├── maps/example.map
│   └── README.md
├── projects/example-cstrike/
│   ├── project.toml
│   ├── maps/example-cstrike.map
│   └── README.md
├── fgd/                        # only files with confirmed redistribution rights
├── tools/
│   ├── versions.lock.toml      # pinned upstream revision, build recipe, hashes
│   └── README.md
├── containers/                 # optional compiler image, later milestone
├── docs/
│   ├── editor-jack.md
│   ├── hammer-wine.md
│   ├── assets-and-licenses.md
│   ├── troubleshooting.md
│   └── preservation.md
└── tests/
```

Local ignored data lives under `.local/` (user config, discovered path cache, installed tool binaries if managed by the repo) and `build/` (BSPs, intermediate files, logs, manifests). Do not create tracked symlinks into Steam or track `.wad`, stock `.fgd` of uncertain license, game binaries, Steam credentials, Wine prefixes, or proprietary editor files. Check licenses before copying any FGD or third party code into the repo; if redistribution is unclear, refer to the user's installed copy and store only an attribution/source reference or original supplemental definitions.

An example `project.toml` should define a project ID, game target, source map, optional custom WADs and extra packaged assets, compile profile and launch map name. Validate names and paths before use. Store no machine-specific absolute paths in it.

## 5. Architecture and invariants

1. **Resolve paths:** parse Steam `libraryfolders.vdf` and check common install roots, including custom libraries. Check that the chosen `Half-Life/valve` directory is real; accept a direct override. Distinguish `Half-Life/cstrike` from standalone or other mod layouts based on actual file checks. If multiple candidates exist, list them and require an explicit selection; do not silently take the first.
2. **Normalize locally:** store the selected actual paths in ignored `.local/user.toml`, or generate `.local/games/valve` and `.local/games/cstrike` symlinks if the editor requires stable paths. Resolve symlinks to check file existence, and never delete or replace an existing unrelated path automatically. The repository works even when Steam is on a mounted disk or installed as a Flatpak if detected or explicitly supplied.
3. **Read only discovery:** `doctor` checks host architecture, Python, game root, mod, WADs, FGD sources, editor availability, compiler availability, graphics capability for GUI only, and writable build/install destinations. A missing optional component gives a warning, not a false failure.
4. **Editor adapter:** derive J.A.C.K. game directory, FGD, WAD list, default source directory, output directory and executable values from the same config used by CLI. First investigate documented J.A.C.K. configuration/import mechanisms on Linux. If no stable safe mechanism exists, generate a concise setup sheet with exact paths plus a screenshot/manual test checklist; do not mutate opaque editor state.
5. **Compiler adapter:** the wrapper stages inputs in `build/<project>/<profile>/`, resolves WAD dependencies without modifying game assets, runs a pinned compiler with a subprocess argument array, captures full stdout/stderr and exit code, verifies a nonempty BSP and writes a build manifest. Keep `fast` and `release` compile arguments explicit and versioned. Disable embedded source for distributable output by default and verify that the compiler honored the setting. Determine the real compiler output naming/path experimentally; do not rely on assumed flags.
6. **Artifact validation:** inspect BSP version/metadata with a supported tool when possible. Record hashes for input `.map`, custom WADs, compiler binary, output BSP and the effective command/options. State whether a repeated build is byte identical; do not promise it if it is not.
7. **Install/launch:** map install destinations by game target, copy only declared BSP and explicitly packaged custom assets, reject path traversal and accidental overwrites, provide dry run, and log installed file paths. Avoid staging partial installs where practical. Never modify maps owned by the game unless explicitly targeting a matching project name and backed up. Native Steam launch may be a printed command if automated launch is unreliable.

### Example manifest fields

```text
project, target_game, map_name, source_sha256, compiler_name,
compiler_revision, compiler_sha256, command_argv, build_profile,
asset_paths_and_hashes, output_paths_and_hashes, timestamp, host_arch
```

Treat reproducibility as three measurable levels: **recreatable setup** (same recipe and external dependencies), **repeatable workflow** (same source and flags compile successfully), and **identical output** (same BSP bytes). Require the first two; measure and report the third.

## 6. Implementation milestones

### M0 — Inspect and prove the toolchain

- [ ] Confirm an actual native J.A.C.K. install's executable, settings location, configuration/import affordances, FGD handling and minimum dependencies. Record findings in `docs/editor-jack.md` with references to upstream docs and tested version.
- [ ] Verify game paths and relevant WAD/FGD locations on a legitimate Linux Steam installation; account for different Steam libraries. Document which assets are mandatory for `valve` and `cstrike` separately.
- [ ] Pin a specific compiler commit/release and verify its Linux build, license, `compile` flags, source embedding control, output paths and basic BSP. Configure distributable builds without embedded `.map` source and verify this on the generated BSP. Upstream `hltools` currently documents source embedding as its default, so its opt-out flag requires validation.
- [ ] Record alternatives and blocker resolutions in a brief decision log. Do not implement a speculative editor configuration writer.

**Exit:** command transcript for a manually edited minimal map that compiles and opens in Half-Life; known editor configuration mechanism or documented manual path.

### M1 — Repo skeleton and machine discovery

- [ ] Create README quick start, license for original repo content, `AGENTS.md` with scope and completion checks, `.gitignore`, CLI skeleton and versioned configuration schemas.
- [ ] Implement Steam discovery plus override; handle VDF escaping, missing or multiple libraries, spaces and Unicode in paths, symlink loops and inaccessible mounts.
- [ ] Implement idempotent `bootstrap` and read-only `doctor` with human-readable and `--json` reports. No root permission or global install required.
- [ ] Add unit tests using temporary fake Steam library trees; cover ambiguous games, missing assets, wrong target, symlinks and paths with spaces.

**Exit:** clean Linux user can resolve a valid game path, rerun bootstrap safely and see actionable diagnostics without requiring J.A.C.K. or a container.

### M2 — Editor integration

- [ ] Add `configure-editor jack`, honoring the validated M0 mechanism. Generate per-game configuration only when the format/import is documented and safe; otherwise generate exact per-field instructions and validate the resulting editor setup manually.
- [ ] Add `editor` launcher if verified; support a user-supplied executable and never download paid software.
- [ ] Confirm 3D viewport, WAD textures, entity lists from the respective FGDs, saving a new map and reopening it for both games. Record tested display server (X11/Wayland) and graphics driver limitations.

**Exit:** a new user can open both example maps with correctly displayed textures and game-specific entity definitions, or receives complete short manual configuration recipes for both game profiles.

### M3 — Build, inspect and local test

- [ ] Implement pinned compiler acquisition/build with verified source revision and checksum. Avoid executing unverified downloaded binaries; document dependencies. Permit an explicitly supplied local compiler path with its version/hash recorded.
- [ ] Implement `build`, profiles, logging, manifest, `inspect`, dry-run/install and run/print-launch workflow. Keep Steam read only until `install`.
- [ ] Add tests for compile failure propagation, missing dependencies, path traversal, destination collisions and exact install file list; test integration with the actual toolchain on a game-equipped workstation.
- [ ] Compile the fixture twice and compare results; reproduce on a second Linux account or machine if available.

**Exit:** `doctor → build → inspect → install → run` succeeds independently for both `valve` and `cstrike`. Verify each map loads and the intended player/team spawns work, not just that BSP files exist.

### M4 — Preservation and optional adapters

- [ ] Add optional CPU-only container pinned by base image digest, compiler commit and dependency hashes. Compare its BSP to the host build; explain observed differences. Keep the host editor native.
- [ ] Add Wine/Hammer instructions only after testing a chosen legal installer, Wine version, isolated prefix, game path visibility and viewport. Preserve configuration recipe and installer checksum; do not commit a prefix or installer.
- [ ] Document optional BSPGuy/viewer launch and the limitations of editing compiled BSP vs preserving `.map` source.
- [ ] Add backup recipe: `git bundle`, compiler sources/build recipe and optionally an image archive, original custom asset sources, licensed personal installers kept separately, checksums and restoration instructions on NAS/offline storage. Test restoring from a bundle on a clean directory.
- [ ] Optional CI: run path/config/unit tests without game assets; run compiler fixture with self-created assets if license allows. Game/editor integration stays a documented local test.

**Exit:** a developer can reconstruct and test the toolchain from tracked instructions and local licensed assets without needing a preserved VM.

## 7. Quality, safety and licensing checks

- Idempotency: `bootstrap`/editor configuration can rerun; generated config has a clear provenance and safe backup behavior.
- Ownership: never copy Steam WADs, MDLs, sounds, maps, stock FGDs with unverified redistribution rights, or paid editor binaries into public Git, CI artifacts, container images or distributable map packages.
- WAD references: compile against the installed WADs without accidentally packaging them; make custom authored WAD packaging explicit. Check game-specific texture resolution rules against the chosen compiler.
- Boundary: sanitize map/project identifiers, resolve paths and forbid `..` traversal in build/install/package operations; do not use shell interpolation for filenames.
- Diagnostics: show the failing prerequisite and remedy; preserve full compiler logs and effective command; `doctor --json` is stable enough for automation.
- Tests: fast synthetic fixtures cover discovery/config/install; one actual compile and launch smoke test proves the integration. Manual editor viewport inspection must be documented.
- Compatibility: document exact tested distro, architecture, Steam packaging, J.A.C.K. build, compiler revision, game build and limitations. Do not label configurations tested merely because they are plausible.
- Git hygiene: ignore `.local/`, `build/`, Wine prefixes, game symlinks, installers and secrets. Track original map, FGD additions when licensed, source images and custom assets with appropriate provenance.

## 8. Risks and fallback decisions

| Risk | Response |
| --- | --- |
| J.A.C.K. has no supported config import | Generate an exact setup sheet and manually verify; keep CLI build independent of editor settings. |
| Compiler changes or miscompiles | Pin verified revision, keep small fixture, document fallback compiler with an adapter rather than silently switching. |
| Flatpak/custom Steam layout differs | Explicit game-root flag and `doctor` diagnostics; discovery is convenience, override is authoritative. |
| Missing GPU in VM | Keep GUI on Linux host; CPU-only compiler/CI can run in VM. |
| Built BSP leaks embedded source | Disable embedding by default for distributable BSPs; inspect a built artifact to verify. Retain the `.map` in Git. |
| Asset redistribution uncertainty | Do not commit or package it until license/provenance is established. |
| Proprietary game updates alter assets | Record game version/asset hashes in manifest; warn when inputs drift. |

## 9. Confirmed owner decisions

Both games are v1 targets. Native Linux J.A.C.K. is primary; Hammer under Wine is a later option. The first tested host is Ubuntu 24.04 with the normal native Steam installation at its default location. V1 includes tooling, one Half-Life room, and one Counter-Strike arena; real projects can be added later. Local builds are sufficient for v1; pinned container and CI builds come later. Distributable BSPs must not embed original `.map` source by default. These decisions do not need to be re-asked during implementation.

## 10. Agent handoff

Give Codex this instruction after adding this document to the empty repository:

> Read `PLAN.md`. Begin with M0 toolchain verification and M1. Treat stated defaults as provisional where the plan calls for validation. Implement milestone by milestone, keeping runnable code, documentation and meaningful tests in sync. Do not invent J.A.C.K. settings formats or bundle proprietary assets. Report what was actually tested, any blocked integration requiring my installed editor/game, the next milestone, and any decisions needed from me. Finish each milestone with its exit criteria before moving on. Prefer the Linux host workflow and preserve the source `.map` and original assets.

## 11. Upstream starting points

- [J.A.C.K. official features and platform support](https://jack.hlfx.ru/en/features.html)
- [hltools repository, status and CLI](https://github.com/speedrun-16/hltools) — upstream explicitly calls it work in progress and documents `compile`, `decompile`, CPU/GPU behavior and source embedding.
- [BSPGuy repository](https://github.com/wootguy/bspguy) — compiled BSP inspection/editing.
- [TrenchBroom repository](https://github.com/TrenchBroom/TrenchBroom) — optional alternative editor; verify exact GoldSrc game configuration before claiming first-class support.

Refresh these upstream references during M0 and record tested revisions; repository documentation is not a substitute for testing the installed binaries.
