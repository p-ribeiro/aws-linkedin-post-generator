# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode (dev)
pip install -e .

# Run the generator (defaults: pages/ → result/, logo.png)
linkedin-aws-post-generator

# Process a specific activity
linkedin-aws-post-generator --activity "Nome da Atividade 1"

# Custom paths
linkedin-aws-post-generator --input screenshots --output out --logo minha-logo.png

# Build a distributable wheel
python -m build
```

No test suite exists at the moment — validate by running the CLI against the `pages/` folder and inspecting the `result/` output.

## Architecture

The pipeline is linear: CLI → layout → render → PDF.

- **`cli.py`** — Entry point (`main()`). Walks `--input` subdirectories, drives the full pipeline for each activity, and saves PNGs + a PDF per activity.
- **`config.py`** — Frozen dataclasses (`CanvasSpec`, `SpacingSpec`, `StyleSpec`, `TypographySpec`, `RenderConfig`) holding all visual constants. Pass `RenderConfig` everywhere instead of individual numbers.
- **`layout.py`** — Pure geometry. `measure_screenshot()` scales an image to fit the available width and returns a `ScreenSlot` (scaled size, frame dimensions, label lines). `group_slots()` groups slots by their numeric prefix. `paginate()` packs groups into pages respecting the canvas height.
- **`render.py`** — Pillow drawing. Three public render functions: `render_cover_page()` (from `0.txt`), `render_title_page()` (from `N.txt`), and `render_page()` (one or more screenshots). Private helpers `_draw_header`, `_draw_title_line`, `_draw_framed_screenshot`, and `_draw_*_cube_decoration` are composed inside these.
- **`utils.py`** — Shared helpers: `load_font()` (tries Linux/macOS/Windows paths, falls back to default), `wrap_text()`, `iter_images()`, `_natural_key()` (natural sort for filenames), `selective_upper()` (uppercases text outside single quotes), `normalize_title()`.

## Input conventions

Activity folders live under `pages/`. Files follow `GROUP.ORDER-label.png` naming:

- `0.txt` → cover page (optional)
- `N.txt` → title page inserted before group N images (optional)
- `N.M-description.png` → screenshot; group = N, order within group = M, label = description with dashes as spaces

Output goes to `result/`: one PNG per page (`Name_p00.png` for cover, `_p01.png` … for content) plus a combined PDF (`Name.pdf`).

## Color palette / brand

Dark navy background `(12, 18, 30)`, slightly lighter header `(18, 27, 45)`, AWS orange `(255, 153, 0)`. All colors and sizes live in `StyleSpec` / `TypographySpec` inside `config.py` — do not hardcode them in render or layout code.

## Font loading

`utils.load_font()` tries platform-specific DejaVu/Arial paths. On Linux the package `fonts-dejavu-core` must be installed. There is no bundled font.
