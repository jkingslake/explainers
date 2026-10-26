"""The channel mascot: a little hanging towel with a face.

It plays the role of 3Blue1Brown's pi creatures, standing in for the viewer:
it asks the naive question, looks at what matters, and reacts to the aha moment.

    towel = Towel().to_corner(DL)
    self.play(FadeIn(towel))
    self.play(towel.change("confused", look_at=equation))
    self.play(*towel.says("Wait, why is that term negative?"))
    self.play(towel.blink())
    self.play(*towel.debubble())

Modes: plain, happy, speaking, surprised, confused, thinking, sad, skeptical, smug.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Animation,
    Arc,
    Circle,
    Ellipse,
    FadeIn,
    FadeOut,
    Line,
    ManimColor,
    Mobject,
    Paragraph,
    Polygon,
    Rectangle,
    Rotate,
    RoundedRectangle,
    Transform,
    VGroup,
    VMobject,
    Write,
    config,
    interpolate_color,
    there_and_back,
    wiggle,
)

from .config import settings
from .style import SERIF

BLACK_INK = "#15171C"

# mouth: (width, depth of upper lip, depth of lower lip, tilt in radians)
# pupils: direction the eyes look when no look_at target is given
# eye_squash: vertical scale of (left, right) eye
MODES: dict[str, dict] = {
    "plain": dict(mouth=(0.30, 0.015, 0.055, 0.0), pupils=(0, 0), eye_squash=(1.0, 1.0)),
    "happy": dict(mouth=(0.40, 0.04, 0.20, 0.0), pupils=(0, 0), eye_squash=(0.85, 0.85)),
    "speaking": dict(mouth=(0.30, 0.0, 0.15, 0.0), pupils=(0, 0), eye_squash=(1.0, 1.0)),
    "surprised": dict(mouth=(0.15, -0.09, 0.11, 0.0), pupils=(0, 0), eye_squash=(1.15, 1.15)),
    "confused": dict(mouth=(0.26, 0.0, 0.03, 0.25), pupils=(-0.6, 0.8), eye_squash=(1.0, 0.8)),
    "thinking": dict(mouth=(0.20, 0.0, 0.02, -0.1), pupils=(0.7, 0.7), eye_squash=(0.9, 0.9)),
    "sad": dict(mouth=(0.30, -0.06, -0.025, 0.0), pupils=(0, -0.8), eye_squash=(0.9, 0.9)),
    "skeptical": dict(mouth=(0.26, -0.01, 0.02, 0.15), pupils=(0.3, 0), eye_squash=(0.55, 1.0)),
    "smug": dict(mouth=(0.32, 0.02, 0.08, 0.2), pupils=(0.5, 0), eye_squash=(0.65, 0.65)),
}


def _mouth_path(width: float, top: float, bottom: float, tilt: float) -> VMobject:
    """Closed lip shape between the corners (+-width/2, 0). `top`/`bottom` are how far
    below the corners each lip's midpoint sits (negative = above). top < bottom means
    the mouth is open; both positive = smile, both negative = frown."""
    # For a cubic with both handles at height k, the midpoint is at 0.75 k.
    l, r = np.array([-width / 2, 0, 0]), np.array([width / 2, 0, 0])
    kt, kb = -top / 0.75, -bottom / 0.75
    if abs(top - bottom) < 0.012:  # keep a visible line for closed mouths
        kb -= 0.016 / 0.75
    path = VMobject()
    path.start_new_path(l)
    path.add_cubic_bezier_curve_to(l + [width / 4, kt, 0], r + [-width / 4, kt, 0], r)
    path.add_cubic_bezier_curve_to(r + [-width / 4, kb, 0], l + [width / 4, kb, 0], l)
    path.close_path()
    path.rotate(tilt, about_point=ORIGIN)
    path.set_fill(BLACK_INK, 1).set_stroke(BLACK_INK, 2)
    return path


class Towel(VGroup):
    """A hanging towel with eyes and a mouth. Height ~2 units by default."""

    BODY_W, BODY_H = 1.35, 1.9

    def __init__(
        self,
        mode: str = "plain",
        color: str | None = None,
        stripe_color: str | None = None,
        height: float = 2.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        cfg = settings().get("mascot", {})
        self.towel_color = color or cfg.get("color", "#5CD0B3")
        self.stripe_color = stripe_color or cfg.get("stripe_color", "#F7F2E8")
        self.mode = mode
        self.bubble: VGroup | None = None

        w, h = self.BODY_W, self.BODY_H
        edge = interpolate_color(ManimColor(self.towel_color), ManimColor("#000000"), 0.35)

        self.loop = Arc(radius=0.13, start_angle=0, angle=np.pi, stroke_width=6, color=edge)
        self.loop.move_to([0, h / 2 + 0.06, 0])

        self.body = RoundedRectangle(width=w, height=h, corner_radius=0.16)
        self.body.set_fill(self.towel_color, 1).set_stroke(edge, 4)

        hem_top = Rectangle(width=w - 0.04, height=0.07).move_to([0, h / 2 - 0.16, 0])
        band1 = Rectangle(width=w - 0.04, height=0.09).move_to([0, -h / 2 + 0.42, 0])
        band2 = Rectangle(width=w - 0.04, height=0.05).move_to([0, -h / 2 + 0.27, 0])
        self.stripes = VGroup(hem_top, band1, band2)
        self.stripes.set_fill(self.stripe_color, 0.85).set_stroke(width=0)

        # soft vertical folds so it reads as fabric rather than a box
        self.folds = VGroup(
            Rectangle(width=0.22, height=h - 0.1).move_to([0.38, 0, 0]),
            Rectangle(width=0.12, height=h - 0.1).move_to([-0.47, 0, 0]),
        ).set_fill(edge, 0.22).set_stroke(width=0)

        xs = np.linspace(-w / 2 + 0.12, w / 2 - 0.12, 9)
        self.fringe = VGroup(
            *[Line([x, -h / 2, 0], [x + 0.01, -h / 2 - 0.13, 0]) for x in xs]
        ).set_stroke(self.stripe_color, 3)

        self.eyes = VGroup(self._eye(), self._eye())
        self.eyes[0].move_to([-0.24, 0.30, 0])
        self.eyes[1].move_to([0.24, 0.30, 0])
        self.mouth = _mouth_path(*MODES["plain"]["mouth"]).shift([0, -0.02, 0])

        self.add(self.loop, self.fringe, self.body, self.folds, self.stripes, self.eyes, self.mouth)
        self._apply_mode(mode)
        self.set_height(height)

    # ------------------------------------------------------------------ parts
    @staticmethod
    def _eye() -> VGroup:
        white = Ellipse(width=0.30, height=0.36).set_fill("#FFFFFF", 1).set_stroke(BLACK_INK, 2)
        pupil = Circle(radius=0.095).set_fill(BLACK_INK, 1).set_stroke(width=0)
        glint = Circle(radius=0.03).set_fill("#FFFFFF", 1).set_stroke(width=0)
        glint.move_to(pupil.get_center() + np.array([0.035, 0.035, 0]))
        return VGroup(white, pupil, glint)

    @property
    def scale_factor(self) -> float:
        return self.body.width / self.BODY_W

    def _mouth_anchor(self) -> np.ndarray:
        return self.body.get_center() + np.array([0, -0.02, 0]) * self.scale_factor

    # ------------------------------------------------------------------ state
    def _apply_mode(self, mode: str, look_at=None) -> "Towel":
        if mode not in MODES:
            raise ValueError(f"unknown towel mode {mode!r}; choose from {sorted(MODES)}")
        spec = MODES[mode]
        s = self.scale_factor
        # corners of the mouth stay put, so expressions change in place
        new_mouth = _mouth_path(*spec["mouth"]).scale(s, about_point=ORIGIN).shift(self._mouth_anchor())
        self.mouth.become(new_mouth)

        for eye, squash, x in zip(self.eyes, spec["eye_squash"], (-0.24, 0.24)):
            white = eye[0]
            centre = self.body.get_center() + np.array([x, 0.30, 0]) * s
            white.become(Ellipse(width=0.30 * s, height=0.36 * s * squash))
            white.set_fill("#FFFFFF", 1).set_stroke(BLACK_INK, 2).move_to(centre)

        if look_at is not None:
            self.look_at(look_at)
        else:
            self.look(np.array([*spec["pupils"], 0.0]))
        self.mode = mode
        return self

    def look(self, direction) -> "Towel":
        """Point the pupils in `direction` (a vector; its length 0..1 = how far)."""
        d = np.array(direction, dtype=float)
        n = np.linalg.norm(d)
        if n > 1:
            d = d / n
        for eye in self.eyes:
            white, pupil, glint = eye
            reach_x = max(white.width / 2 - pupil.width / 2 - 0.01 * self.scale_factor, 0)
            reach_y = max(white.height / 2 - pupil.height / 2 - 0.01 * self.scale_factor, 0)
            target = white.get_center() + np.array([d[0] * reach_x, d[1] * reach_y, 0])
            offset = target - pupil.get_center()
            pupil.shift(offset)
            glint.shift(offset)
        return self

    def look_at(self, target) -> "Towel":
        point = target.get_center() if isinstance(target, Mobject) else np.array(target, dtype=float)
        d = point - self.eyes.get_center()
        n = np.linalg.norm(d)
        return self.look(d / n if n > 1e-6 else ORIGIN)

    # ------------------------------------------------------------ animations
    def change(self, mode: str, look_at=None, **anim_kwargs) -> Animation:
        """Animate to a new expression (and optionally look at a point/mobject)."""
        target = self.copy()
        target._apply_mode(mode, look_at=look_at)
        self.mode = mode
        return Transform(self, target, **anim_kwargs)

    def glance(self, target, **anim_kwargs) -> Animation:
        """Keep the expression, just look at something."""
        return self.change(self.mode, look_at=target, **anim_kwargs)

    def blink(self, run_time: float = 0.3) -> Animation:
        return self.eyes.animate(rate_func=there_and_back, run_time=run_time).stretch(0.08, 1)

    def hop(self, height: float = 0.3, run_time: float = 0.5) -> Animation:
        return self.animate(rate_func=there_and_back, run_time=run_time).shift(height * UP)

    def sway(self, angle: float = 0.12, run_time: float = 1.2) -> Animation:
        """A little wiggle on its hook, e.g. for excitement or laughter."""
        return Rotate(self, angle, about_point=self.loop.get_top(), rate_func=wiggle, run_time=run_time)

    def says(self, content, mode: str = "speaking", side=RIGHT, **bubble_kw) -> list[Animation]:
        """Speech bubble. `content` is a str (rendered as text) or any Mobject.
        side: RIGHT, LEFT or UP. Bubble options: font_size, wrap (chars/line), max_width.
        Returns a list of animations: use self.play(*towel.says(...))."""
        return self._bubble(content, mode, side, thought=False, **bubble_kw)

    def thinks(self, content, mode: str = "thinking", side=RIGHT, **bubble_kw) -> list[Animation]:
        return self._bubble(content, mode, side, thought=True, **bubble_kw)

    def debubble(self, mode: str = "plain") -> list[Animation]:
        anims = [self.change(mode)]
        if self.bubble is not None:
            anims.append(FadeOut(self.bubble))
            self.bubble = None
        return anims

    def _bubble(self, content, mode, side, thought, **bubble_kw) -> list[Animation]:
        anims: list[Animation] = []
        if self.bubble is not None:
            anims.append(FadeOut(self.bubble))
        self.bubble = Bubble(content, thought=thought, **bubble_kw)
        self.bubble.pin_to(self, side)
        anims.append(self.change(mode, look_at=self.bubble.box))
        anims.append(FadeIn(self.bubble.box_and_tail))
        anims.append(Write(self.bubble.content))
        return anims


class Bubble(VGroup):
    """Speech (or thought) bubble with its tail pointing at a Towel."""

    def __init__(self, content, thought: bool = False, font_size: float = 32, max_width: float = 4.5, wrap: int = 28, **kwargs):
        super().__init__(**kwargs)
        if isinstance(content, str):
            content = Paragraph(*_wrap(content, wrap), font=SERIF, font_size=font_size, color=BLACK_INK, alignment="center", line_spacing=0.6)
        if content.width > max_width:
            content.scale_to_fit_width(max_width)
        self.content = content
        self.thought = thought
        self.box = RoundedRectangle(
            width=content.width + 0.6, height=content.height + 0.5, corner_radius=0.3 if not thought else 0.5
        ).set_fill("#FFFFFF", 1).set_stroke("#DDDDDD", 2)
        self.box.move_to(content)
        self.tail = VGroup()
        self.box_and_tail = VGroup(self.tail, self.box)
        self.add(self.box_and_tail, self.content)

    def pin_to(self, towel: Towel, side=RIGHT) -> "Bubble":
        """side=RIGHT/LEFT puts the bubble up and to that side; side=UP straight above."""
        sx = 0 if side[0] == 0 else (1 if side[0] > 0 else -1)
        mouth = towel.mouth.get_center()
        lift = 0.5 if sx == 0 else 0.1
        self.move_to(towel.get_top() + np.array([sx * (self.width / 2 + 0.2), self.height / 2 + lift, 0]))
        # nudge back on screen
        half_w, half_h = config.frame_width / 2 - 0.3, config.frame_height / 2 - 0.3
        dx = min(0, half_w - self.get_right()[0]) + max(0, -half_w - self.get_left()[0])
        dy = min(0, half_h - self.get_top()[1])
        self.shift([dx, dy, 0])

        if sx == 0:
            base = self.box.get_bottom() + np.array([0.3, 0.02, 0])
            tip = towel.get_top() + np.array([0.15, 0.05, 0])
            sx = 1
        else:
            corner = self.box.get_corner(DOWN + (LEFT if sx > 0 else RIGHT))
            base = corner + np.array([sx * 0.45, 0.02, 0])
            tip = mouth + np.array([sx * 0.25, 0.15, 0]) * towel.scale_factor
        if self.thought:
            dots = VGroup(
                *[
                    Circle(radius=r).set_fill("#FFFFFF", 1).set_stroke("#DDDDDD", 2).move_to(base + a * (tip - base))
                    for a, r in ((0.3, 0.12), (0.62, 0.08), (0.88, 0.05))
                ]
            )
            self.tail.become(dots)
        else:
            tri = Polygon(base + [-0.18, 0, 0], base + [0.18, 0, 0], tip)
            tri.set_fill("#FFFFFF", 1).set_stroke("#DDDDDD", 2)
            self.tail.become(tri)
        return self


def _wrap(text: str, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines
