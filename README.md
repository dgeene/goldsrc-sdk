# GoldSrc Mapping SDK

A Linux-first, reproducible workspace for creating maps for **Half-Life 1** and **Counter-Strike 1.6**. The goal is to keep map sources, configuration, build recipes, and setup instructions in Git while using your own Steam installations for game assets.

**Status:** Planned. The repository implementation is described in [PLAN.md](PLAN.md); the commands below are the intended interface, not yet available in an empty repository.

## Target setup

- Ubuntu 24.04 x86_64 with the native Steam installation
- Legitimate Half-Life 1 and Counter-Strike 1.6 installations
- Native Linux J.A.C.K. as the primary map editor
- A pinned, locally runnable GoldSrc map compiler

The editor and games run on the Linux host with normal GPU access. A containerized compiler and Hammer under Wine are later options. Valve game files and the J.A.C.K. application are **not** included in this repository.

## Intended workflow

Once implemented, setup and mapping should look like this:

```bash
./goldsrc bootstrap
./goldsrc doctor --game valve
./goldsrc doctor --game cstrike
./goldsrc configure-editor jack --game valve
./goldsrc configure-editor jack --game cstrike
./goldsrc build projects/example --profile fast
./goldsrc build projects/example-cstrike --profile fast
./goldsrc install projects/example --game valve --dry-run
./goldsrc install projects/example-cstrike --game cstrike --dry-run
```

The two example projects will be a playable Half-Life room and a small Counter-Strike arena. Source `.map` files belong in Git; generated BSPs and machine-specific paths do not. Distributable BSPs should not embed their original `.map` source by default.

## Build this repository with Codex

Add [PLAN.md](PLAN.md) to the repository root and ask Codex to follow its **Agent handoff** section. Start with toolchain verification and machine discovery, then implement the milestones and their acceptance checks in order. The plan records confirmed choices, layout, tests, and licensing boundaries.
