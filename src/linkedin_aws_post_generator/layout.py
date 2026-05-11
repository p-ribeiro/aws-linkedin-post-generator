from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw

from .config import RenderConfig
from .utils import load_font, wrap_text


@dataclass
class ScreenSlot:
    """A screenshot scaled to fit the available width, with its frame dimensions."""
    path: Path
    label: str
    label_lines: List[str]
    scaled_w: int
    scaled_h: int
    frame_w: int
    frame_h: int   # frame only (without label)
    total_h: int   # label + gap + frame


def image_label(path: Path) -> str:
    """Return a human-readable label from a filename like '1.2-bia-browser.png'."""
    stem = path.stem
    label = re.sub(r"^\d+\.\d+[-\s]*", "", stem)
    # Replace dashes with spaces only outside single-quoted sections
    label = re.sub(
        r"'[^']*'|[^']+",
        lambda m: m.group() if m.group().startswith("'") else m.group().replace("-", " "),
        label,
    )
    return label.strip()


def image_group_key(path: Path) -> str:
    """Return the group prefix from a filename like '1.2-name.png' -> '1'.

    Images sharing the same first number are kept together on one page.
    """
    m = re.match(r"^(\d+)\.", path.name)
    return m.group(1) if m else path.name


def measure_screenshot(img_path: Path, avail_w: int, cfg: RenderConfig) -> ScreenSlot:
    """Scale a screenshot to fit the available width/height and return its slot."""
    img = Image.open(img_path)
    w, h = img.size
    pad = cfg.spacing.frame_padding

    label = image_label(img_path)
    label_font = load_font(cfg.typo.label_font_size, bold=True)
    label_lines = wrap_text(label, label_font, avail_w)
    tb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), "A", font=label_font)
    line_h = tb[3] - tb[1]
    line_spacing = int(line_h * 0.35)
    label_h = line_h * len(label_lines) + line_spacing * max(0, len(label_lines) - 1)

    inner_w = avail_w - 2 * pad
    avail_h = cfg.canvas.height - cfg.spacing.content_top - cfg.spacing.bottom_margin
    max_inner_h = avail_h - label_h - cfg.typo.label_gap - 2 * pad

    scale_w = inner_w / w
    scale_h = (max_inner_h / h) if max_inner_h > 0 else scale_w
    scale = min(scale_w, scale_h)

    scaled_w = max(1, int(w * scale))
    scaled_h = max(1, int(h * scale))
    frame_w = scaled_w + 2 * pad
    frame_h = scaled_h + 2 * pad
    total_h = label_h + cfg.typo.label_gap + frame_h

    return ScreenSlot(
        path=img_path,
        label=label,
        label_lines=label_lines,
        scaled_w=scaled_w,
        scaled_h=scaled_h,
        frame_w=frame_w,
        frame_h=frame_h,
        total_h=total_h,
    )


def group_slots(slots: List[ScreenSlot]) -> List[List[ScreenSlot]]:
    groups: Dict[str, List[ScreenSlot]] = {}
    order: List[str] = []
    for slot in slots:
        key = image_group_key(slot.path)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(slot)
    return [groups[k] for k in order]


def paginate(slots: List[ScreenSlot], cfg: RenderConfig) -> List[List[ScreenSlot]]:
    """Pack slots into pages, keeping same-prefix images together."""
    avail_h = cfg.canvas.height - cfg.spacing.content_top - cfg.spacing.bottom_margin
    gap = cfg.spacing.gap_between_frames
    pages: List[List[ScreenSlot]] = []

    for group in group_slots(slots):
        current_page: List[ScreenSlot] = []
        used_h = 0

        for slot in group:
            needed = slot.total_h + (gap if current_page else 0)
            if current_page and used_h + needed > avail_h:
                pages.append(current_page)
                current_page = [slot]
                used_h = slot.total_h
            else:
                if current_page:
                    used_h += gap
                current_page.append(slot)
                used_h += slot.total_h

        if current_page:
            pages.append(current_page)

    return pages
