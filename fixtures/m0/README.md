# Original M0 room

`sdk_m0_room.map` is original, text-authored Valve 220 geometry: six solid brushes around a sealed 256 × 256 × 128 interior, one Half-Life player start and one light. It is covered by the repository MIT license. It is a compiler fixture, not the later playable CS arena or a claim of a completed manual JACK round trip.

Texture `-0OUT_WALL3` is referenced by name from the user's installed `valve/halflife.wad`; no texture data or absolute WAD path is stored here. `python3 tools/m0.py smoke` supplies the local WAD search file and keeps textures external in the BSP. In JACK add the same WAD to the profile before opening the MAP.

Manual edits should first be exported into `build/m0/manual/` for the pending acceptance test. Preserve intentional source improvements in this directory after review, keeping machine-specific WAD paths out of Git.
