from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter

from .config import RenderConfig
from .layout import ScreenSlot
from .utils import load_font


def _add_shadow(canvas: Image.Image, box: Tuple[int, int, int, int], cfg: RenderConfig) -> None:
    x0, y0, x1, y1 = box
    off_y = cfg.style.shadow_offset_y
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.rounded_rectangle(
        [x0, y0 + off_y, x1, y1 + off_y],
        radius=cfg.style.frame_radius,
        fill=(0, 0, 0, cfg.style.shadow_opacity),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(cfg.style.shadow_blur))
    canvas.alpha_composite(shadow)


def _draw_header(canvas: Image.Image, logo_path: Path, cfg: RenderConfig) -> None:
    draw = ImageDraw.Draw(canvas)
    W = cfg.canvas.width

    draw.rectangle([0, 0, W, cfg.spacing.header_h], fill=cfg.style.header_bg)

    logo = Image.open(logo_path).convert("RGBA")
    target_h = cfg.style.logo_target_h
    scale = target_h / logo.size[1]
    logo = logo.resize((int(logo.size[0] * scale), target_h), Image.Resampling.LANCZOS)
    lx = cfg.spacing.margin
    ly = (cfg.spacing.header_h - target_h) // 2
    canvas.alpha_composite(logo, (lx, ly))

    badge_text = "Desafio AWS"
    font = load_font(cfg.typo.badge_font_size, bold=True)
    tb = draw.textbbox((0, 0), badge_text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]

    bx1 = W - cfg.spacing.margin
    bx0 = bx1 - (tw + cfg.typo.badge_pad_x * 2)
    by0 = (cfg.spacing.header_h - (th + cfg.typo.badge_pad_y * 2)) // 2
    by1 = by0 + th + cfg.typo.badge_pad_y * 2

    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=cfg.typo.badge_radius, fill=cfg.style.aws_orange)
    draw.text((bx0 + cfg.typo.badge_pad_x, by0 + cfg.typo.badge_pad_y - 2), badge_text, font=font, fill=cfg.style.navy)


def _draw_title_line(canvas: Image.Image, activity_title: str,
                     page_num: int, total_pages: int, cfg: RenderConfig) -> None:
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(cfg.typo.title_font_size, bold=True)
    page_font = load_font(cfg.typo.page_font_size, bold=False)

    y = cfg.spacing.title_y
    draw.text((cfg.spacing.margin, y), activity_title, font=title_font, fill=cfg.style.title_color)

    if total_pages > 1:
        page_text = f"{page_num}/{total_pages}"
        tb = draw.textbbox((0, 0), page_text, font=page_font)
        tw = tb[2] - tb[0]
        draw.text((cfg.canvas.width - cfg.spacing.margin - tw, y + 6),
                  page_text, font=page_font, fill=cfg.style.title_color)


def _draw_framed_screenshot(canvas: Image.Image, slot: ScreenSlot,
                             x: int, y: int, cfg: RenderConfig) -> None:
    draw = ImageDraw.Draw(canvas)
    label_font = load_font(cfg.typo.label_font_size, bold=True)
    label_text = slot.label.upper()
    pad = cfg.spacing.frame_padding

    draw.text((x + pad, y), label_text, font=label_font, fill=cfg.style.title_color)
    tb = draw.textbbox((0, 0), label_text, font=label_font)
    label_h = tb[3] - tb[1]

    frame_y = y + int(label_h) + cfg.typo.label_gap
    frame_box = (x, frame_y, x + slot.frame_w, frame_y + slot.frame_h)

    _add_shadow(canvas, frame_box, cfg)
    draw.rounded_rectangle(frame_box, radius=cfg.style.frame_radius, fill=cfg.style.white)

    sc = Image.open(slot.path).convert("RGBA")
    sc = sc.resize((slot.scaled_w, slot.scaled_h), Image.Resampling.LANCZOS)
    canvas.alpha_composite(sc, (x + pad, frame_y + pad))


def render_page(
    logo: Path,
    activity_title: str,
    page_num: int,
    total_pages: int,
    slots: List[ScreenSlot],
    out_path: Path,
    cfg: RenderConfig,
) -> Image.Image:
    canvas = Image.new("RGBA", (cfg.canvas.width, cfg.canvas.height), cfg.style.bg)

    _draw_header(canvas, logo, cfg)
    _draw_title_line(canvas, activity_title, page_num, total_pages, cfg)

    gap = cfg.spacing.gap_between_frames
    total_h = sum(s.total_h for s in slots) + gap * (len(slots) - 1)
    avail_h = cfg.canvas.height - cfg.spacing.content_top - cfg.spacing.bottom_margin
    start_y = cfg.spacing.content_top + (avail_h - total_h) // 2

    avail_w = cfg.canvas.width - 2 * cfg.spacing.margin
    cur_y = start_y
    for slot in slots:
        x = cfg.spacing.margin + (avail_w - slot.frame_w) // 2
        _draw_framed_screenshot(canvas, slot, x, cur_y, cfg)
        cur_y += slot.total_h + gap

    rgb = canvas.convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(out_path, "PNG", optimize=True)
    return rgb
