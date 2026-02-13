from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# -----------------------------
# Config
# -----------------------------

@dataclass(frozen=True)
class CanvasSpec:
    width: int = 1080
    height: int = 1350


@dataclass(frozen=True)
class SpacingSpec:
    margin: int = 48
    header_h: int = 120
    title_y: int = 135
    content_top: int = 185          # top of first frame
    bottom_margin: int = 48
    gap_between_frames: int = 24    # vertical gap between stacked frames
    frame_padding: int = 12         # padding inside each frame around the screenshot


@dataclass(frozen=True)
class StyleSpec:
    # Colors (RGBA)
    bg: Tuple[int, int, int, int] = (12, 18, 30, 255)
    header_bg: Tuple[int, int, int, int] = (18, 27, 45, 255)
    navy: Tuple[int, int, int, int] = (18, 27, 45, 255)
    white: Tuple[int, int, int, int] = (255, 255, 255, 255)
    title_color: Tuple[int, int, int, int] = (220, 228, 245, 255)
    aws_orange: Tuple[int, int, int, int] = (255, 153, 0, 255)

    # Frame
    frame_radius: int = 18
    shadow_blur: int = 16
    shadow_opacity: int = 80
    shadow_offset_y: int = 4

    # Logo
    logo_target_h: int = 72


@dataclass(frozen=True)
class TypographySpec:
    badge_font_size: int = 38
    title_font_size: int = 30
    page_font_size: int = 22
    label_font_size: int = 28
    label_gap: int = 14            # space between label text and the frame below it

    badge_pad_x: int = 22
    badge_pad_y: int = 12
    badge_radius: int = 24


@dataclass(frozen=True)
class RenderConfig:
    canvas: CanvasSpec = CanvasSpec()
    spacing: SpacingSpec = SpacingSpec()
    style: StyleSpec = StyleSpec()
    typo: TypographySpec = TypographySpec()


# -----------------------------
# Utilities
# -----------------------------

def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def normalize_title(dir_name: str) -> str:
    return dir_name.replace("_", " ").replace("-", " ").strip()


def iter_images(folder: Path) -> List[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    return [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in exts]


def add_shadow(canvas: Image.Image, box: Tuple[int, int, int, int], cfg: RenderConfig):
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


# -----------------------------
# Measure screenshots to plan page layout
# -----------------------------

@dataclass
class ScreenSlot:
    """A screenshot scaled to fit the available width, with its frame dimensions."""
    path: Path
    label: str
    scaled_w: int
    scaled_h: int
    frame_w: int
    frame_h: int       # frame only (without label)
    total_h: int       # label + gap + frame


def image_label(path: Path) -> str:
    """Extract a human-readable label from a filename like '1.2-bia-browser.png'.
    Strips the number prefix and extension, replaces dashes with spaces."""
    stem = path.stem                       # '1.2-bia-browser'
    label = re.sub(r"^\d+\.\d+[-\s]*", "", stem)  # 'bia-browser'
    return label.replace("-", " ").strip()


def measure_screenshot(img_path: Path, avail_w: int, cfg: RenderConfig) -> ScreenSlot:
    """Scale screenshot to fill available width; compute tight frame size."""
    img = Image.open(img_path)
    w, h = img.size
    pad = cfg.spacing.frame_padding

    inner_w = avail_w - 2 * pad
    scale = inner_w / w
    scaled_w = inner_w
    scaled_h = max(1, int(h * scale))

    frame_w = avail_w
    frame_h = scaled_h + 2 * pad

    # Measure label height
    label = image_label(img_path)
    label_font = load_font(cfg.typo.label_font_size, bold=True)
    tb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), label.upper(), font=label_font)
    label_h = tb[3] - tb[1]
    total_h = label_h + cfg.typo.label_gap + frame_h

    return ScreenSlot(
        path=img_path,
        label=label,
        scaled_w=scaled_w,
        scaled_h=scaled_h,
        frame_w=frame_w,
        frame_h=frame_h,
        total_h=total_h,
    )


def image_group_key(path: Path) -> str:
    """Extract the group prefix from a filename like '1.2-name.png' -> '1'.
    Images with the same first number must stay on the same page."""
    m = re.match(r"^(\d+)\.", path.name)
    return m.group(1) if m else path.name


def group_slots(slots: List[ScreenSlot]) -> List[List[ScreenSlot]]:
    """Group slots by their first-number prefix, preserving order."""
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
    """Pack screenshots into pages.
    Images sharing the same first-number prefix are kept together on one page.
    Groups that don't share a prefix go on separate pages.
    Within a page, if a group doesn't fit vertically it overflows to a new page."""
    avail_h = cfg.canvas.height - cfg.spacing.content_top - cfg.spacing.bottom_margin
    gap = cfg.spacing.gap_between_frames

    groups = group_slots(slots)
    pages: List[List[ScreenSlot]] = []

    for group in groups:
        # Each group starts a new page
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


# -----------------------------
# Drawing
# -----------------------------

def draw_header(canvas: Image.Image, logo_path: Path, cfg: RenderConfig):
    draw = ImageDraw.Draw(canvas)
    W = cfg.canvas.width

    # Header background
    draw.rectangle([0, 0, W, cfg.spacing.header_h], fill=cfg.style.header_bg)

    # Logo
    logo = Image.open(logo_path).convert("RGBA")
    target_h = cfg.style.logo_target_h
    scale = target_h / logo.size[1]
    logo = logo.resize((int(logo.size[0] * scale), target_h), Image.LANCZOS)

    lx = cfg.spacing.margin
    ly = (cfg.spacing.header_h - target_h) // 2
    canvas.alpha_composite(logo, (lx, ly))

    # Badge "Desafio AWS"
    badge_text = "Desafio AWS"
    font = load_font(cfg.typo.badge_font_size, bold=True)

    tb = draw.textbbox((0, 0), badge_text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]

    bx1 = W - cfg.spacing.margin
    bx0 = bx1 - (tw + cfg.typo.badge_pad_x * 2)
    by0 = (cfg.spacing.header_h - (th + cfg.typo.badge_pad_y * 2)) // 2
    by1 = by0 + th + cfg.typo.badge_pad_y * 2

    draw.rounded_rectangle(
        [bx0, by0, bx1, by1],
        radius=cfg.typo.badge_radius,
        fill=cfg.style.aws_orange,
    )
    draw.text(
        (bx0 + cfg.typo.badge_pad_x, by0 + cfg.typo.badge_pad_y - 2),
        badge_text,
        font=font,
        fill=cfg.style.navy,
    )


def draw_title_line(canvas: Image.Image, activity_title: str,
                    page_num: int, total_pages: int, cfg: RenderConfig):
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(cfg.typo.title_font_size, bold=True)
    page_font = load_font(cfg.typo.page_font_size, bold=False)

    y = cfg.spacing.title_y
    draw.text((cfg.spacing.margin, y), activity_title,
              font=title_font, fill=cfg.style.title_color)

    if total_pages > 1:
        page_text = f"{page_num}/{total_pages}"
        tb = draw.textbbox((0, 0), page_text, font=page_font)
        tw = tb[2] - tb[0]
        draw.text((cfg.canvas.width - cfg.spacing.margin - tw, y + 6),
                  page_text, font=page_font, fill=cfg.style.title_color)


def draw_framed_screenshot(canvas: Image.Image, slot: ScreenSlot,
                           x: int, y: int, cfg: RenderConfig):
    """Draw a label above, then a white rounded-rect frame with the screenshot."""
    draw = ImageDraw.Draw(canvas)

    # Label (all caps, aligned with frame content)
    label_font = load_font(cfg.typo.label_font_size, bold=True)
    label_text = slot.label.upper()
    pad = cfg.spacing.frame_padding
    draw.text((x + pad, y), label_text, font=label_font, fill=cfg.style.title_color)
    tb = draw.textbbox((0, 0), label_text, font=label_font)
    label_h = tb[3] - tb[1]

    frame_y = y + label_h + cfg.typo.label_gap
    frame_box = (x, frame_y, x + slot.frame_w, frame_y + slot.frame_h)

    # Shadow
    add_shadow(canvas, frame_box, cfg)

    # White frame
    draw.rounded_rectangle(frame_box, radius=cfg.style.frame_radius, fill=cfg.style.white)

    # Screenshot
    sc = Image.open(slot.path).convert("RGBA")
    sc = sc.resize((slot.scaled_w, slot.scaled_h), Image.LANCZOS)

    pad = cfg.spacing.frame_padding
    px = x + pad
    py = frame_y + pad
    canvas.alpha_composite(sc, (px, py))


def render_page(logo: Path, activity_title: str, page_num: int,
                total_pages: int, slots: List[ScreenSlot],
                out_path: Path, cfg: RenderConfig) -> Image.Image:
    canvas = Image.new("RGBA", (cfg.canvas.width, cfg.canvas.height), cfg.style.bg)

    draw_header(canvas, logo, cfg)
    draw_title_line(canvas, activity_title, page_num, total_pages, cfg)

    # Compute total content height to center vertically in the available space
    gap = cfg.spacing.gap_between_frames
    total_h = sum(s.total_h for s in slots) + gap * (len(slots) - 1)
    avail_h = cfg.canvas.height - cfg.spacing.content_top - cfg.spacing.bottom_margin
    start_y = cfg.spacing.content_top + (avail_h - total_h) // 2

    x = cfg.spacing.margin
    cur_y = start_y
    for slot in slots:
        draw_framed_screenshot(canvas, slot, x, cur_y, cfg)
        cur_y += slot.total_h + gap

    rgb = canvas.convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(out_path, "PNG", optimize=True)
    return rgb


# -----------------------------
# CLI
# -----------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Generate LinkedIn carousel pages from activity screenshots.")
    ap.add_argument("--in_root", required=True, help="Root folder with activity subfolders")
    ap.add_argument("--out_dir", required=True, help="Output folder")
    ap.add_argument("--logo", required=True, help="Path to logo PNG")

    # Canvas
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1350)

    # Spacing
    ap.add_argument("--margin", type=int, default=48)
    ap.add_argument("--frame_pad", type=int, default=12, help="Padding inside each frame")
    ap.add_argument("--gap", type=int, default=24, help="Gap between stacked frames")

    args = ap.parse_args()

    cfg = RenderConfig(
        canvas=CanvasSpec(width=args.width, height=args.height),
        spacing=SpacingSpec(
            margin=args.margin,
            frame_padding=args.frame_pad,
            gap_between_frames=args.gap,
        ),
    )

    in_root = Path(args.in_root)
    out_dir = Path(args.out_dir)
    logo = Path(args.logo)

    for act_dir in sorted([p for p in in_root.iterdir() if p.is_dir()]):
        imgs = iter_images(act_dir)
        if not imgs:
            continue

        title = normalize_title(act_dir.name)
        avail_w = cfg.canvas.width - 2 * cfg.spacing.margin

        # Measure all screenshots and compute tight frame sizes
        slots = [measure_screenshot(p, avail_w, cfg) for p in imgs]

        # Pack into pages based on available vertical space
        pages = paginate(slots, cfg)

        rendered: List[Image.Image] = []
        for idx, page_slots in enumerate(pages, start=1):
            out_name = f"{act_dir.name}_p{idx:02d}.png"
            img = render_page(
                logo=logo,
                activity_title=title,
                page_num=idx,
                total_pages=len(pages),
                slots=page_slots,
                out_path=out_dir / out_name,
                cfg=cfg,
            )
            rendered.append(img)
            print("Wrote", out_dir / out_name)

        # Save all pages as a single PDF for this activity
        pdf_path = out_dir / f"{act_dir.name}.pdf"
        rendered[0].save(pdf_path, "PDF", save_all=True,
                         append_images=rendered[1:], resolution=150)
        print("Wrote", pdf_path)


if __name__ == "__main__":
    main()
