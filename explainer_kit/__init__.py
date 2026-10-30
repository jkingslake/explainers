"""Shared building blocks for every explainer video.

In a video's scenes.py:

    from manim import *
    from explainer_kit import *
"""

from .config import channel_name, settings
from .scene import ExplainerScene, Narration
from .style import (
    BACKGROUND,
    FRAME_MARGIN,
    MUTED,
    QUANTITY_COLORS,
    SERIF,
    TEXT_COLOR,
    caption,
    eq,
    fits_frame,
    heading,
    stack,
    words,
)
from .towel import MODES as TOWEL_MODES
from .towel import Bubble, Towel
from .tts import speak
