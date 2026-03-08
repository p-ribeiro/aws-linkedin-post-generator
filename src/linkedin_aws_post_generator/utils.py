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


def selective_upper(text: str) -> str:
    """Uppercase text except for content inside single quotes, which is kept as-is."""
    import re
    return re.sub(
        r"'[^']*'|[^']+",
        lambda m: m.group() if m.group().startswith("'") else m.group().upper(),
        text,
    )


def wrap_text(text: str, font, max_w: int) -> List[str]:
    """Word-wrap *text* so each line fits within *max_w* pixels."""
    from PIL import ImageDraw, Image as _Image
    draw = ImageDraw.Draw(_Image.new("RGBA", (1, 1)))
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def _natural_key(p: Path) -> tuple:
    import re
    parts = re.split(r'(\d+)', p.stem)
    return tuple(int(x) if x.isdigit() else x.lower() for x in parts)


def iter_images(folder: Path) -> List[Path]:
    return [
        p for p in sorted(folder.iterdir(), key=_natural_key)
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS
    ]
