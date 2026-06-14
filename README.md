# Fleet Manager

A lightweight, fully offline desktop tool for **EVE Online** fleet commanders that
fairly distributes the number of characters (clients/windows) each pilot brings to a
fleet, up to the hard cap of **60 characters**.

Built natively with **PySide6 (Qt)** and packaged into a single Windows `.exe` with
**PyInstaller** — no browser, no internet connection, and no installation required.

## What problem it solves

In a multiboxing fleet every pilot can run a different number of clients. Some can
field many, some only a few. The commander needs an *even* spread so the fleet reaches
60 characters without overloading anyone. Fleet Manager computes, for each pilot,
exactly how many characters they should bring up — and gives the commander a clear
"+/-" command to relay to each pilot.

## How the distribution works

The core is a **water-filling** algorithm with per-pilot caps:

1. The target total is `min(60, sum of all pilots' maximums)`.
2. Characters are handed out evenly. Any pilot who hits their personal maximum is
   "capped" and drops out of the pool — the surplus flows to the pilots who can still
   take more (the queue skips to the next person).
3. Any leftover (when the total doesn't divide evenly) is distributed one-by-one
   following the **current sort order**, so the ordering is deterministic and fair.

The algorithm lives in `core/distribution.py` as a pure function and is covered by
unit tests in `tests/test_distribution.py`.

## Features

- **Add pilots** by name + maximum number of windows they can field.
- **Fair-share calculation** — each pilot's "target" count is computed automatically.
- **Per-pilot command** — a coloured `+N` / `−N` hint tells the commander how many
  windows each pilot should add or drop.
- **Confirmation checkbox** — the commander ticks it once a pilot has changed their
  window count; the pilot's "current" value then matches the target.
- **Live fleet gauge** — a one-line `FLEET  X / 60` readout with a progress bar that
  reflects the **actual** number of windows currently up. It turns **red** when the
  fleet exceeds 60.
- **Duplicate detection** — pilots added twice (same name, case-insensitive) are
  flagged in red with a `⚠` icon.
- **Sorting** — alphabetical `A→Z` / `Z→A`, or by invitation time (one button that
  toggles oldest/newest). The sort order also drives the fair-share queue.
- **Always-on-top** toggle in the header — keep the window above the EVE client.
- **Remembers** window position, size, theme and the always-on-top state between runs.
- **EVE-styled dark themes** — Default plus Amarr / Gallente / Caldari / Minmatar
  faction accents.

## Tech & data

- **Stack:** Python + PySide6 (Qt Widgets), packaged with PyInstaller.
- **Fleet data is in-memory only** — the pilot list is never written to disk and resets
  when the app closes. Only window settings are persisted, to `fleet_config.json` next
  to the executable.
- Fully offline — no ESI / network calls.

## Run from source

```
pip install -r requirements.txt
python main.py                                 # launch the app
python -m unittest discover -s tests -v        # run the algorithm tests
```

## Build the executable

```
python -m PyInstaller build.spec --noconfirm
```

The single-file build is produced at `dist/Fleet Manager.exe` (~44 MB). Double-click
to run — no install, no browser, no internet.

## Project layout

```
main.py                     entry point (QApplication + theme + window)
config.py                   window/theme settings persistence
core/
  distribution.py           fair-share water-filling algorithm (pure, tested)
  sorting.py                sort modes
ui/
  styles.py                 dark EVE QSS theme + faction presets
  main_window.py            the main window
tests/
  test_distribution.py      unit tests for the algorithm
build.spec                  PyInstaller build spec
```
