# Native Linux J.A.C.K.

## Observed installation, 2026-09-24

The tested install contains `Jack` (64-bit x86 ELF), `Jack.sh`, bundled Qt 4, `libpng12.so.0`, plugins, `halflife/halflife.fgd`, `halflife/zhlt.fgd`, `halflife/zhlt.wad`, and `VDKManual.pdf` (Revision 8, December 2023). The binary SHA-256 is `452e9ae562a077cdf6d63dddaea000453a1ba68fb638a9f57cda07fb0648c28d`. The binary contains a 1.1.x version template; **the exact numeric build still needs Help → About confirmation**. A manual revision or current website release is not proof of the installed executable version.

`readelf -d Jack` reports `RPATH [.]`. Launching needs the install directory as the working directory. The included `Jack.sh` appends the application directory to `LD_LIBRARY_PATH`, but does not change directory and contains unquoted path expansions. The M0 launcher can accept that script, but using the directory or `Jack` directly avoids those script limitations:

```bash
python3 tools/m0.py editor --editor-path /path/to/jack --dry-run
python3 tools/m0.py editor --editor-path /path/to/jack
```

The launcher uses a subprocess argument array, resolves the executable before changing directory, sets `cwd` to its parent and prepends that directory to `LD_LIBRARY_PATH`. Map arguments are made absolute first. This is tested with a synthetic executable in a path containing spaces and Unicode, and by briefly starting the real installed binary. No editor configuration writer is implemented.

The manual (§6.1, p.86) locates settings in the install directory, falling back to `~/Documents/JACK` when the install is unwritable. `VDKGameCfg.ini`, `VDKSettings.ini`, `VDKRunCfg.ini` and `VDKLayout.dat` were observed in the tested install. They are private editor state; the SDK does not parse or write them.

## Configuration decision and references

Use the documented manual workflow in the bundled manual §2.2, pp.12–16 and §6.1, p.86. The manual also describes a Ctrl+F2 automatic configuration dialog for the **Steam edition**. That is not a documented external configuration import API; no stable external writer/import contract was found in the reviewed manual or official site. Manual profiles are the supported M0 path.

Official references: [features/platforms](https://jack.hlfx.ru/en/features.html), [downloads](https://jack.hlfx.ru/en/download.html), [developer site](https://crystice.com/jack/). Use your own installed `VDKManual.pdf` for the detailed field descriptions; it is not redistributed here.

## Create the two profiles

Run `python3 tools/m0.py probe` to obtain the actual resolved paths. Let `H` denote its `half_life_dir`, `J` the editor's `cwd`, and `R` this repository. These letters are documentation placeholders, not text to enter into JACK. This workstation also has a generated exact-path sheet at `.local/editor-setup.md`.

Open **Tools → Options / Configure J.A.C.K. → Game Profiles → Edit → Add**. Create separate Half-Life and Counter-Strike 1.6 profiles.

| Field | Half-Life | Counter-Strike 1.6 |
| --- | --- | --- |
| Game data / FGD | resolved `valve` FGD, normally `J/halflife/halflife.fgd` | resolved `cstrike` FGD, locally `H/cstrike/halflife-cs.fgd` |
| Map type | Half-Life / TFC | Half-Life / TFC |
| Texture format | Packages | Packages |
| Base Game Directory | `H/valve` | `H/valve` |
| Mod Directory | leave blank | `H/cstrike` |
| Game executable | `H/hl.sh` (installed native wrapper; direct launch not yet playtested) | `H/hl.sh` (with `-game cstrike` at launch) |
| Source Maps Directory | `R/fixtures/m0` during M0 | choose your own CS source directory; CS arena is a later milestone |
| Default point / solid entity | `info_player_start` / `func_wall` | `info_player_start` / `func_wall` |
| Texture files | `H/valve/halflife.wad`; add liquids, decals, xeno as needed | base Half-Life WAD plus `H/cstrike/cstrike.wad`; add individual CS map WADs as needed |

Keep `Invert studio model pitch (SQB)` enabled for native GoldSrc. `zhlt.fgd` is optional compiler-specific content: the fixture uses no definitions from it, and compatibility of its extra entities with hltools is not yet established. Tool textures can refer to JACK's `zhlt.wad` in place when needed; there is no reason to copy it into Steam.

Do not assign the unified `hltools` executable to all four traditional Build Programs slots. For M0, export Valve 220 MAP and compile using the external smoke recipe. Leave automatic game launch and compiler presets unconfigured until the corresponding integrations are tested. Steam's executable and its data directory are separate values; the candidate manual game launch is `steam -applaunch 70 -game valve +map sdk_m0_room` (CS uses app 10 / `-game cstrike`, with its own future fixture).

## Dependencies and acceptance checklist

Observed host: Ubuntu 24.04.5 x86_64, Wayland session with XWayland (`DISPLAY=:0`). ELF dependencies resolved with the bundled library directory: QtCore/Gui/OpenGL/Network 4, libpng12, X11/Xext/Xfixes/Xcursor/Xrender/Xft, fontconfig, OpenGL, glib, libaudio, libc/libstdc++ and their transitive dependencies. `ldd` reported no missing libraries. This is the verified working host set, not a minimum-package claim for a clean Ubuntu install. Do not replace the bundled Qt 4 with Qt 5/6.

A three-second startup created the JACK window without exiting. It logged nonfatal ICU, GTK theme/accessibility and inherited snap/GTK module warnings. A visible window does not establish texture rendering or graphics-driver compatibility. No package changes were made.

Still to verify interactively:

- Record **Help → About** version and graphics driver; confirm the 3D viewport.
- Add each profile's FGD and WADs; inspect the textured room and entity list. CS must expose `info_player_start` (CT), `info_player_deathmatch` (T) and CS-specific entities.
- Open `fixtures/m0/sdk_m0_room.map`, adjust the light or a brush manually, export Valve 220 MAP into `build/m0/manual/`, and reopen that export. Preserve a `.jmf`/`.rmf` source if used.
- Compile the exported map using the pinned command in `tools/README.md`, then inspect the BSP. The current `smoke` helper always stages the tracked fixture; for the manual export use the command directly with a WAD config from a smoke run.
- Explicitly install the BSP and load it in Half-Life; walk around, inspect lighting and textures, and confirm collision/spawn. Record the command and observed result in `docs/m0-verification.md`.

These unchecked steps keep M0 open. The SDK has not silently configured JACK or certified an unobserved playtest.
