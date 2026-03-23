from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter

from .config import RenderConfig
from .layout import ScreenSlot
from .utils import load_font, wrap_text


def _add_shadow(
    canvas: Image.Image, box: Tuple[int, int, int, int], cfg: RenderConfig
) -> None:
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

    badge_text = "Formação AWS 5.0"
    font = load_font(cfg.typo.badge_font_size, bold=True)
    tb = draw.textbbox((0, 0), badge_text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]

    bx1 = W - cfg.spacing.margin
    bx0 = bx1 - (tw + cfg.typo.badge_pad_x * 2)
    by0 = (cfg.spacing.header_h - (th + cfg.typo.badge_pad_y * 2)) // 2
    by1 = by0 + th + cfg.typo.badge_pad_y * 2

    draw.rounded_rectangle(
        [bx0, by0, bx1, by1], radius=cfg.typo.badge_radius, fill=cfg.style.aws_orange
    )
    draw.text(
        (bx0 + cfg.typo.badge_pad_x, by0 + cfg.typo.badge_pad_y - 2),
        badge_text,
        font=font,
        fill=cfg.style.navy,
    )


def _draw_title_line(
    canvas: Image.Image,
    activity_title: str,
    page_num: int,
    total_pages: int,
    cfg: RenderConfig,
) -> None:
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(cfg.typo.title_font_size, bold=True)
    page_font = load_font(cfg.typo.page_font_size, bold=False)

    y = cfg.spacing.title_y
    draw.text(
        (cfg.spacing.margin, y),
        activity_title,
        font=title_font,
        fill=cfg.style.title_color,
    )

    if total_pages > 1:
        page_text = f"{page_num}/{total_pages}"
        tb = draw.textbbox((0, 0), page_text, font=page_font)
        tw = tb[2] - tb[0]
        draw.text(
            (cfg.canvas.width - cfg.spacing.margin - tw, y + 6),
            page_text,
            font=page_font,
            fill=cfg.style.title_color,
        )


def _draw_framed_screenshot(
    canvas: Image.Image, slot: ScreenSlot, x: int, y: int, cfg: RenderConfig
) -> None:
    draw = ImageDraw.Draw(canvas)
    label_font = load_font(cfg.typo.label_font_size, bold=True)
    pad = cfg.spacing.frame_padding

    tb = draw.textbbox((0, 0), "A", font=label_font)
    line_h = tb[3] - tb[1]
    line_spacing = int(line_h * 0.2)
    cur_label_y = y
    for line in slot.label_lines:
        draw.text(
            (x + pad, cur_label_y), line, font=label_font, fill=cfg.style.title_color
        )
        cur_label_y += line_h + line_spacing
    label_h = line_h * len(slot.label_lines) + line_spacing * max(
        0, len(slot.label_lines) - 1
    )

    frame_y = y + int(label_h) + cfg.typo.label_gap
    frame_box = (x, frame_y, x + slot.frame_w, frame_y + slot.frame_h)

    _add_shadow(canvas, frame_box, cfg)
    draw.rounded_rectangle(
        frame_box, radius=cfg.style.frame_radius, fill=cfg.style.white
    )

    sc = Image.open(slot.path).convert("RGBA")
    sc = sc.resize((slot.scaled_w, slot.scaled_h), Image.Resampling.LANCZOS)
    canvas.alpha_composite(sc, (x + pad, frame_y + pad))


def _draw_isometric_cube(
    layer: Image.Image,
    cx: int,
    cy: int,
    s: int,
    color: Tuple[int, int, int, int],
    line_w: int,
) -> None:
    """Draw an isometric cube outline on a transparent layer."""
    draw = ImageDraw.Draw(layer)
    c = int(s * 0.866)  # cos 30°
    h = s // 2  # sin 30°

    pts = {
        "T": (cx, cy),
        "R": (cx + c, cy + h),
        "M": (cx, cy + s),
        "L": (cx - c, cy + h),
        "BR": (cx + c, cy + h + s),
        "B": (cx, cy + 2 * s),
        "BL": (cx - c, cy + h + s),
    }

    fill = (*color[:3], 18)
    draw.polygon([pts["T"], pts["R"], pts["M"], pts["L"]], fill=fill)
    draw.polygon([pts["R"], pts["BR"], pts["B"], pts["M"]], fill=fill)
    draw.polygon([pts["L"], pts["M"], pts["B"], pts["BL"]], fill=fill)

    edges = [
        ("T", "R"),
        ("R", "M"),
        ("M", "L"),
        ("L", "T"),
        ("R", "BR"),
        ("BR", "B"),
        ("B", "M"),
        ("L", "BL"),
        ("BL", "B"),
    ]
    for a, b in edges:
        draw.line([pts[a], pts[b]], fill=color, width=line_w)


def _draw_cube_decoration(canvas: Image.Image, cfg: RenderConfig) -> None:
    """Draw floating isometric cubes on the right side of the canvas."""
    W, H = cfg.canvas.width, cfg.canvas.height
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    line_w = max(4, W // 810)

    orange = cfg.style.aws_orange
    white = cfg.style.white

    # (cx_frac, cy_frac, size_frac, base_color, alpha)
    cubes = [
        # top cluster
        (0.84, 0.14, 0.100, orange, 230),
        (0.98, 0.21, 0.095, white, 155),
        (0.73, 0.22, 0.070, white, 135),
        # mid-top cluster
        (0.89, 0.31, 0.085, orange, 205),
        (0.77, 0.38, 0.060, white, 125),
        (0.94, 0.40, 0.075, orange, 180),
        # mid cluster
        (0.82, 0.50, 0.055, white, 120),
        (0.91, 0.53, 0.065, orange, 160),
        (0.72, 0.55, 0.045, white, 100),
        # mid-bottom cluster
        (0.87, 0.63, 0.070, orange, 150),
        (0.78, 0.67, 0.050, white, 110),
        (0.97, 0.68, 0.060, orange, 135),
        # bottom cluster
        (0.84, 0.77, 0.055, white, 100),
        (0.92, 0.80, 0.065, orange, 130),
    ]

    for cx_f, cy_f, sz_f, base, alpha in cubes:
        _draw_isometric_cube(
            layer,
            int(cx_f * W),
            int(cy_f * H),
            int(sz_f * W),
            (*base[:3], alpha),
            line_w,
        )

    canvas.alpha_composite(layer)


def _draw_cover_cube_decoration(canvas: Image.Image, cfg: RenderConfig) -> None:
    """Draw floating isometric cubes in the four corners for the cover page."""
    W, H = cfg.canvas.width, cfg.canvas.height
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    line_w = max(4, W // 810)

    orange = cfg.style.aws_orange
    white = cfg.style.white

    cubes = [
        # top-left corner
        (0.07, 0.06, 0.085, orange, 220),
        (0.17, 0.10, 0.065, white, 150),
        (0.04, 0.17, 0.055, white, 130),
        (0.13, 0.20, 0.050, orange, 160),
        # top-right corner
        (0.93, 0.06, 0.085, orange, 220),
        (0.83, 0.10, 0.065, white, 150),
        (0.96, 0.17, 0.055, white, 130),
        (0.87, 0.20, 0.050, orange, 160),
        # bottom-left corner
        (0.07, 0.88, 0.080, orange, 200),
        (0.17, 0.84, 0.060, white, 140),
        (0.04, 0.80, 0.050, white, 120),
        # bottom-right corner
        (0.93, 0.88, 0.080, orange, 200),
        (0.83, 0.84, 0.060, white, 140),
        (0.96, 0.80, 0.050, white, 120),
    ]

    for cx_f, cy_f, sz_f, base, alpha in cubes:
        _draw_isometric_cube(
            layer,
            int(cx_f * W),
            int(cy_f * H),
            int(sz_f * W),
            (*base[:3], alpha),
            line_w,
        )

    canvas.alpha_composite(layer)


def render_cover_page(
    logo: Path,
    activity_title: str,
    cover_text: str,
    out_path: Path,
    cfg: RenderConfig,
) -> Image.Image:
    """Render a cover page using cover_text (from 0.txt) as the main centered title."""
    W, H = cfg.canvas.width, cfg.canvas.height
    canvas = Image.new("RGBA", (W, H), cfg.style.bg)
    draw = ImageDraw.Draw(canvas)

    # --- Logo centered at top ---
    logo_img = Image.open(logo).convert("RGBA")
    logo_h = int(H * 0.09)
    scale = logo_h / logo_img.size[1]
    logo_img = logo_img.resize(
        (int(logo_img.size[0] * scale), logo_h), Image.Resampling.LANCZOS
    )
    lx = (W - logo_img.size[0]) // 2
    ly = int(H * 0.08)
    canvas.alpha_composite(logo_img, (lx, ly))

    # --- Orange horizontal accent line below logo ---
    line_y = ly + logo_h + int(H * 0.03)
    line_w_px = int(W * 0.25)
    line_x0 = (W - line_w_px) // 2
    line_thickness = max(4, H // 800)
    draw.rectangle(
        [line_x0, line_y, line_x0 + line_w_px, line_y + line_thickness],
        fill=cfg.style.aws_orange,
    )

    # --- "Formação AWS 5.0" label below the line ---
    badge_font = load_font(cfg.typo.badge_font_size, bold=True)
    badge_text = "Formação AWS 5.0"
    tb = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = tb[2] - tb[0]
    badge_y = line_y + line_thickness + int(H * 0.02)
    draw.text(
        ((W - badge_w) // 2, badge_y),
        badge_text,
        font=badge_font,
        fill=cfg.style.aws_orange,
    )

    # --- Large centered title from 0.txt ---
    font_size = int(W * 0.065)
    font = load_font(font_size, bold=True)
    text_max_w = int(W * 0.70)

    wrapped = wrap_text(cover_text, font, text_max_w)
    line_h = int(draw.textbbox((0, 0), "A", font=font)[3])
    line_spacing = int(line_h * 0.35)
    total_text_h = len(wrapped) * line_h + max(0, len(wrapped) - 1) * line_spacing

    text_area_top = badge_y + int(H * 0.06)
    text_area_bottom = int(H * 0.82)
    text_y = text_area_top + (text_area_bottom - text_area_top - total_text_h) // 2

    for line in wrapped:
        tb = draw.textbbox((0, 0), line, font=font)
        lw = tb[2] - tb[0]
        draw.text(((W - lw) // 2, text_y), line, font=font, fill=cfg.style.white)
        text_y += line_h + line_spacing

    # --- Activity title at the bottom ---
    title_font = load_font(cfg.typo.title_font_size, bold=True)
    tb = draw.textbbox((0, 0), activity_title, font=title_font)
    tw = tb[2] - tb[0]
    draw.text(
        ((W - tw) // 2, int(H * 0.88)),
        activity_title,
        font=title_font,
        fill=cfg.style.title_color,
    )

    # --- Cube decoration in corners ---
    _draw_cover_cube_decoration(canvas, cfg)

    rgb = canvas.convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(out_path, "PNG", optimize=True)
    return rgb


def render_title_page(
    logo: Path,
    activity_title: str,
    body_text: str,
    out_path: Path,
    cfg: RenderConfig,
) -> Image.Image:
    canvas = Image.new("RGBA", (cfg.canvas.width, cfg.canvas.height), cfg.style.bg)
    _draw_header(canvas, logo, cfg)
    _draw_title_line(canvas, activity_title, page_num=0, total_pages=0, cfg=cfg)
    _draw_cube_decoration(canvas, cfg)

    # Large bold text — left-aligned in left ~55% of content area, vertically centered
    draw = ImageDraw.Draw(canvas)
    W = cfg.canvas.width
    margin = cfg.spacing.margin
    font_size = int(W * 0.055)
    font = load_font(font_size, bold=True)

    text_max_w = int(W * 0.54) - margin
    avail_h = cfg.canvas.height - cfg.spacing.content_top - cfg.spacing.bottom_margin

    wrapped = wrap_text(body_text, font, text_max_w)
    line_h = int(draw.textbbox((0, 0), "A", font=font)[3])
    line_spacing = int(line_h * 0.35)
    total_text_h = len(wrapped) * line_h + max(0, len(wrapped) - 1) * line_spacing

    text_y = cfg.spacing.content_top + (int(avail_h * 0.60) - total_text_h) // 2
    for line in wrapped:
        draw.text((margin, text_y), line, font=font, fill=cfg.style.white)
        text_y += line_h + line_spacing

    rgb = canvas.convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(out_path, "PNG", optimize=True)
    return rgb


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
