# M0 evidence — 2026-09-24

M0 has a runnable, pinned compiler experiment. Its exit criterion is **not yet met**: an interactive edit/export/reopen in JACK and loading the resulting map in Half-Life remain unverified. The exact JACK build number also remains to be recorded from Help → About. No map has been installed into Steam by these tools.

## Tested host and tools

| Component | Observed |
| --- | --- |
| OS / architecture | Ubuntu 24.04.5 LTS, x86_64 |
| Python | 3.12.2 (scripts require 3.11+) |
| CMake / C++ | 3.28.3 / GCC 13.3.0 |
| Steam | native launcher found on PATH; one library in the installed VDF |
| Games | Half-Life app 70 build 15961492; Counter-Strike app 10 build 12934623 |
| JACK | native x86_64, bundled Qt 4; executable fingerprint in `editor-jack.md`; exact build pending |
| Display | Wayland with XWayland; JACK window created and remained alive during a three-second startup probe |
| hltools | 1.24.0, `fc5500439a04c3962e99af75589f96ca6b99afa5`, Release, CPU only |
| Compiler SHA-256 | `457aef5b9068cddb7a4c58800ce96a5d3abaefa25bf6c376f1a70378dd8045a0` |
| Fixture SHA-256 | `b3c276856d49c1dcedd10daa21b869be610221c84b1b9c083173677f9e397efb` |

This checks one workstation. No clean-account, alternate distro, Flatpak launcher or GPU-driver certification is implied.

## Command transcript (paths expressed relative to this repo)

Machine paths are saved only in ignored `.local/user.toml`. The exact probe, compiler commands and hashes remain in ignored `build/m0/`. Commands actually exercised:

```text
python3 tools/m0.py probe
  exit 0; both targets present; executable/data/game paths resolved
python3 tools/m0.py editor --dry-run --map fixtures/m0/sdk_m0_room.map
  Jack argv uses absolute map path; cwd is its installation directory
cmake -S .local/src/hltools -B .local/src/hltools/build -DCMAKE_BUILD_TYPE=Release -DHLTOOLS_GPU=OFF
  exit 0
cmake --build .local/src/hltools/build --target hltools --parallel 4
  exit 0; built bin/hltools
python3 tools/build_compiler.py
  exit 0; pinned revision checked; recipe rerun and binary hash recorded
.local/src/hltools/bin/hltools compile -h
  documents -noembedsource
python3 tools/m0.py smoke
  exit 0; BSP30, 6,988 bytes, no embedded source, no appended bytes
python3 tools/m0.py smoke
  exit 0; same structure, different timestamp/hash
python3 -m unittest discover -s tests -v
  9 tests passed
```

The native startup check called the same `editor_command` function, launched JACK with its cwd/environment, read X window titles, then terminated only that newly started process. It observed a `J.A.C.K.` window and nonfatal GTK/ICU warnings. It did not interact with the 3D viewport or change game profiles.

The first, hand-authored fixture compile failed with an outside-world diagnostic because its face winding was reversed. Reversing the point order fixed the fixture; no compiler source workaround was needed. The final compile log has no leak/error/warning diagnostics.

`hltools bsp info` for the final fixture reported:

```text
version        30 (GoldSrc)
file size      6.8 KB
stages         csg+bsp, vis, rad
entities       3 (0 brush models)
textures       5 (0 embedded, 5 from wads)
wads           halflife.wad
models         1
faces          16
clipnodes      18
leaves         2
lightdata      4350 bytes
visdata        1 byte
```

The five texture references include the selected texture's alternate family. The game assets and WADs were read in place. Output was written beside the staged source: `sdk_m0_room.bsp`, `.prt`, `.ext`, and an empty `logs/` directory. The helper captures separate stdout and inspection logs plus `report.json`.

## Source embedding experiment

The tested normal command was:

```text
hltools compile -noembedsource -wadtextures -threads 2 -wadcfgfile <stage>/wad.cfg <stage>/sdk_m0_room.map
```

Removing **only** `-noembedsource` produced an appended ZIP with entry `source.map`. Python's ZIP reader opened it, and `tools/m0.py inspect` rejected the BSP with exit 1 and `BSP has appended data (possible embedded MAP source)`. Recompiling with the flag removed the ZIP; the restored BSP ended exactly at the last lump. The local report was refreshed after this experiment. This positive control establishes that the absence check can detect the compiler's real source archive.

## Repeated output

Two initial successful output hashes were:

```text
567d390faa6fa1060da336defdc01b25bb909ea838db281209bdb4d95ea48756
6aecddabeb6f3c9f71f34080203f12dda01fc8976e1c8fd2d1d2c5314b7354d1
```

The first artifact was later recompiled for the source-embedding experiment; these are historical observed hashes, not expected hashes for every run. The entity lump contains `compiled_at`; all other lumps matched. An in-memory comparison replacing only that timestamp made the BSP bytes equal. Actual BSPs remain unmodified. The compile banner also includes the compiler build date, so a source pin alone does not guarantee identical output across build dates.

## Finish M0 interactively

Follow [JACK setup and checklist](editor-jack.md). Record the editor build, viewport/textures/FGD result, a manually edited MAP export and reopen, then its compile command and BSP inspection. `smoke` compiles the tracked fixture; use its logged compiler command with the manual export path for that final test.

Installing into Steam is an explicit manual step for this M0 acceptance exercise: choose the generated BSP, ensure `valve/maps/sdk_m0_room.bsp` does not already exist (back it up if it does), then copy only that BSP. Start Half-Life using the resolved Steam launcher:

```text
steam -applaunch 70 -game valve +map sdk_m0_room
```

That is a candidate command, **not a tested launch transcript**. Verify actual map loading, player spawn, collision, visible textures and lighting. Record observations here. Automated install/launch and CS arena playtesting belong to later milestones.
