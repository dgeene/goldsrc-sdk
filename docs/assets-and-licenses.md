# Local game assets

M0 inspected a legitimate native Steam installation on 2026-09-24. Both Steam manifests use `installdir "Half-Life"`; app 70 reports build **15961492**, and app 10 reports build **12934623**. Do not assume those build IDs on another machine. The tested library list contains one library. No Steam account data or complete manifests are checked in.

The game root contains `hl.sh` and `hl_linux`. The installed `hl.sh` changes to its own directory and prepares its library path; it is a more appropriate candidate for native direct launch than treating the Steam data directory as an executable. Actual engine launch remains an acceptance step.

| Target | Required baseline for this SDK's initial maps | Editor definitions found locally |
| --- | --- | --- |
| `valve` | `valve/liblist.gam`, `valve/dlls/hl.so`, `valve/cl_dlls/client.so`, `valve/halflife.wad`, native root launcher/binary | JACK `halflife/halflife.fgd` |
| `cstrike` | Base Half-Life content plus `cstrike/liblist.gam`, `cstrike/dlls/cs.so`, `cstrike/cl_dlls/client.so`, `cstrike/cstrike.wad` | `cstrike/halflife-cs.fgd` in this installation |

These are checked file-presence baselines for the observed layout, not a complete inventory of runtime models/sounds or proof of game integrity. `cstrike.wad` is the planned CS texture baseline, not a universal requirement for every possible CS map. Every map must resolve the textures it actually references. The M0 room uses only `-0OUT_WALL3` and its alternate texture family in `valve/halflife.wad`; both games' full assets remain in Steam.

Other observed authoring WADs: `valve/liquids.wad`, `valve/xeno.wad`, `valve/decals.wad`; CS includes `cs_dust.wad`, `cs_assault.wad`, `cs_office.wad` and other level sets. `cached.wad`, `tempdecal.wad`, spray/font/UI WADs are not mapping prerequisites and should not all be added blindly to a profile. The probe inventories WAD filenames but does not declare them all mandatory.

No FGD was found in `valve/`. The CS FGD found here may have been added separately: presence does not establish Steam distribution or redistribution rights. Both FGD locations can be overridden independently. Missing editor FGDs should be supplied from a licensed local editor/SDK source, never fabricated by copying an uncertain third-party download. The inspected CS FGD defines CT/T starts and buy/bomb zones without an `@include` dependency.

For another Steam library, pass its exact `steamapps/common/Half-Life` path with `--half-life-dir`. M0 read the real `libraryfolders.vdf` to confirm this workstation, but has not implemented general VDF discovery yet. Native, custom-mount and Flatpak game roots can be provided explicitly; Flatpak Steam launching itself has not been tested.

Original repository Python, documentation and fixture geometry are under the root MIT license. No Valve textures, stock FGDs, paid editor files or third-party compiler source are distributed here. The compiler remains a separate upstream checkout with its own GPL-2.0 license text and libzip/zlib notices. Review those upstream files before distributing compiler binaries. The smoke command uses `-wadtextures` and confirms zero embedded textures; source geometry is original but stock WADs remain external. Generated build outputs are ignored.
