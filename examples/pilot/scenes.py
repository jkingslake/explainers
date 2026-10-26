"""Pilot / reference video: a 2-minute taste of Schoof (2007) on marine ice sheet instability.

It exists to show the house style and the explainer_kit API in one small, working file.
Copy its patterns (narrate blocks, colour palette, term-by-term equations, simulated
curves, towel beats) when building a real video.

    python tools/render.py examples/pilot           # draft
    python tools/render.py examples/pilot --final   # 1080p
"""

from manim import *

from explainer_kit import *

# One colour per quantity, for the whole video.
PALETTE = {
    "q": YELLOW,  # ice flux across the grounding line (output)
    "h": BLUE,  # ice thickness at the grounding line
    "a": GREEN,  # snowfall / accumulation (input)
    "x_g": TEAL,  # grounding line position
}
T2C = {"q": PALETTE["q"], "h": PALETTE["h"], "a": PALETTE["a"], "x_g": PALETTE["x_g"]}

SEA = 0.9  # sea level (screen y) in the cross-section


# ---------------------------------------------------------------- the model
# Bed depth below sea level along the flowline (nondimensional), with an
# overdeepened "sill" region near x = 1 where the bed gets deeper inland.
def depth(x):
    return 0.05 + 0.75 * x - 0.45 / (1 + np.exp(-(x - 1.0) / 0.08))


K = 10.0  # lumps together rheology, sliding and density constants


def flux(x):
    """Schoof's boundary-layer flux, q = C h^(19/4), with h set by flotation."""
    return K * depth(x) ** 4.75


def settle(x0, t_end=6.0, steps=600):
    """Grounding line migration: advances when input a*x exceeds output q."""
    xs, x, dt = [x0], x0, t_end / steps
    for _ in range(steps):
        x += dt * (x - flux(x))
        xs.append(x)
    return np.array(xs)


# ---------------------------------------------------------------- cross-section
def bed_y(x):
    """Screen-space bed elevation for the cold open: deeper towards the left (inland)."""
    return SEA - (1.9 + 0.16 * (2.5 - x))


def ice_shape(xg):
    """Grounded ice + floating shelf for grounding line at screen x = xg."""
    hg = (SEA - bed_y(xg)) * 1.12  # flotation thickness at the grounding line
    s_g = bed_y(xg) + hg
    xs = np.linspace(-7.6, xg, 60)
    top = [[x, s_g + 0.42 * np.sqrt(max(xg - x, 0)), 0] for x in xs]
    base = [[x, bed_y(x), 0] for x in xs[::-1]]
    grounded = Polygon(*top, *base).set_fill("#DDEBF5", 1).set_stroke("#9FB8CC", 2)
    L = 2.2
    shelf_top = [[xg + L * t, SEA + 0.11 * hg * (1 - 0.6 * t), 0] for t in np.linspace(0, 1, 12)]
    shelf_bot = [[xg + L * t, SEA - 0.89 * hg * (1 - 0.6 * t), 0] for t in np.linspace(1, 0, 12)]
    shelf = Polygon(*shelf_top, *shelf_bot).set_fill("#DDEBF5", 1).set_stroke("#9FB8CC", 2)
    return VGroup(grounded, shelf), hg


class ColdOpen(ExplainerScene):
    """The puzzle"""

    def construct(self):
        xs = np.linspace(-7.6, 7.6, 80)
        rock = Polygon(*[[x, bed_y(x), 0] for x in xs], [7.6, -4.2, 0], [-7.6, -4.2, 0])
        rock.set_fill(GREY_BROWN, 1).set_stroke(GREY_BROWN, 3)
        ocean = Polygon([-7.6, SEA, 0], [7.6, SEA, 0], *[[x, bed_y(x), 0] for x in xs[::-1]])
        ocean.set_fill(BLUE_E, 0.75).set_stroke(width=0)
        sea_line = DashedLine([-7.6, SEA, 0], [7.6, SEA, 0], dash_length=0.15).set_stroke(BLUE, 2)
        sea_label = words("sea level", 24, color=BLUE).next_to(sea_line, UP, buff=0.1).to_edge(RIGHT)

        xg = ValueTracker(2.5)
        ice = always_redraw(lambda: ice_shape(xg.get_value())[0])
        gl_dot = always_redraw(lambda: Dot([xg.get_value(), bed_y(xg.get_value()), 0], color=PALETTE["x_g"], radius=0.09))

        with self.narrate(
            "This is a slice through a marine ice sheet, like the one in West Antarctica. "
            "The ice rests on bedrock that lies far below sea level."
        ) as n:
            self.play(FadeIn(rock), FadeIn(ocean), Create(sea_line), FadeIn(sea_label), run_time=n.frac(0.4))
            self.play(FadeIn(ice, shift=0.3 * DOWN), run_time=n.frac(0.3))

        gl_label = words("grounding line", 28, color=PALETTE["x_g"])
        gl_label.next_to(gl_dot, DOWN, buff=0.35).shift(0.6 * RIGHT)
        with self.narrate(
            "Where the ice gets thin enough to float, it lifts off the bed. "
            "That spot is the grounding line, and this whole story is about where it can sit."
        ) as n:
            self.wait(n.frac(0.35))
            self.play(FadeIn(gl_dot, scale=2), Write(gl_label))
            self.play(Indicate(gl_dot, scale_factor=1.8))

        slope = Arrow([4.5, bed_y(4.5) - 0.9, 0], [-1.5, bed_y(-1.5) - 0.9, 0], buff=0, color=RED, stroke_width=5)
        slope_label = words("deeper inland", 28, color=RED).next_to(slope, DOWN, buff=0.1)
        towel = Towel(height=1.5).to_corner(UR, buff=0.4)
        with self.narrate("And notice that the bed gets deeper as you go inland.") as n:
            self.play(FadeOut(gl_label), GrowArrow(slope), FadeIn(slope_label), run_time=n.frac(0.6))
        self.play(FadeIn(towel, shift=LEFT))
        with self.narrate("Why would the slope of the bed matter?") as n:
            self.play(*towel.says("Why would the slope matter?", side=LEFT, font_size=28), run_time=n.frac(0.5))
        self.play(*towel.debubble("confused"), FadeOut(slope), FadeOut(slope_label))

        arrow = always_redraw(
            lambda: Arrow(
                ORIGIN,
                RIGHT * min(0.4 + 0.25 * ice_shape(xg.get_value())[1] ** 2.5, 4.5),
                buff=0,
                color=PALETTE["q"],
                stroke_width=8,
                max_tip_length_to_length_ratio=0.2,
            ).next_to([xg.get_value(), SEA + 0.75, 0], RIGHT, buff=0.05)
        )
        q_label = always_redraw(lambda: MathTex("q", color=PALETTE["q"], font_size=48).next_to(arrow, UP, buff=0.1))
        with self.narrate(
            "Watch what happens if the grounding line retreats, just a little. "
            "The ice there is now thicker, so more ice flows out across it. "
            "That thins the ice behind it, which lets the grounding line retreat further still."
        ) as n:
            self.play(FadeIn(arrow), FadeIn(q_label), towel.glance(gl_dot), run_time=n.frac(0.15))
            self.play(xg.animate.set_value(-3.5), towel.change("surprised", look_at=LEFT * 3), run_time=n.frac(0.8), rate_func=rate_functions.ease_in_quad)
        with self.narrate("A runaway retreat, from a tiny nudge.") as n:
            self.play(towel.hop())


def snowfall_sketch():
    """A small ice sheet with snow falling along its whole length, and a brace for x_g."""
    base, left, right = -1.2, -3.2, 3.2
    surface = lambda x: base + 0.25 + 1.7 * np.sqrt(max((right - x) / (right - left), 0))
    xs = np.linspace(left, right, 50)
    sheet = Polygon(*[[x, surface(x), 0] for x in xs], [right, base, 0], [left, base, 0])
    sheet.set_fill("#DDEBF5", 1).set_stroke("#9FB8CC", 2)
    rng = np.random.default_rng(3)
    snow = VGroup()
    for x in rng.uniform(left + 0.1, right - 0.1, 45):
        flake = Dot([x, rng.uniform(2.4, 3.6), 0], radius=0.04, color=WHITE)
        flake.landing = [x, surface(x) + 0.03, 0]
        snow.add(flake)
    brace = BraceBetweenPoints([left, base, 0], [right, base, 0], DOWN, color=PALETTE["x_g"])
    span = VGroup(brace, MathTex("x_g", color=PALETTE["x_g"]).next_to(brace, DOWN, buff=0.1))
    return sheet, snow, span


class Title(ExplainerScene):
    """Title"""

    def construct(self):
        self.title_card(
            "Ice sheet grounding line dynamics: steady states, stability, and hysteresis",
            "Christian Schoof",
            "Journal of Geophysical Research: Earth Surface, 2007",
            narration="This idea was made precise in a 2007 paper by Christian Schoof.",
        )


class FluxLaw(ExplainerScene):
    """Input versus output"""

    def construct(self):
        law = eq("q", r"\approx", "C", r"\,", "h", "^{19/4}", t2c={"q": PALETTE["q"], "h": PALETTE["h"]}, size=72)
        q_part, h_part, power = law[0], law[4], law[5]
        q_lab = words("ice flux out", 28, color=PALETTE["q"]).next_to(law, DOWN, buff=0.9).align_to(q_part, RIGHT).shift(0.3 * LEFT)
        h_lab = words("thickness at the grounding line", 28, color=PALETTE["h"]).next_to(law, DOWN, buff=0.9).align_to(h_part, LEFT)
        q_ptr = Line(q_lab.get_top() + 0.3 * RIGHT, q_part.get_bottom(), buff=0.1, color=PALETTE["q"], stroke_width=2)
        h_ptr = Line(h_lab.get_top() + 0.3 * RIGHT, h_part.get_bottom(), buff=0.1, color=PALETTE["h"], stroke_width=2)

        with self.narrate(
            "Schoof showed that the flux of ice across the grounding line, q, "
            "depends on the ice thickness there, h, raised to a very high power."
        ) as n:
            self.play(Write(law), run_time=n.frac(0.4))
            self.play(FadeIn(q_lab, shift=0.2 * UP), Create(q_ptr), run_time=n.frac(0.15))
            self.play(FadeIn(h_lab, shift=0.2 * UP), Create(h_ptr), run_time=n.frac(0.15))

        with self.narrate("With the standard laws for how ice flows and slides, that power is nineteen over four. Almost five.") as n:
            self.play(Circumscribe(power, color=YELLOW), run_time=n.frac(0.4))

        double = eq(r"2^{19/4}", r"\approx", "27", size=56).next_to(law, UP, buff=0.8)
        with self.narrate("So doubling the thickness multiplies the outflow by about twenty seven.") as n:
            self.play(FadeIn(double, shift=0.2 * DOWN), run_time=n.frac(0.5))
        self.play(FadeOut(VGroup(double, q_lab, h_lab, q_ptr, h_ptr)), law.animate.scale(0.6).to_corner(UL))

        inflow = eq(r"\text{input}", "=", "a", r"\,", "x_g", t2c={"a": PALETTE["a"], "x_g": PALETTE["x_g"]}, size=43)
        inflow.next_to(law, DOWN, buff=0.4, aligned_edge=LEFT)
        sheet, snow, span = snowfall_sketch()
        with self.narrate(
            "Meanwhile, snow falls on the ice upstream. The total input grows with the distance, x g, "
            "from the ice divide to the grounding line."
        ) as n:
            self.play(FadeIn(sheet), run_time=n.frac(0.15))
            self.play(
                LaggedStart(*[f.animate(rate_func=rate_functions.ease_in_quad).move_to(f.landing) for f in snow], lag_ratio=0.03),
                run_time=n.frac(0.45),
            )
            self.play(FadeIn(span), Write(inflow), run_time=n.frac(0.3))
        self.play(FadeOut(VGroup(sheet, snow, span)))

        # --- input vs output, from the model above
        ax = Axes(
            x_range=[0, 1.6, 0.4], y_range=[0, 2.4, 0.6], x_length=8, y_length=4.2,
            axis_config={"color": MUTED, "include_ticks": False}, tips=False,
        ).to_edge(RIGHT, buff=0.7).shift(0.6 * UP)
        x_lab = MathTex("x_g", color=PALETTE["x_g"]).next_to(ax.x_axis, RIGHT, buff=0.15)
        bed_ax = Axes(x_range=[0, 1.6, 0.4], y_range=[-0.9, 0, 1], x_length=8, y_length=1.5, axis_config={"color": MUTED, "include_ticks": False}, tips=False)
        bed_ax.next_to(ax, DOWN, buff=0.3)
        bed_curve = bed_ax.plot(lambda x: -depth(x), x_range=[0.02, 1.6], color=GREY_BROWN, stroke_width=5)
        retro = bed_ax.plot(lambda x: -depth(x), x_range=[0.867, 1.133], color=RED, stroke_width=7)
        bed_lab = words("bed", 24, color=GREY_BROWN).next_to(bed_ax, LEFT, buff=0.15)
        retro_lab = words("deepens inland", 24, color=RED).next_to(bed_ax.c2p(1.0, -0.62), DOWN, buff=0.15)

        input_line = ax.plot(lambda x: x, x_range=[0, 1.6], color=PALETTE["a"], stroke_width=5)
        x_max = 1.555  # where the output curve leaves the top of the axes
        output_curve = ax.plot(flux, x_range=[0.02, x_max], color=PALETTE["q"], stroke_width=5)
        in_lab = words("input", 26, color=PALETTE["a"]).next_to(ax.c2p(1.6, 1.6), DOWN, buff=0.2)
        out_lab = words("output", 26, color=PALETTE["q"]).next_to(ax.c2p(x_max, 2.4), LEFT, buff=0.15)

        with self.narrate("Plot both against grounding line position, with the shape of the bed underneath.") as n:
            self.play(Create(ax), FadeIn(x_lab), Create(bed_ax), Create(bed_curve), FadeIn(bed_lab), run_time=n.frac(0.4))
            self.play(Create(input_line), FadeIn(in_lab), run_time=n.frac(0.25))
            self.play(Create(output_curve), FadeIn(out_lab), run_time=n.frac(0.35))

        steady = [0.715, 0.944, 1.413]
        dots = VGroup(*[Dot(ax.c2p(x, x), radius=0.09, color=WHITE) for x in steady])
        with self.narrate("Wherever the two curves cross, input balances output, and the grounding line could sit still.") as n:
            self.play(LaggedStart(*[FadeIn(d, scale=2) for d in dots], lag_ratio=0.4), run_time=n.frac(0.6))

        towel = Towel(height=1.3).to_corner(DL, buff=0.4)
        with self.narrate(
            "But look at the middle one. It sits where the bed deepens inland."
        ) as n:
            self.play(Create(retro), FadeIn(retro_lab), Indicate(dots[1], color=RED, scale_factor=1.6), FadeIn(towel, shift=UP), run_time=n.frac(0.6))

        traj = settle(0.935)
        t = ValueTracker(0)
        def probe_now():
            x = traj[min(int(t.get_value() * (len(traj) - 1)), len(traj) - 1)]
            gap = Line(ax.c2p(x, x), ax.c2p(x, min(flux(x), 2.4)), color=RED, stroke_width=6)
            return VGroup(gap, Dot(ax.c2p(x, 0), color=PALETTE["x_g"], radius=0.1))

        probe = always_redraw(probe_now)
        with self.narrate(
            "Nudge the grounding line back a little. Now the output is bigger than the input, "
            "so the ice thins and keeps retreating, all the way to the next crossing."
        ) as n:
            self.play(FadeIn(probe), towel.change("thinking", look_at=dots[1]), run_time=n.frac(0.2))
            self.play(t.animate.set_value(1), towel.change("surprised", look_at=dots[0]), run_time=n.frac(0.6), rate_func=linear)

        with self.narrate(
            "Steady states can exist where the bed deepens inland, but they are never stable, at least without "
            "an ice shelf holding the ice back. That is the marine ice sheet instability."
        ) as n:
            self.play(*towel.says("So the bed decides where it can stop!", mode="happy", side=UP, font_size=26, wrap=18), run_time=n.frac(0.4))


class End(ExplainerScene):
    """Credits"""

    def construct(self):
        self.end_card(
            "Schoof, C. (2007). Ice sheet grounding line dynamics:\n"
            "Steady states, stability, and hysteresis. J. Geophys. Res., 112, F03S28.",
            "doi.org/10.1029/2006JF000664",
        )


SCENES = [ColdOpen, Title, FluxLaw, End]
