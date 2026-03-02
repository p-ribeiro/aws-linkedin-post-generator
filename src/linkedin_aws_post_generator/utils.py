from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import ImageFont


_FONT_PATHS = {
    True: [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ],
    False: [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ],
}

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS[bold]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def normalize_title(dir_name: str) -> str:
    return dir_name.replace("_", " ").replace("-", " ").strip()


def iter_images(folder: Path) -> List[Path]:
    return [
        p for p in sorted(folder.iterdir())
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS
    ]
