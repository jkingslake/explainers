# Modelling channelized surface drainage of supraglacial lakes: explained

Kingslake, J., Ng, F. and Sole, A. (2015). *Modelling channelized surface drainage of supraglacial lakes.*
Journal of Glaciology, 61(225), 185–199. https://doi.org/10.3189/2015JoG14J158

Video: [`out/kingslake-2015-modelling-channelized-surface.mp4`](out/kingslake-2015-modelling-channelized-surface.mp4)
(RUNTIME, 1080p30) · subtitles: `out/kingslake-2015-modelling-channelized-surface.srt`

The video follows the paper's own framing and order: the observations that motivate it, the model
(Section 3), the drainage stability analysis built on the stability parameter Λ (Section 4), the numerical
simulations (Section 5) and the discussion (Section 6).

## YouTube description

Why do some lakes on the Greenland and Antarctic ice sheets drain away completely across the ice surface,
while others trickle out and stop? In this explainer we walk through our 2015 Journal of Glaciology paper,
which models a lake draining through a channel that the flowing water melts into the ice. Drainage is a
competition between drawdown of the lake surface and incision of the channel, and the sign of a single
drainage stability parameter, Λ, decides whether it is stable or unstable. Larger lakes and steeper channels
drain unstably and empty; wider channels stabilise drainage; the channel's roughness and the height of the
snow dam don't affect stability. Lakes whose area shrinks as they drain stabilise, and lakes that keep
receiving meltwater always empty completely.

Paper: https://doi.org/10.3189/2015JoG14J158

CHAPTERS

Tags: glaciology, supraglacial lakes, ice sheets, Greenland, Antarctica, meltwater, lake drainage, Journal of Glaciology

## Files

* `analysis.md`: the full model, derivations (checked in `checks.py`), reproduction notes and typos found
* `script.md`: narration and visual plan, scene by scene
* `model.py`: the model, the paper's four simulations and the Fig 10a parameter sweep
* `scenes.py`: the Manim scenes; `assets/`: figures cropped from the paper

## Simplifications made in the video

* The analytical sections show the vertically walled lake with no input first, as the paper does; the shape
  (p_L) and input (Q_in) cases are summarised rather than derived step by step.
* Fig 4 (Bernoulli and force-balance curves) is redrawn for ζ = 1 m with illustrative slope and roughness
  values for the two force-balance curves (the paper doesn't give them).
* Fig 5 is plotted as Q/Q₀ with ζ₀ = 1 m, which reproduces the paper's curves (see analysis.md).
* Fig 7 uses A_Li = 4.6 km², φ_b = 0.03 (not stated in the paper), chosen so that, as in the caption,
  the three highest p_L values halt.
* Fig 10 is shown for the (A_Li, φ_b) panel only (final lake depth); the time-to-empty panels and the ζ₀
  panels are summarised in narration.
* Simulations use RK45 rather than forward Euler, and ρ_i = 900 kg m⁻³ (not stated; reproduces every
  quoted value).
* The discussion's limitations are listed briefly; the multi-channel competition argument and the
  advected-lake speculation for Nivlisen are not covered.
* Cross-section drawings exaggerate vertical scale and channel slope.
