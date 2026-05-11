from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class CanvasSpec:
    width: int = 3240
    height: int = 4050


@dataclass(frozen=True)
class SpacingSpec:
    margin: int = 144
    header_h: int = 360
    title_y: int = 405
    content_top: int = 555  # top of first frame
    bottom_margin: int = 144
    gap_between_frames: int = 72  # vertical gap between stacked frames
    frame_padding: int = 36  # padding inside each frame around the screenshot


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
    frame_radius: int = 54
    shadow_blur: int = 48
    shadow_opacity: int = 80
    shadow_offset_y: int = 12

    # Logo
    logo_target_h: int = 216


@dataclass(frozen=True)
class TypographySpec:
    badge_font_size: int = 114
    title_font_size: int = 90
    page_font_size: int = 66
    label_font_size: int = 84
    label_gap: int = 84  # space between label text and the frame below it

    badge_pad_x: int = 66
    badge_pad_y: int = 36
    badge_radius: int = 72


@dataclass(frozen=True)
class RenderConfig:
    canvas: CanvasSpec = field(default_factory=CanvasSpec)
    spacing: SpacingSpec = field(default_factory=SpacingSpec)
    style: StyleSpec = field(default_factory=StyleSpec)
    typo: TypographySpec = field(default_factory=TypographySpec)
