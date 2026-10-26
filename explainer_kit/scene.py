"""ExplainerScene: a manim Scene with synced narration, subtitles and branded cards.

    class Intro(ExplainerScene):
        def construct(self):
            with self.narrate("Here is the question the whole paper turns on.") as n:
                self.play(Write(question), run_time=n.duration * 0.6)
            # the block waits until the sentence has finished before moving on
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from manim import (
    DL,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    LaggedStart,
    Line,
    Scene,
    VGroup,
    Write,
    config,
)

from .config import channel_name
from .style import BACKGROUND, MUTED, TEXT_COLOR, caption, heading, words
from .towel import Towel
from .tts import speak


class Narration:
    """Handle returned by ExplainerScene.narrate; use it to time animations."""

    def __init__(self, scene: Scene, text: str, duration: float, start: float):
        self.scene, self.text, self.duration, self.start = scene, text, duration, start

    @property
    def elapsed(self) -> float:
        return self.scene.renderer.time - self.start

    @property
    def remaining(self) -> float:
        return max(self.duration - self.elapsed, 0.0)

    def frac(self, f: float, minimum: float = 0.3) -> float:
        """A run_time that is fraction `f` of the whole sentence."""
        return max(f * self.duration, minimum)


class ExplainerScene(Scene):
    def setup(self):
        self.camera.background_color = BACKGROUND
        self.cues: list[dict] = []

    # ------------------------------------------------------------ narration
    @contextmanager
    def narrate(self, text: str, pad: float = 0.35):
        """Speak `text` while the body of the `with` block plays. On exit, waits for the
        voice to finish (plus `pad` seconds), blinking any towel on screen meanwhile."""
        text = " ".join(text.split())
        clip = speak(text)
        start = self.renderer.time
        if clip.path is not None:
            self.add_sound(str(clip.path))
        n = Narration(self, text, clip.duration, start)
        yield n
        self.cues.append({"start": start, "end": start + clip.duration, "text": text})
        self.idle(clip.duration + pad - n.elapsed)

    def say(self, text: str, *animations, fill: float = 0.7, pad: float = 0.35):
        """Shorthand: play `animations` over the first `fill` fraction of the sentence."""
        with self.narrate(text, pad=pad) as n:
            if animations:
                self.play(*animations, run_time=n.frac(fill))

    def idle(self, seconds: float):
        """wait(), but any Towel on screen blinks during longer pauses."""
        if seconds <= 0.02:
            return
        towels = [m for m in self.mobjects if isinstance(m, Towel)]
        if towels and seconds > 1.8:
            self.wait(seconds * 0.45)
            self.play(*[t.blink() for t in towels], run_time=0.3)
            self.wait(max(seconds * 0.55 - 0.3, 0.01))
        else:
            self.wait(seconds)

    def tear_down(self):
        writer = getattr(self.renderer, "file_writer", None)
        movie = getattr(writer, "movie_file_path", None)
        if movie and self.cues:
            Path(movie).with_suffix(".cues.json").write_text(json.dumps(self.cues, indent=1))

    # ------------------------------------------------------------ branded cards
    def title_card(self, title: str, authors: str, venue: str = "", narration: str | None = None):
        """Paper title, authors and the channel byline, with the towel saying hello."""
        t = heading(title, size=50)
        if t.width > config.frame_width - 1.5:
            t = VGroup(*[heading(line, size=50) for line in _split_title(title)]).arrange(DOWN, buff=0.2)
        a = words(authors, size=30, color=TEXT_COLOR)
        v = words(venue, size=26, color=MUTED) if venue else VGroup()
        rule = Line(2 * LEFT, 2 * RIGHT).set_stroke(MUTED, 1.5)
        by = words(f"An explainer by {channel_name()}", size=30, color=TEXT_COLOR)
        block = VGroup(t, a, v, rule, by).arrange(DOWN, buff=0.35)
        rule.stretch_to_fit_width(max(t.width, 4))
        block.move_to(0.3 * UP)
        towel = Towel(mode="happy", height=1.6).to_corner(DL, buff=0.4)

        with self.narrate(narration or f"{title}. By {authors}.") as n:
            self.play(Write(t), run_time=n.frac(0.4))
            self.play(LaggedStart(FadeIn(a), FadeIn(v), FadeIn(rule), FadeIn(by), lag_ratio=0.3), FadeIn(towel, shift=0.3 * UP))
            self.play(towel.sway())
        self.play(FadeOut(block), FadeOut(towel))

    def end_card(self, citation: str, url: str = "", narration: str | None = None):
        head = heading("The paper", size=40)
        cite = words(citation, size=28)
        if cite.width > config.frame_width - 1.5:
            cite.scale_to_fit_width(config.frame_width - 1.5)
        link = words(url, size=24, color=MUTED) if url else VGroup()
        by = words(f"Explained by {channel_name()}", size=30)
        tools = caption("Animated with Manim. Script and animation drafted with Claude.", size=22)
        block = VGroup(head, cite, link, by, tools).arrange(DOWN, buff=0.4).shift(0.4 * UP)
        towel = Towel(mode="happy", height=1.6).to_corner(DL, buff=0.4)
        with self.narrate(narration or "Thanks for watching. The paper itself is linked below.") as n:
            self.play(LaggedStart(*[FadeIn(m, shift=0.2 * UP) for m in block], lag_ratio=0.2), FadeIn(towel), run_time=n.frac(0.6))
        self.idle(2.0)

    def paper_figure(self, image_path: str | Path, source: str, height: float = 5.5) -> Group:
        """A figure cropped from the paper, with a source line underneath. Prefer
        re-drawing figures from the model itself; use this when the original matters."""
        img = ImageMobject(str(image_path)).set_height(height)
        return Group(img, caption(source).next_to(img, DOWN, buff=0.2))


def _split_title(title: str) -> list[str]:
    ws = title.split()
    best = min(range(1, len(ws)), key=lambda i: abs(len(" ".join(ws[:i])) - len(" ".join(ws[i:]))), default=1)
    return [" ".join(ws[:best]), " ".join(ws[best:])]
