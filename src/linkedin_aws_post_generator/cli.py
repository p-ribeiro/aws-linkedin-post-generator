from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from PIL import Image

from .config import CanvasSpec, RenderConfig, SpacingSpec
from .layout import measure_screenshot, paginate
from .render import render_page
from .utils import iter_images, normalize_title


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate LinkedIn carousel images from AWS activity screenshots."
    )
    ap.add_argument("--in_root", required=True, help="Root folder with activity subfolders")
    ap.add_argument("--out_dir", required=True, help="Output folder")
    ap.add_argument("--logo", required=True, help="Path to logo PNG")

    ap.add_argument("--activity", action="append", metavar="NAME",
                    help="Only process this activity folder (can be repeated)")

    ap.add_argument("--width", type=int, default=3240, help="Canvas width in pixels")
    ap.add_argument("--height", type=int, default=4050, help="Canvas height in pixels")
    ap.add_argument("--margin", type=int, default=144, help="Horizontal margin in pixels")
    ap.add_argument("--frame_pad", type=int, default=36, help="Padding inside each frame")
    ap.add_argument("--gap", type=int, default=72, help="Gap between stacked frames")

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

    allowed = set(args.activity) if args.activity else None

    for act_dir in sorted(p for p in in_root.iterdir() if p.is_dir()):
        if allowed and act_dir.name not in allowed:
            continue
        imgs = iter_images(act_dir)
        if not imgs:
            continue

        title = normalize_title(act_dir.name)
        avail_w = cfg.canvas.width - 2 * cfg.spacing.margin
        slots = [measure_screenshot(p, avail_w, cfg) for p in imgs]
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

        pdf_path = out_dir / f"{act_dir.name}.pdf"
        rendered[0].save(pdf_path, "PDF", save_all=True, append_images=rendered[1:], resolution=300)
        print("Wrote", pdf_path)
