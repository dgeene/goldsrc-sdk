# M0 compiler experiment

`versions.lock.toml` pins **hltools 1.24.0**, commit `fc5500439a04c3962e99af75589f96ca6b99afa5`. The original source is fetched into `.local/src/hltools`; it is not vendored. See upstream [source and build recipe at the pin](https://github.com/speedrun-16/hltools/tree/fc5500439a04c3962e99af75589f96ca6b99afa5), [LICENSE](https://github.com/speedrun-16/hltools/blob/fc5500439a04c3962e99af75589f96ca6b99afa5/LICENSE), and [third-party notices](https://github.com/speedrun-16/hltools/blob/fc5500439a04c3962e99af75589f96ca6b99afa5/THIRD_PARTY_NOTICES.md).

```bash
python3 tools/build_compiler.py --jobs 4
python3 tools/m0.py smoke
```

The build script checks the full revision and refuses tracked source modifications. It runs:

```bash
cmake -S .local/src/hltools -B .local/src/hltools/build \
  -DCMAKE_BUILD_TYPE=Release -DHLTOOLS_GPU=OFF
cmake --build .local/src/hltools/build --target hltools --parallel 4
.local/src/hltools/bin/hltools compile -h
```

Dependencies: CMake 3.21+, Git, a C compiler and C++17 compiler, Make (default CMake generator). Tested GCC 13.3.0, CMake 3.28.3. CMake downloads zlib 1.3.1 and libzip 1.11.4, validates their pinned SHA-256 hashes, and links them statically. GPU support is explicitly off; no Vulkan SDK is needed. The AES-disabled CMake warning is expected because the build disables crypto backends. Re-running does not update the pin. An interrupted clone must be inspected/repaired manually; the script never deletes existing source.

The smoke helper stages the original fixture and a quoted WAD search file in a unique `build/m0/smoke-*` directory, then runs an argument array equivalent to:

```text
hltools compile -noembedsource -wadtextures -threads 2 -wadcfgfile <stage>/wad.cfg <stage>/sdk_m0_room.map
hltools bsp info <stage>/sdk_m0_room.bsp
```

The compiler writes beside the input map, regardless of the caller's working directory. Observed outputs: `.bsp`, `.prt`, `.ext`, and a `logs/` directory (empty in this run). The helper also captures `compile.log`, `bsp-info.log`, input/compiler/WAD/output hashes and command arguments in `report.json`. Failed runs keep their logs. `--compiler` allows an explicitly supplied binary; its hash is recorded, but the report's `expected_revision` is **not** proof that an override came from that source. `compiler-build.json` records the revision of the locally built compiler.

`-noembedsource` is mandatory in this experiment. `inspect` independently checks the BSP30 header, nonempty lumps, bounds/overlaps and EOF after at most three alignment bytes; it rejects ZIP archives and other appended data. This strict guard targets this pinned output layout, not every extended BSP format, and does not replace an engine playtest.

`-wadtextures` keeps the fixture's stock textures in the installed WAD rather than embedding them. No WADs are copied into the stage. WAD paths with spaces/Unicode are quoted; quotes/newlines cannot be represented by the upstream WAD tokenizer and are rejected with a diagnostic.

The pin is a tested M0 candidate, not a general compatibility claim: upstream describes hltools as work in progress. The manual game-load exit test remains required before adopting it for M3. Keep the lock, build transcript, fixture and source snapshot when preserving the toolchain. Current BSP output includes a timestamp, so repeated output is not byte identical.
