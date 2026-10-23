# For coding agents

- Picking up work in this checkout: read `docs/HANDOVER.md` first. It says where the work stopped, what the hard requirements are, and what is still missing.
- Building, running the checks, or debugging a reported in-game bug: read `docs/local-environment.md` first. It covers where the game logs live, the decompile tool, and the two build traps.
- Panel, play modes, keys, panel text: read `docs/ui-development.md` first, then `CONTRIBUTING.md`.
- Combat simulator and other characters: read `CONTRIBUTING.md` and the documents it lists.
- One feature per pull request against `main`. Run the checks the guide lists and report in the PR which ones ran, which passed and what was tested in the game.
- Do not change search, valuation or potion policy unless the issue asks for it, and never commit game JARs, decompiled code, game assets or build output.
- Card behaviour comes from the game's bytecode, never from exported tables like `sts_cards.json`: those carry final numbers but not the branches that decide when the numbers apply. Decompile with `E:\sts-devkit\decompiled\decompile.sh`.
