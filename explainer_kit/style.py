"""House style: palette, typography and small layout helpers.

Colours are the classic 3Blue1Brown set (Manim ships them under the same names).
Give every quantity in a video ONE colour and keep it for the whole video;
declare that mapping once per video as a dict and pass it as `t2c`.
"""

from __future__ import annotations

from manim import (
    BLUE,
    DOWN,
    GOLD,
    GREEN,
    GREY_A,
    GREY_B,
    MAROON,
    ORANGE,
    PINK,
    PURPLE,
    RED,
    TEAL,
    WHITE,
    YELLOW,
    MathTex,
    Text,
    VGroup,
    config,
)

BACKGROUND = "#0F1013"
TEXT_COLOR = GREY_A
MUTED = GREY_B

# Ordered so that the first few are maximally distinct. Use these for quantities.
QUANTITY_COLORS = [BLUE, YELLOW, GREEN, RED, TEAL, GOLD, PURPLE, MAROON, PINK, ORANGE]

SERIF = "CMU Serif"  # Computer Modern, so Text() matches MathTex (fonts-cmu)

FRAME_MARGIN = 0.5  # keep everything at least this far from the frame edge


def words(s: str, size: float = 36, color=TEXT_COLOR, **kw) -> Text:
    """Body text in the house serif."""
    return Text(s, font=SERIF, font_size=size, color=color, **kw)


def heading(s: str, size: float = 54, color=WHITE, **kw) -> Text:
    return Text(s, font=SERIF, font_size=size, color=color, **kw)


def eq(*tex: str, t2c: dict | None = None, size: float = 48, **kw) -> MathTex:
    """MathTex with a colour map. Split terms you will animate into separate strings
    (or use {{ }}) so TransformMatchingTex and indexing work."""
    return MathTex(*tex, tex_to_color_map=t2c or {}, font_size=size, color=TEXT_COLOR, **kw)


def caption(s: str, size: float = 24) -> Text:
    """Small grey source line, e.g. 'Adapted from Fig. 3 of Smith et al. (2021)'.
    Place with .to_corner(DR) or .to_edge(DOWN)."""
    return Text(s, font=SERIF, font_size=size, color=MUTED, slant="ITALIC")


def fits_frame(mob, margin: float = FRAME_MARGIN) -> bool:
    """True if `mob` lies fully inside the frame with `margin` to spare."""
    w = config.frame_width / 2 - margin
    h = config.frame_height / 2 - margin
    return (
        mob.get_left()[0] >= -w
        and mob.get_right()[0] <= w
        and mob.get_bottom()[1] >= -h
        and mob.get_top()[1] <= h
    )


def stack(*mobs, buff: float = 0.4, direction=DOWN) -> VGroup:
    return VGroup(*mobs).arrange(direction, buff=buff)
