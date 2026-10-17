# TESTING MODS - dated, self-contained copies of the mod for testing.

Layout: <stamp>-<description>/water-ford/ = a full copy of mods/water-ford/mod
as of that stamp. Copies are loadable Factorio mod directories: point the dev
games --mod-directory at a stamp folder to load that state instead of the real
mod. They are never auto-loaded: the dev launcher (testing/scratch/config.ini)
normally points at testing/scratch/mods, which is a SYMLINK to the real
mods/water-ford/mod, so every scratch game session runs the real working
files. If a copy must load side-by-side with the real mod, rename its
info.json name field first (two mods with the same name cannot coexist).

Snapshots:
- 2026-10-17-boards-16-16-16/ - pre-promotion state: water-ford still on the
  old planks.png deck art (frozen config), three-depth dev compare tilesets
  (boards-land-a/b/c, boards-ford-a/b/c), 16/16/16 C size ladder.
