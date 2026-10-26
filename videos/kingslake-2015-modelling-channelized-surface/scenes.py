"""Kingslake, Ng & Sole (2015): Modelling channelized surface drainage of supraglacial lakes.

Follows the paper's framing, order and notation. Narration matches script.md.
Every curve comes from model.py.
"""

import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from manim import *  # noqa: E402

from explainer_kit import *  # noqa: E402
from model import (  # noqa: E402
    DAY,
    FIG7,
    SIM1,
    SIM2,
    SIM3,
    SIM4,
    Lake,
    analytic_Q,
    bernoulli_Q,
    final_depth_map,
    force_balance_Q,
    simulate,
    trajectory,
)

ASSETS = HERE / "assets"
LIGHT_BROWN_ = "#CD853F"

# One colour per quantity for the whole video (analysis.md, section 4).
PALETTE = {
    r"\zeta": YELLOW,
    "h_L": BLUE,
    "h_C": RED,
    "Q": TEAL,
    "A_{Li}": GREEN,
    "A_L": GREEN,
    r"\Lambda": GOLD,
    r"\tilde\Lambda": GOLD,
    r"\Lambda_C": GOLD,
    r"\alpha": PINK,
    r"\beta": ORANGE,
    r"\phi_b": PURPLE,
    "w": MAROON,
    "f_R": LIGHT_BROWN_,
}

ICE = "#C9D6DF"
ICE_DARK = "#7D8F9C"
WATER = "#2C6E9B"
SNOW = "#F4F6F8"


def ceq(*parts, size=44, **kw):
    """MathTex whose parts are coloured when they exactly match a PALETTE key."""
    m = MathTex(*parts, font_size=size, color=TEXT_COLOR, **kw)
    for sub in m:
        if sub.tex_string in PALETTE:
            sub.set_color(PALETTE[sub.tex_string])
    return m


def sym(tex, size=40):
    return ceq(tex, size=size)


# ---------------------------------------------------------------- cross-section
class Geo:
    """Screen geometry of a lake + outlet + channel cross-section (vertical exaggeration)."""

    def __init__(self, center=ORIGIN, k=0.3, W0=2.6, p_L=1.0, h_Li=10.0, rim=1.6, chan_len=4.2,
                 slope=0.14, below=1.2, far=None):
        self.c, self.k, self.W0, self.p, self.h_Li = np.array(center, float), k, W0, p_L, h_Li
        self.rim, self.chan_len, self.slope, self.below = rim, chan_len, slope, below
        self.h_top = h_Li + rim
        self.x_out = self.W(self.h_top)
        self.x_end = self.x_out + chan_len
        self.far = far if far is not None else W0 + 1.2

    def W(self, h):
        if self.p == 1:
            return self.W0
        return self.W0 * (max(h, 0.0) / self.h_Li) ** ((self.p - 1) / 2)

    def pt(self, x, h):
        return self.c + np.array([x, self.k * h, 0.0])

    def chan_floor_h(self, x, h_C):
        """Channel-floor height (m) at screen x >= x_out."""
        return h_C - self.slope * (x - self.x_out) / self.k

    def mobs(self, h_L, h_C, D=0.0, dam=False, show_far_ice=True):
        k, pt = self.k, self.pt
        hs_down = np.linspace(self.h_top, 0, 40)
        hwt = max(h_C, 0.0)
        hs_up = np.linspace(0, hwt, 30)
        h_end = self.chan_floor_h(self.x_end, h_C)
        top_end = self.chan_floor_h(self.x_end, self.h_top)
        bottom = -self.below

        ice_pts = [pt(-self.far, self.h_top)]
        ice_pts += [pt(-self.W(h), h) for h in hs_down]
        ice_pts += [pt(self.W(h), h) for h in hs_up]
        if h_C < 0:
            ice_pts.append(pt(self.W(0), h_C))
        ice_pts += [pt(self.x_out, h_C), pt(self.x_end, h_end), pt(self.x_end, bottom), pt(-self.far, bottom)]
        ice = Polygon(*ice_pts).set_fill(ICE, 1).set_stroke(ICE_DARK, 2)

        far_pts = [pt(self.W(hwt), h_C)] + [pt(self.W(h), h) for h in np.linspace(hwt, self.h_top, 20)]
        far_pts += [pt(self.x_out, self.h_top), pt(self.x_end, top_end), pt(self.x_end, h_end), pt(self.x_out, h_C)]
        trench = Polygon(*far_pts).set_fill(ICE_DARK, 1).set_stroke(width=0)

        group = VGroup(trench, ice) if show_far_ice else VGroup(ice)
        if h_L > 0.02:
            hL = h_L
            lake_pts = [pt(-self.W(h), h) for h in np.linspace(hL, 0, 30)]
            if hL <= h_C:
                lake_pts += [pt(self.W(h), h) for h in np.linspace(0, hL, 30)]
            else:
                lake_pts += [pt(self.W(h), h) for h in hs_up]
                if h_C < 0:
                    lake_pts.append(pt(self.W(0), h_C))
                d = max(D, 0.0)
                edge = min(self.W(hwt), self.x_out) - 0.45
                lake_pts += [
                    pt(self.x_out, h_C),
                    pt(self.x_end, h_end),
                    pt(self.x_end, h_end + d),
                    pt(self.x_out, h_C + d),
                    pt((self.x_out + edge) / 2, hL - 0.35 * (hL - h_C - d)),
                    pt(edge, hL),
                ]
            water = Polygon(*lake_pts).set_fill(WATER, 0.95).set_stroke(BLUE, 1.5)
            group.add(water)
        if dam:
            dam_m = Rectangle(width=0.28, height=k * (max(h_L - h_C, 0) + 0.5))
            dam_m.set_fill(SNOW, 1).set_stroke(GREY_B, 1.5)
            dam_m.move_to(pt(self.x_out + 0.14, h_C), aligned_edge=DOWN)
            group.add(dam_m)
        return group.set_z_index(-1)


def outlet_depth(lake: Lake, zeta: float) -> float:
    return lake.outlet(zeta)[2]


def img(path, height):
    return ImageMobject(str(path)).set_height(height)


def img_point(im, fx, fy):
    """Point at fraction (fx from left, fy from top) of an ImageMobject."""
    return im.get_corner(UL) + np.array([fx * im.width, -fy * im.height, 0])


def run_tracker(run, s):
    """Interpolate a simulation at progress s in [0, 1]."""
    t = s * run.t[-1]
    return (np.interp(t, run.t, run.h_L), np.interp(t, run.t, run.h_C), np.interp(t, run.t, run.Q), t)


# ================================================================ scenes
class ColdOpen(ExplainerScene):
    """Lakes that drain over the ice"""

    def construct(self):
        c = img(ASSETS / "greenland_fig1c.png", 5.6).shift(0.25 * UP)
        d = img(ASSETS / "greenland_fig1d.png", 5.6).move_to(c)
        date_c = words("30 June 2001", 30).next_to(c, UP, buff=0.2)
        date_d = words("7 July 2001", 30).next_to(c, UP, buff=0.2)
        cap = caption("Landsat 7 images. Fig. 1, Kingslake et al. (2015)").next_to(c, DOWN, buff=0.2)

        with self.narrate(
            "Every summer, meltwater collects in hollows on the surface of the Greenland ice sheet, forming lakes."
        ) as n:
            self.play(FadeIn(c), FadeIn(date_c), FadeIn(cap), run_time=n.frac(0.4))

        B, A, C = img_point(c, 0.58, 0.27), img_point(c, 0.26, 0.57), img_point(c, 0.33, 0.87)
        path = CubicBezier(B + 0.15 * LEFT, B + 1.2 * LEFT + 0.9 * DOWN, A + 1.0 * RIGHT + 0.2 * UP, A + 0.45 * RIGHT)
        flow = path.copy().set_stroke(PALETTE["Q"], 6)
        with self.narrate(
            "These two satellite images were taken a week apart. In that week, lake B drained across the ice "
            "surface into lake A. And lake C drained away completely."
        ) as n:
            self.play(FadeIn(d), ReplacementTransform(date_c, date_d), run_time=n.frac(0.2))
            self.wait(n.frac(0.15))
            self.play(Create(flow), run_time=n.frac(0.3))
            ring = Circle(radius=0.75, color=YELLOW, stroke_width=4).move_to(C + 0.3 * LEFT)
            self.play(Create(ring), run_time=n.frac(0.2))
        self.play(FadeOut(Group(c, d, date_d, cap, flow, ring)))

        niv = img(ASSETS / "nivlisen_fig2a.png", 5.6).shift(0.25 * UP)
        cap2 = caption("MODIS image, 5 January 2008. Fig. 2a, Kingslake et al. (2015)").next_to(niv, DOWN, buff=0.2)
        with self.narrate(
            "In East Antarctica, we found lakes near the grounding line of the ice sheet draining across the "
            "Nivlisen ice shelf, with water travelling up to seventy kilometres, nearly every summer."
        ) as n:
            self.play(FadeIn(niv), FadeIn(cap2), run_time=n.frac(0.25))
            self.play(niv.animate.scale(1.35, about_point=img_point(niv, 0.55, 0.3)), FadeOut(cap2), run_time=n.frac(0.7))
        self.play(FadeOut(niv))

        geo = Geo(center=[-1.2, -2.0, 0], k=0.26, W0=2.3, chan_len=4.0)
        sec = geo.mobs(10, 9, dam=True)
        towel = Towel(height=1.4).to_corner(DL, buff=0.35)
        ax_kw = dict(x_range=[0, 1, 1], y_range=[0, 1, 1], x_length=2.6, y_length=1.5, tips=False,
                     axis_config={"color": MUTED, "include_ticks": False})
        ax1 = Axes(**ax_kw).to_corner(UR, buff=0.6).shift(2.9 * LEFT)
        ax2 = Axes(**ax_kw).to_corner(UR, buff=0.6)
        dec = ax1.plot(lambda t: 0.85 / (1 + 4 * t) ** 3 + 0.05, color=PALETTE["Q"], stroke_width=5)
        inc = ax2.plot(lambda t: 0.12 / (1 - 0.8 * t) ** 3, x_range=[0, 0.92], color=PALETTE["Q"], stroke_width=5)
        lab1 = words("stable", 26).next_to(ax1, DOWN, buff=0.15)
        lab2 = words("unstable", 26).next_to(ax2, DOWN, buff=0.15)
        qlab = VGroup(*[sym("Q", 34).next_to(a, LEFT, buff=0.1).align_to(a, UP) for a in (ax1, ax2)])
        with self.narrate(
            "Lakes can drain down to the bed of an ice sheet, or over its surface, through a channel that the "
            "flowing water melts into the ice. We wanted to understand that surface drainage. When does it fizzle "
            "out, and when does it run away and empty the lake?"
        ) as n:
            self.play(FadeIn(sec), run_time=n.frac(0.2))
            self.wait(n.frac(0.25))
            self.play(Create(ax1), Create(ax2), FadeIn(qlab), run_time=n.frac(0.1))
            self.play(Create(dec), FadeIn(lab1), run_time=n.frac(0.15))
            self.play(Create(inc), FadeIn(lab2), FadeIn(towel, shift=UP), run_time=n.frac(0.15))
            self.play(towel.change("confused", look_at=ax2), run_time=n.frac(0.1))


class Title(ExplainerScene):
    """Title"""

    def construct(self):
        self.title_card(
            "Modelling channelized surface drainage of supraglacial lakes",
            "J. Kingslake, F. Ng and A. Sole",
            "Journal of Glaciology, 2015",
            narration="That's the question of our twenty fifteen paper in the Journal of Glaciology.",
        )


class Geometry(ExplainerScene):
    """The model lake"""

    def construct(self):
        geo = Geo(center=[-1.6, -2.3, 0], k=0.32, W0=2.6, chan_len=4.6)
        h_L, h_C = 10.0, 9.0
        sec = geo.mobs(h_L, h_C, dam=True)
        hl_arrow = DoubleArrow(geo.pt(-1.7, 0), geo.pt(-1.7, h_L), buff=0, color=PALETTE["h_L"], stroke_width=4,
                               tip_length=0.18)
        hl_lab = sym("h_L").next_to(hl_arrow, RIGHT, buff=0.1)
        with self.narrate("Here is our model. A lake of depth h L drains through a channel cut into the ice surface.") as n:
            self.play(FadeIn(sec), run_time=n.frac(0.4))
            self.play(GrowFromCenter(hl_arrow), FadeIn(hl_lab), run_time=n.frac(0.3))

        outlet_dot = Dot(geo.pt(geo.x_out, h_C), color=WHITE, radius=0.07)
        outlet_lab = words("lake outlet", 26).next_to(geo.pt(geo.x_out, geo.h_top), UP, buff=0.6).shift(0.8 * RIGHT)
        outlet_ptr = Line(outlet_lab.get_bottom(), outlet_dot.get_center(), buff=0.08, color=WHITE, stroke_width=2)
        with self.narrate(
            "We ignore the length of the channel, and assume the discharge is controlled at a single point near the "
            "lake, which we call the lake outlet."
        ) as n:
            self.play(FadeIn(outlet_dot, scale=2), FadeIn(outlet_lab), Create(outlet_ptr), run_time=n.frac(0.4))

        hc_arrow = DoubleArrow(geo.pt(geo.x_out - 0.35, 0), geo.pt(geo.x_out - 0.35, h_C), buff=0,
                               color=PALETTE["h_C"], stroke_width=4, tip_length=0.18)
        hc_lab = sym("h_C").next_to(hc_arrow, LEFT, buff=0.1).shift(0.6 * DOWN)
        slope_line = Line(geo.pt(geo.x_out + 1.4, geo.chan_floor_h(geo.x_out + 1.4, h_C)),
                          geo.pt(geo.x_out + 3.2, geo.chan_floor_h(geo.x_out + 3.2, h_C)))
        phi_lab = sym(r"\phi_b").next_to(slope_line, DOWN, buff=0.25)
        dam_lab = words("snow dam", 24).next_to(geo.pt(geo.x_out + 0.14, h_L + 1.2), UP, buff=0.2)

        zeta = 1.0
        D = outlet_depth(SIM1, zeta)
        flowing = geo.mobs(h_L, h_C, D=D)
        q_arrow = Arrow(geo.pt(geo.x_out + 1.2, geo.chan_floor_h(geo.x_out + 1.2, geo.h_top) + 1.3),
                        geo.pt(geo.x_out + 3.4, geo.chan_floor_h(geo.x_out + 3.4, geo.h_top) + 1.3),
                        buff=0, color=PALETTE["Q"], stroke_width=6)
        q_lab = sym("Q").next_to(q_arrow, UP, buff=0.1)
        with self.narrate(
            "The bottom of the channel there sits at a height h C above the lake bed. Drainage begins when a dam of "
            "wet snow in the channel fails, and water starts to flow, with discharge Q."
        ) as n:
            self.play(GrowFromCenter(hc_arrow), FadeIn(hc_lab), FadeIn(phi_lab), FadeOut(outlet_lab), FadeOut(outlet_ptr),
                      run_time=n.frac(0.3))
            self.play(FadeIn(dam_lab), run_time=n.frac(0.1))
            self.wait(n.frac(0.15))
            self.play(FadeOut(dam_lab), FadeOut(sec), FadeIn(flowing), run_time=n.frac(0.15))
            self.play(GrowArrow(q_arrow), FadeIn(q_lab), run_time=n.frac(0.15))

        diagram = VGroup(flowing, hl_arrow, hl_lab, hc_arrow, hc_lab, phi_lab, q_arrow, q_lab, outlet_dot)
        self.play(diagram.animate.scale(0.5).to_corner(UL, buff=0.4))

        shapes = VGroup()
        for p in (1, 2, 3):
            g = Geo(center=ORIGIN, k=0.1, W0=0.8, p_L=p, rim=1.0, chan_len=0.01, slope=0.0, below=0.4, far=1.1)
            m = g.mobs(10, 10.5)
            lab = ceq(r"p_L =", str(p), size=34).next_to(m, DOWN, buff=0.2)
            shapes.add(VGroup(m, lab))
        shapes.arrange(RIGHT, buff=1.0).move_to([1.2, 0.2, 0])
        names = VGroup(*[words(s, 24, color=MUTED).next_to(sh, DOWN, buff=0.1) for s, sh in
                         zip(["vertical walls", "bowl", "cone"], shapes)])
        with self.narrate(
            "The lake's shape is described by a single parameter, p L. A lake with vertical walls has p L equal to "
            "one. Bowl shaped lakes have p L between one and three, and a cone has p L of three."
        ) as n:
            self.play(LaggedStart(*[FadeIn(s, shift=0.2 * UP) for s in shapes], lag_ratio=0.5), run_time=n.frac(0.6))
            self.play(FadeIn(names), run_time=n.frac(0.2))

        eq2 = ceq(r"{d", "h_L", r"\over dt}", "=", r"{1", r"\over", "A_{Li}", "}",
                  r"\left({h_{Li} \over", "h_L", r"}\right)^{p_L-1}", r"\big(", "Q_{in}", "-", "Q", r"\big)", size=48)
        eq2.to_edge(DOWN, buff=0.9)
        br = Brace(eq2[4:11], DOWN, color=MUTED)
        br_lab = words("one over the lake's current area", 24, color=MUTED).next_to(br, DOWN, buff=0.1)
        with self.narrate(
            "Water conservation then tells us how the lake depth changes: d h L by d t equals the input minus the "
            "discharge, divided by the lake's area."
        ) as n:
            self.play(Write(eq2), run_time=n.frac(0.5))
            self.play(Indicate(eq2[12:15]), run_time=n.frac(0.2))
            self.play(GrowFromCenter(br), FadeIn(br_lab), run_time=n.frac(0.2))
        self.idle(0.5)


class Bernoulli(ExplainerScene):
    """From the lake into the channel"""

    def construct(self):
        geo = Geo(center=[-3.4, -2.6, 0], k=0.55, W0=2.4, h_Li=10, rim=1.2, chan_len=3.0, slope=0.18, far=4.5)
        # zoom on the top of the lake: shift so that h ~ 7..11 is visible
        h_L, h_C = 10.0, 9.0
        D = outlet_depth(SIM1, 1.0)
        sec = geo.mobs(h_L, h_C, D=D).shift(2.8 * DOWN)
        p_lake = geo.pt(-0.8, h_L) + 2.8 * DOWN
        p_out = geo.pt(geo.x_out, h_C + D) + 2.8 * DOWN
        stream = CubicBezier(p_lake, p_lake + 1.6 * RIGHT, p_out + 1.0 * LEFT + 0.1 * UP, p_out + 0.5 * RIGHT)
        stream.set_stroke(WHITE, 3).set_opacity(0.9)
        stream_d = DashedVMobject(stream, num_dashes=24)
        lab_lake = MathTex("u = 0", ",", r"\ z =", "h_L", font_size=32).next_to(p_lake, UP, buff=0.25)
        lab_lake[3].set_color(PALETTE["h_L"])
        lab_out = MathTex("u = v", ",", r"\ z =", "h_C", "+ D", font_size=32).next_to(p_out, UP, buff=1.1).shift(0.6 * RIGHT)
        lab_out[3].set_color(PALETTE["h_C"])

        with self.narrate(
            "To find the discharge, we follow the water along a streamline on its surface, from the still body of "
            "the lake out into the channel."
        ) as n:
            self.play(FadeIn(sec), run_time=n.frac(0.3))
            self.play(Create(stream_d), run_time=n.frac(0.4))
            parcel = Dot(p_lake, color=WHITE, radius=0.08)
            self.play(MoveAlongPath(parcel, stream), run_time=n.frac(0.25), rate_func=rate_functions.ease_in_quad)

        eq3 = ceq("z", "+", r"{u^2 \over 2g}", "=", r"\text{constant}", size=46).to_corner(UR, buff=0.7)
        eq4 = ceq("h_L", "=", "(", "h_C", "+", "D", ")", "+", r"{v^2 \over 2g}", size=46).move_to(eq3)
        with self.narrate(
            "Bernoulli's equation says that height plus velocity squared over two g stays the same. So the lake "
            "level equals the height of the water in the channel, plus the velocity head."
        ) as n:
            self.play(Write(eq3), run_time=n.frac(0.3))
            self.play(FadeIn(lab_lake), FadeIn(lab_out), run_time=n.frac(0.2))
            self.play(TransformMatchingTex(eq3, eq4), run_time=n.frac(0.35))

        eq5 = ceq("Q", "=", "v", "w", "D", size=40).next_to(eq4, DOWN, buff=0.4)
        eq6 = ceq("h_L", "-", "h_C", "=", "D", "+", r"{", "Q", r"^2 \over 2 g", "w", r"^2 D^2}", size=46).move_to(eq4)
        self.play(FadeOut(VGroup(sec, stream_d, lab_lake, lab_out)), FadeOut(parcel))

        ax = Axes(x_range=[0, 4.0, 1], y_range=[0, 1.3, 0.5], x_length=6.2, y_length=4.6, tips=False,
                  axis_config={"color": MUTED, "include_ticks": False}).to_corner(DL, buff=0.7).shift(0.4 * RIGHT)
        x_lab = words("discharge", 26).next_to(ax.x_axis, DOWN, buff=0.15)
        q_sym = sym("Q", 34).next_to(x_lab, RIGHT, buff=0.15)
        y_lab = words("depth of flow", 26).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.15)
        Ds = np.linspace(0.001, 0.999, 300)
        curve = VMobject().set_points_smoothly([ax.c2p(bernoulli_Q(D_, 1.0, 2.0), D_) for D_ in Ds])
        curve.set_stroke(WHITE, 5)
        Dc = 2 / 3
        Cpt = Dot(ax.c2p(bernoulli_Q(Dc, 1.0, 2.0), Dc), color=WHITE, radius=0.09)
        C_lab = MathTex("C", font_size=34).next_to(Cpt, RIGHT, buff=0.12)
        sub_lab = words("subcritical", 26, color=MUTED).next_to(ax.c2p(1.0, 1.04), UP, buff=0.05)
        sup_lab = words("supercritical", 26, color=MUTED).move_to(ax.c2p(2.9, 0.14))
        eq7 = ceq(r"D_C", "=", r"\tfrac{2}{3}", "(", "h_L", "-", "h_C", ")", size=40).next_to(eq5, DOWN, buff=0.4)
        with self.narrate(
            "With discharge equal to velocity times width times depth, this gives the classic curve from open "
            "channel hydraulics. It has a subcritical branch and a supercritical branch, which meet at a critical "
            "point where the discharge is greatest."
        ) as n:
            self.play(FadeIn(eq5), run_time=n.frac(0.15))
            self.play(TransformMatchingTex(eq4, eq6), run_time=n.frac(0.2))
            self.play(Create(ax), FadeIn(x_lab), FadeIn(q_sym), FadeIn(y_lab), run_time=n.frac(0.1))
            self.play(Create(curve), run_time=n.frac(0.2))
            self.play(FadeIn(sub_lab), FadeIn(sup_lab), run_time=n.frac(0.1))
            self.play(FadeIn(Cpt, scale=2), FadeIn(C_lab), FadeIn(eq7), run_time=n.frac(0.15))
        self.idle(0.4)


class ForceBalance(ExplainerScene):
    """Friction and gravity"""

    def construct(self):
        # the Bernoulli curve, as at the end of the previous scene
        ax = Axes(x_range=[0, 4.0, 1], y_range=[0, 1.3, 0.5], x_length=6.2, y_length=4.6, tips=False,
                  axis_config={"color": MUTED, "include_ticks": False}).to_corner(DL, buff=0.7).shift(0.4 * RIGHT)
        x_lab = words("discharge", 26).next_to(ax.x_axis, DOWN, buff=0.15)
        q_sym = sym("Q", 34).next_to(x_lab, RIGHT, buff=0.15)
        y_lab = words("depth of flow", 26).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.15)
        Ds = np.linspace(0.001, 0.999, 300)
        curve = VMobject().set_points_smoothly([ax.c2p(bernoulli_Q(D_, 1.0, 2.0), D_) for D_ in Ds]).set_stroke(WHITE, 5)
        Dc = 2 / 3
        Cpt = Dot(ax.c2p(bernoulli_Q(Dc, 1.0, 2.0), Dc), color=WHITE, radius=0.09)
        C_lab = MathTex("C", font_size=34).next_to(Cpt, RIGHT, buff=0.12)
        self.add(ax, x_lab, q_sym, y_lab, curve, Cpt, C_lab)

        # slab of water on the slope
        ang = 0.32
        slab = Rectangle(width=2.2, height=0.7).set_fill(WATER, 0.9).set_stroke(BLUE, 2)
        bed = Line(2.2 * LEFT, 2.2 * RIGHT, color=ICE_DARK, stroke_width=6).next_to(slab, DOWN, buff=0)
        block = VGroup(bed, slab).rotate(-ang).move_to([3.6, 1.6, 0])
        down_dir = np.array([np.cos(-ang), np.sin(-ang), 0])
        grav = Arrow(slab.get_center(), slab.get_center() + 1.5 * down_dir, buff=0, color=PALETTE[r"\phi_b"], stroke_width=6)
        fric = Arrow(slab.get_center() + 0.2 * DOWN, slab.get_center() + 0.2 * DOWN - 1.5 * down_dir, buff=0,
                     color=PALETTE["f_R"], stroke_width=6)
        eq8 = ceq(r"\tau_F", "=", r"\tfrac{1}{8}", "f_R", r"\rho_w v^2", size=38)
        eq9 = ceq(r"\tau_G", "=", r"\rho_w g D", r"\phi_b", size=38)
        eqs = VGroup(eq8, eq9).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(block, DOWN, buff=0.5)
        with self.narrate("Bernoulli alone doesn't fix the flow. We also balance the forces on the water in the channel.") as n:
            self.play(FadeIn(block), run_time=n.frac(0.4))
        with self.narrate(
            "Friction from the ice, set by the hydraulic roughness f R, balances the pull of gravity along the "
            "channel slope, phi b."
        ) as n:
            self.play(GrowArrow(fric), Write(eq8), run_time=n.frac(0.45))
            self.play(GrowArrow(grav), Write(eq9), run_time=n.frac(0.45))

        eq10 = ceq("Q", "=", r"\sqrt{8 g", r"\phi_b", r"\over", "f_R", r"}", r"\, w D^{3/2}", size=42).move_to(eqs)
        fb_dash = DashedVMobject(ax.plot(lambda q: (q / force_balance_Q(1.0, 0.01, 0.25, 2.0)) ** (2 / 3), x_range=[0, 3.95]),
                                 num_dashes=40).set_stroke(PALETTE[r"\phi_b"], 4)
        q_A = _intersect(lambda D_: bernoulli_Q(D_, 1, 2) - force_balance_Q(D_, 0.01, 0.25, 2), 0.67, 0.999)
        with self.narrate(
            "That gives a second relationship between discharge and flow depth. Where it crosses the Bernoulli "
            "curve, both are satisfied."
        ) as n:
            self.play(FadeOut(VGroup(block, grav, fric)), ReplacementTransform(VGroup(eq8, eq9), eq10), run_time=n.frac(0.35))
            self.play(Create(fb_dash), run_time=n.frac(0.4))

        A_dot = Dot(ax.c2p(bernoulli_Q(q_A, 1, 2), q_A), color=PALETTE[r"\phi_b"], radius=0.09)
        A_lab = MathTex("A", font_size=34).next_to(A_dot, UP, buff=0.12)
        phi2, f2 = 0.06, 0.08
        fb_dot = DashedVMobject(ax.plot(lambda q: (q / force_balance_Q(1.0, phi2, f2, 2.0)) ** (2 / 3), x_range=[0, 3.95]),
                                num_dashes=80, dashed_ratio=0.25).set_stroke(PALETTE[r"\phi_b"], 4)
        q_B = _intersect(lambda D_: bernoulli_Q(D_, 1, 2) - force_balance_Q(D_, phi2, f2, 2), 0.001 + 0.05, 0.6)
        B_dot = Dot(ax.c2p(bernoulli_Q(q_B, 1, 2), q_B), color=PALETTE[r"\phi_b"], radius=0.09)
        B_lab = MathTex("B", font_size=34).next_to(B_dot, DOWN, buff=0.12)
        rough = words("rough, gentle", 24, color=MUTED).next_to(ax.c2p(3.95, (3.95 / force_balance_Q(1.0, 0.01, 0.25, 2.0)) ** (2 / 3)), RIGHT, buff=0.1)
        smooth = words("steep, smooth", 24, color=MUTED).next_to(ax.c2p(3.95, (3.95 / force_balance_Q(1.0, phi2, f2, 2.0)) ** (2 / 3)), RIGHT, buff=0.1)
        with self.narrate(
            "For a rough, gently sloping channel, the crossing is on the subcritical branch, at A. For a steep, "
            "smooth channel it's supercritical, at B. In that case, we assume the flow passes through the critical "
            "point at the outlet, and use the critical flow equations instead."
        ) as n:
            self.play(FadeIn(A_dot, scale=2), FadeIn(A_lab), FadeIn(rough), run_time=n.frac(0.2))
            self.play(Create(fb_dot), FadeIn(smooth), run_time=n.frac(0.2))
            self.play(FadeIn(B_dot, scale=2), FadeIn(B_lab), run_time=n.frac(0.15))
            self.wait(n.frac(0.15))
            self.play(Indicate(Cpt, scale_factor=2), Indicate(C_lab), run_time=n.frac(0.2))


def _intersect(f, a, b):
    from scipy.optimize import brentq

    return brentq(f, a, b)


class Incision(ExplainerScene):
    """Melting the channel"""

    def construct(self):
        floor0 = Line(5.5 * LEFT, 1.0 * RIGHT).shift(0.3 * DOWN)
        ice = Rectangle(width=6.5, height=2.4).set_fill(ICE, 1).set_stroke(ICE_DARK, 2)
        ice.next_to(floor0, DOWN, buff=0).align_to(floor0, LEFT)
        water = Rectangle(width=6.5, height=0.9).set_fill(WATER, 0.95).set_stroke(BLUE, 1.5).next_to(ice, UP, buff=0)
        flow_arrows = VGroup(*[Arrow(LEFT * 0.5, RIGHT * 0.5, buff=0, color=WHITE, stroke_width=3).move_to(
            water.get_center() + np.array([x, 0, 0])) for x in (-2.2, -0.4, 1.4)])
        heat = VGroup(*[
            FunctionGraph(lambda y: 0.08 * np.sin(14 * y), x_range=[0, 0.7]).rotate(-PI / 2).move_to(
                ice.get_top() + np.array([x, -0.05, 0])).set_stroke(ORANGE, 3)
            for x in np.linspace(-2.6, 2.6, 7)
        ])
        towel = Towel(height=1.4).to_corner(DR, buff=0.4)
        with self.narrate(
            "Finally, the channel itself. We assume the lake is at zero degrees, so the only source of heat is "
            "friction in the turbulent flow."
        ) as n:
            self.play(FadeIn(ice), FadeIn(water), FadeIn(towel, shift=LEFT), run_time=n.frac(0.25))
            self.play(*towel.says("Zero degrees? Where's the heat from?", side=LEFT, font_size=26, wrap=20), run_time=n.frac(0.25))
            self.play(LaggedStart(*[GrowArrow(a) for a in flow_arrows], lag_ratio=0.3), run_time=n.frac(0.2))
            self.play(Create(heat), *towel.debubble("thinking"), run_time=n.frac(0.2))

        eq11 = ceq("m", "=", r"{\tau_F \, v \, w", r"\over L}", size=44)
        eq12 = ceq(r"{d", "h_C", r"\over dt}", "=", r"-{", "f_R", r"\rho_w", r"\over 8 L \rho_i}", r"\, v^3", size=48)
        VGroup(eq11, eq12).arrange(DOWN, buff=0.5).to_edge(UP, buff=0.6).shift(2.2 * LEFT)
        melt_shift = 0.35 * DOWN
        with self.narrate(
            "The heat dissipated by that friction melts ice, and we assume it all goes into the channel bottom. So "
            "the channel bottom lowers at a rate proportional to the velocity cubed."
        ) as n:
            self.play(Write(eq11), run_time=n.frac(0.3))
            self.play(ice.animate.stretch_to_fit_height(ice.height - 0.35, about_edge=DOWN),
                      water.animate.shift(melt_shift), flow_arrows.animate.shift(melt_shift),
                      heat.animate.shift(melt_shift), towel.change("happy", look_at=ice), run_time=n.frac(0.35))
            self.play(Write(eq12), run_time=n.frac(0.3))

        items = [
            "1  discharge set at one point, the lake outlet",
            "2  steady, uniform flow at the outlet",
            "3  melting ignored in Bernoulli's balance",
            "4  melt only on the channel floor",
            "5  frictional heat used locally",
        ]
        lst = VGroup(*[words(s, 28) for s in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        lst.to_edge(LEFT, buff=0.8).shift(0.2 * DOWN)
        with self.narrate(
            "These assumptions are restrictive, but as we'll see, the model gives useful insight into how drainage works."
        ) as n:
            self.play(FadeOut(VGroup(ice, water, flow_arrows, heat, eq11)), eq12.animate.to_corner(UR, buff=0.6),
                      run_time=n.frac(0.2))
            self.play(LaggedStart(*[FadeIn(i, shift=0.2 * RIGHT) for i in lst], lag_ratio=0.25), run_time=n.frac(0.7))
        self.idle(1.0)


class Reduction(ExplainerScene):
    """Two competing mechanisms"""

    def construct(self):
        geo = Geo(center=[-4.4, -3.3, 0], k=0.22, W0=1.5, chan_len=2.6, slope=0.1, far=2.0)
        sec = geo.mobs(10, 9, D=0.6)
        z_arrow = DoubleArrow(geo.pt(geo.x_out + 0.25, 9), geo.pt(geo.x_out + 0.25, 10), buff=0, color=YELLOW,
                              stroke_width=4, tip_length=0.12, max_tip_length_to_length_ratio=0.5)
        lvl = DashedLine(geo.pt(0.6, 10), geo.pt(geo.x_out + 0.5, 10), color=PALETTE["h_L"], dash_length=0.06)
        z_lab = sym(r"\zeta", 36).next_to(z_arrow, RIGHT, buff=0.08)
        eqz = ceq(r"\zeta", "=", "h_L", "-", "h_C", size=48).to_edge(UP, buff=0.5)
        with self.narrate(
            "Now the analysis. Define zeta as the height of the lake surface above the bottom of the channel."
        ) as n:
            self.play(FadeIn(sec), Write(eqz), run_time=n.frac(0.5))
            self.play(Create(lvl), GrowFromCenter(z_arrow), FadeIn(z_lab), run_time=n.frac(0.4))

        e13 = ceq("D", "=", r"\zeta", "-", r"{v^2 \over 2g}", size=40)
        e14 = ceq("D", "=", r"{v^2", "f_R", r"\over 8 g", r"\phi_b", "}", size=40)
        pair = VGroup(e13, e14).arrange(RIGHT, buff=1.2).next_to(eqz, DOWN, buff=0.5)
        e15 = ceq("v^2", "=", r"\zeta", r"\, {2g \over 1 + ", "f_R", r"/ 4", r"\phi_b", "}", size=44).move_to(pair)
        with self.narrate("Combining Bernoulli and the force balance, the flow velocity squared is proportional to zeta.") as n:
            self.play(FadeIn(pair, shift=0.2 * DOWN), run_time=n.frac(0.35))
            self.play(TransformMatchingTex(pair, e15), run_time=n.frac(0.45))

        e16 = ceq(r"{d", "h_C", r"\over dt}", "=", "-", r"\alpha", r"\zeta", "^{3/2}", size=46)
        e19 = ceq("Q", "=", r"\beta", r"\zeta", "^{3/2}", size=46)
        pair2 = VGroup(e16, e19).arrange(RIGHT, buff=1.4).next_to(e15, DOWN, buff=0.5)
        with self.narrate(
            "So both the channel incision rate and the discharge go like zeta to the power three halves, with "
            "coefficients we call alpha and beta."
        ) as n:
            self.play(FadeIn(e16, shift=0.2 * UP), run_time=n.frac(0.3))
            self.play(FadeIn(e19, shift=0.2 * UP), run_time=n.frac(0.3))
            self.play(Indicate(e16[5]), Indicate(e19[2]), run_time=n.frac(0.3))

        e21 = ceq(r"{d", "h_L", r"\over dt}", "=", r"{1", r"\over", "A_{Li}", "}", r"\left({h_{Li} \over", "h_L",
                  r"}\right)^{p_L-1}", r"\left[", "Q_{in}", "-", r"\beta", r"\zeta", r"^{3/2}", r"\right]", size=42)
        e21.next_to(pair2, DOWN, buff=0.5)
        with self.narrate(
            "Putting these into the lake equation reduces the whole model to two ordinary differential equations. "
            "And subtracting them tells us how zeta changes."
        ) as n:
            self.play(FadeOut(e15), pair2.animate.next_to(eqz, DOWN, buff=0.5), run_time=n.frac(0.2))
            e21.next_to(pair2, DOWN, buff=0.5)
            self.play(Write(e21), run_time=n.frac(0.45))

        e22 = ceq(r"{d", r"\zeta", r"\over dt}", "=", r"{1", r"\over", "A_{Li}", "}", r"\left({h_{Li} \over", "h_L",
                  r"}\right)^{p_L-1}", r"\left(", "Q_{in}", "-", r"\beta", r"\zeta", r"^{3/2}", r"\right)", "+",
                  r"\alpha", r"\zeta", r"^{3/2}", size=44)
        e22.move_to(DOWN * 0.4)
        b1 = Brace(e22[4:18], DOWN, color=PALETTE["h_L"])
        b1_lab = words("lake level", 28, color=PALETTE["h_L"]).next_to(b1, DOWN, buff=0.1)
        b2 = Brace(e22[19:22], UP, color=PALETTE["h_C"])
        b2_lab = words("channel incision", 28, color=PALETTE["h_C"]).next_to(b2, UP, buff=0.1)
        with self.narrate(
            "This equation contains the two competing mechanisms that control drainage. The first term is the lake "
            "level changing, because of the imbalance between input and discharge. The second is the channel "
            "incising into the ice."
        ) as n:
            self.play(FadeOut(VGroup(pair2, sec, z_arrow, lvl, z_lab)), ReplacementTransform(e21, e22), run_time=n.frac(0.25))
            self.wait(n.frac(0.1))
            self.play(GrowFromCenter(b1), FadeIn(b1_lab), run_time=n.frac(0.25))
            self.play(GrowFromCenter(b2), FadeIn(b2_lab), run_time=n.frac(0.25))
        self.idle(0.6)


class StabilityParameter(ExplainerScene):
    """Stable and unstable drainage"""

    def construct(self):
        e25 = ceq(r"{d", r"\zeta", r"\over dt}", "=", r"\zeta", "^{3/2}", r"\left(", r"\alpha", "-", r"{", r"\beta",
                  r"\over", "A_{Li}", "}", r"\right)", size=50).to_edge(UP, buff=0.6)
        with self.narrate(
            "Start with the simplest lake: vertical walls, and no input of water. Then d zeta by d t is zeta to the "
            "three halves, times alpha minus beta over the lake area."
        ) as n:
            self.play(Write(e25), run_time=n.frac(0.6))

        e26 = ceq(r"\Lambda", "=", r"\alpha", "-", r"{", r"\beta", r"\over", "A_{Li}", "}", size=50)
        e26.next_to(e25, DOWN, buff=0.5)
        box = SurroundingRectangle(e25[6:15], color=GOLD, buff=0.08)
        with self.narrate("We call that bracket the drainage stability parameter, Lambda.") as n:
            self.play(Create(box), run_time=n.frac(0.4))
            self.play(TransformFromCopy(e25[7:14], e26[2:]), FadeIn(e26[:2]), run_time=n.frac(0.5))

        # feedback loop
        loop_c = 1.3 * DOWN + 3.2 * LEFT
        n1 = sym(r"\zeta", 50).move_to(loop_c + 1.3 * UP)
        n2 = ceq("Q", size=50).move_to(loop_c + 1.4 * RIGHT + 0.4 * DOWN)
        n3 = words("incision outpaces drawdown", 26, color=PALETTE["h_C"]).move_to(loop_c + 1.4 * DOWN)
        arrows = VGroup(
            CurvedArrow(n1.get_right() + 0.1 * RIGHT, n2.get_top() + 0.1 * UP, angle=-PI / 3, color=MUTED),
            CurvedArrow(n2.get_bottom() + 0.1 * DOWN, n3.get_right() + 0.1 * RIGHT + 0.15 * UP, angle=-PI / 3, color=MUTED),
            CurvedArrow(n3.get_left() + 0.1 * LEFT + 0.15 * UP, n1.get_left() + 0.1 * LEFT, angle=-PI / 2, color=MUTED),
        )
        up_tags = VGroup(*[MathTex(r"\uparrow", font_size=40).next_to(m, RIGHT, buff=0.08) for m in (n1, n2)])
        cond_pos = ceq(r"\Lambda", "> 0", size=44).next_to(n1, LEFT, buff=1.4)
        with self.narrate(
            "If Lambda is positive, zeta grows. The channel incises faster than the lake surface is drawn down. And "
            "since discharge increases with zeta, there's a positive feedback, and the discharge grows unboundedly. "
            "We call this unstable drainage. The lake always empties."
        ) as n:
            self.play(FadeIn(cond_pos), FadeIn(n1), FadeIn(up_tags[0]), run_time=n.frac(0.15))
            self.play(Create(arrows[0]), FadeIn(n2), FadeIn(up_tags[1]), run_time=n.frac(0.2))
            self.play(Create(arrows[1]), FadeIn(n3), run_time=n.frac(0.2))
            self.play(Create(arrows[2]), run_time=n.frac(0.15))
            self.play(LaggedStart(Indicate(n1), Indicate(n2), Indicate(n3), lag_ratio=0.5), run_time=n.frac(0.2))
        unstable_lab = words("unstable", 30, color=GOLD).next_to(VGroup(n1, n2, n3), RIGHT, buff=0.8)

        neg = words("drawdown outpaces incision: stable", 28, color=PALETTE["h_L"]).next_to(VGroup(n1, n2, n3), DOWN, buff=0.4)
        with self.narrate(
            "If Lambda is negative, the lake surface is drawn down faster than the channel incises, so zeta and the "
            "discharge decrease. This is stable drainage."
        ) as n:
            self.play(FadeIn(unstable_lab), run_time=n.frac(0.2))
            self.play(FadeIn(neg, shift=0.2 * UP), run_time=n.frac(0.4))

        # Fig 5: Q(t) from Eqn 28 for six lake areas
        loop_group = VGroup(n1, n2, n3, arrows, up_tags, unstable_lab, neg, cond_pos)
        e28 = ceq("Q", "=", r"{", r"\beta", r"\over", r"\left( 1/\sqrt{", r"\zeta", r"_0} \;-\;", r"\Lambda",
                  r"t/2 \right)^3", "}", size=42)
        ax = Axes(x_range=[0, 35, 5], y_range=[0, 5, 1], x_length=6.4, y_length=4.4, tips=False,
                  axis_config={"color": MUTED, "font_size": 24}, x_axis_config={"numbers_to_include": [0, 10, 20, 30]},
                  y_axis_config={"numbers_to_include": [1, 2, 3, 4, 5]}).to_edge(RIGHT, buff=1.5).shift(0.5 * DOWN)
        xl = words("time (days)", 24).next_to(ax.x_axis, DOWN, buff=0.4)
        yl = ceq("Q", r"\,/\,", "Q", "_0", size=30).next_to(ax.y_axis, LEFT, buff=0.35)
        base = Lake(phi_b=0.01)
        zeta0 = 1.0  # Fig 5 is reproduced by zeta0 = 1 m with Q shown relative to its initial value
        curves, labels = VGroup(), VGroup()
        for A_km2 in (0.5, 2, 4, 6.2, 8, 15):
            lk = replace(base, A_Li=A_km2 * 1e6, zeta0=zeta0)
            ts = np.linspace(0, 35, 300)
            qs = np.minimum(analytic_Q(lk, ts) / lk.beta, 5.2)
            keep = qs <= 5.0
            c = VMobject().set_points_smoothly([ax.c2p(t, q) for t, q in zip(ts[keep], qs[keep])])
            col = interpolate_color(ManimColor(PALETTE["h_L"]), ManimColor(PALETTE["h_C"]), min(A_km2 / 15, 1))
            c.set_stroke(col, 4)
            curves.add(c)
            lab = MathTex(f"{A_km2:g}" + r"\ \mathrm{km^2}", font_size=24, color=col)
            end = c.get_end()
            lab.next_to(end, RIGHT if A_km2 < 15 else LEFT, buff=0.1)
            labels.add(lab)
        right = sorted([l for l in labels[:-1]], key=lambda m: m.get_y())
        for lo_, hi_ in zip(right, right[1:]):
            if hi_.get_y() - lo_.get_y() < 0.3:
                hi_.set_y(lo_.get_y() + 0.3)
        with self.narrate(
            "The equation can be solved exactly. Here's the discharge over time for lakes of different areas, with "
            "a two metre wide channel sloping at one percent. Above about six square kilometres, Lambda is positive, "
            "and discharge grows. Below, it decays."
        ) as n:
            self.play(FadeOut(loop_group), FadeOut(box), FadeOut(e25), e26.animate.to_corner(UL, buff=0.7), run_time=n.frac(0.1))
            e28.next_to(e26, DOWN, buff=0.6, aligned_edge=LEFT)
            self.play(Write(e28), run_time=n.frac(0.2))
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=n.frac(0.1))
            self.play(LaggedStart(*[Create(c) for c in curves], lag_ratio=0.25), run_time=n.frac(0.35))
            self.play(FadeIn(labels), run_time=n.frac(0.15))
        self.idle(0.8)


class PhysicalControls(ExplainerScene):
    """What controls stability"""

    def construct(self):
        e29 = ceq(r"\Lambda", "=", r"{", "f_R", r"\rho_w", r"\over 8 L \rho_i}", r"\left({2g \over 1+", "f_R", r"/4",
                  r"\phi_b", r"}\right)^{3/2}", r"\left[\, 1 -", r"{(\rho_i L/\rho_w g)", r"\,", "w", r"\over",
                  "A_{Li}", r"\,", r"\phi_b", r"}", r"\right]", size=42).to_edge(UP, buff=0.5)
        self.add(e29)
        rows = [
            ("lake area", "slower", "no change", "less stable"),
            ("channel width", "faster", "no change", "more stable"),
            ("channel slope", "faster*", "faster", "less stable"),
            ("smoother channel", "faster*", "faster*", "no effect"),
            ("snow dam height", "faster", "faster", "no effect"),
        ]
        heads = ["increase", "lake drawdown", "channel incision", "stability"]
        col_x = [-4.6, -1.3, 1.6, 4.6]
        y0 = 1.3
        head = VGroup(*[words(h, 26, color=MUTED).move_to([x, y0, 0]) for h, x in zip(heads, col_x)])
        rule = Line([-6.3, y0 - 0.3, 0], [6.3, y0 - 0.3, 0], stroke_width=1.5, color=MUTED)
        cells = []
        for i, r in enumerate(rows):
            y = y0 - 0.75 - 0.62 * i
            cols = [PALETTE["A_{Li}"], PALETTE["w"], PALETTE[r"\phi_b"], PALETTE["f_R"], PALETTE[r"\zeta"]]
            cell = VGroup(words(r[0], 28, color=cols[i]).move_to([col_x[0], y, 0]))
            for j in (1, 2, 3):
                cc = TEXT_COLOR if r[j] != "no effect" else MUTED
                if r[j] == "less stable":
                    cc = PALETTE["h_C"]
                if r[j] == "more stable":
                    cc = PALETTE["h_L"]
                cell.add(words(r[j], 26, color=cc).move_to([col_x[j], y, 0]))
            cells.append(cell)
        note = words("* partly offset by a change in flow depth or shear stress", 22, color=MUTED).to_edge(DOWN, buff=0.4)
        towel = Towel(height=1.3).to_corner(DR, buff=0.3)

        with self.narrate(
            "So what controls stability? First, the lake area. For a given outflow, the channel incision rate doesn't "
            "depend on the lake's area. But the larger the lake, the slower its level drops. So larger lakes "
            "encourage unstable drainage."
        ) as n:
            self.play(FadeIn(head), Create(rule), Indicate(e29[16], scale_factor=1.6), run_time=n.frac(0.25))
            self.play(FadeIn(cells[0], shift=0.2 * UP), FadeIn(towel, shift=UP), run_time=n.frac(0.25))
            self.play(*towel.says("Bigger lakes are less stable?", side=LEFT, font_size=24, wrap=16), run_time=n.frac(0.3))
        self.play(*towel.debubble("thinking"))

        with self.narrate(
            "A steeper channel makes the water flow faster, which speeds up both incision and drawdown. For drawdown "
            "this is partly compensated by a shallower flow, so the net effect is to promote unstable drainage."
        ) as n:
            self.play(Indicate(e29[9], scale_factor=1.5), Indicate(e29[18], scale_factor=1.5), run_time=n.frac(0.3))
            self.play(FadeIn(cells[2], shift=0.2 * UP), FadeIn(note), run_time=n.frac(0.3))
        with self.narrate(
            "A wider channel doesn't change the incision rate, but it carries more water for a given velocity, which "
            "speeds up drawdown. So wider channels promote stable drainage."
        ) as n:
            self.play(Indicate(e29[14], scale_factor=1.6), run_time=n.frac(0.3))
            self.play(FadeIn(cells[1], shift=0.2 * UP), run_time=n.frac(0.3))
        with self.narrate(
            "Interestingly, the roughness of the channel doesn't appear in the square brackets, so it doesn't affect "
            "stability. A smoother channel speeds the flow, but makes it shallower, and the lower shear stress means "
            "less heat for incision. The effects balance."
        ) as n:
            bracket_box = SurroundingRectangle(e29[11:21], color=PALETTE["f_R"], buff=0.08)
            self.play(Create(bracket_box), towel.change("surprised", look_at=e29), run_time=n.frac(0.3))
            self.play(FadeIn(cells[3], shift=0.2 * UP), run_time=n.frac(0.3))
        with self.narrate(
            "And the height of the snow dam doesn't appear at all. It sets how fast the lake drains, but not whether "
            "drainage is stable."
        ) as n:
            self.play(FadeIn(cells[4], shift=0.2 * UP), FadeOut(bracket_box), towel.change("happy"), run_time=n.frac(0.4))
        self.idle(1.0)


class StableButComplete(ExplainerScene):
    """Stopping with water left behind"""

    def construct(self):
        lk = Lake(phi_b=0.01)
        al, z0, hLi = lk.alpha, 1.0, 10.0
        Lc = -al / (hLi / z0 - 1)
        ax = Axes(x_range=[0, 2.2, 1], y_range=[0, 10.5, 5], x_length=7.0, y_length=5.0, tips=False,
                  axis_config={"color": MUTED, "include_ticks": False}).to_edge(LEFT, buff=1.3).shift(0.2 * UP)
        xl = VGroup(words("lake surface above channel bottom", 24), sym(r"\zeta", 32)).arrange(RIGHT, buff=0.15)
        xl.next_to(ax.x_axis, DOWN, buff=0.7)
        yl = VGroup(words("channel bottom above lake bed", 24), sym("h_C", 32)).arrange(RIGHT, buff=0.15)
        yl.rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.2)
        start = Dot(ax.c2p(z0, hLi - z0), radius=0.09, color=WHITE)
        z0_lab = ceq(r"\zeta", "_0", size=32).next_to(start, UP, buff=0.12)
        towel = Towel(height=1.3).to_corner(DR, buff=0.3)

        with self.narrate(
            "During stable drainage, does the lake empty? Let's plot the height of the channel bottom against zeta."
        ) as n:
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), FadeIn(towel, shift=UP), run_time=n.frac(0.4))
            self.play(*towel.says("Why stop with water left?", side=LEFT, font_size=24, wrap=14), run_time=n.frac(0.4))

        def end_of(Lam):
            if Lam == 0:
                return z0, 0.0
            slope = -al / Lam
            if Lam > 0:
                return z0 + (hLi - z0) / -slope, 0.0
            h_at_0 = hLi - z0 - slope * z0
            if h_at_0 > 1e-9:
                return 0.0, h_at_0
            return z0 - (hLi - z0) / slope, 0.0

        cases = [
            (0.1 * al, r"\Lambda > 0"),
            (0.0, r"\Lambda = 0"),
            (Lc / 2, r"\Lambda_C < \Lambda < 0"),
            (Lc, r"\Lambda = \Lambda_C"),
            (3 * Lc, r"\Lambda < \Lambda_C"),
        ]
        lines = VGroup()
        labels = VGroup()
        for L, tex in cases:
            ze, he = end_of(L)
            ln = Line(ax.c2p(z0, hLi - z0), ax.c2p(max(ze, 0.0), he)).set_stroke(GOLD, 4)
            ln.add_tip(tip_length=0.18)
            lines.add(ln)
            lab = MathTex(tex, font_size=24, color=GOLD)
            if he > 1e-9:  # meets the vertical axis
                lab.next_to(ax.c2p(0.45, hLi - z0 + (-al / L) * (0.45 - z0)), UP, buff=0.12)
            else:
                lab.next_to(ax.c2p(ze, 0), DOWN, buff=0.15)
            labels.add(lab)
        e30 = ceq(r"{d", "h_C", r"\over d", r"\zeta", "}", "=", "-", r"{", r"\alpha", r"\over", r"\Lambda", "}", size=44)
        e30.to_corner(UR, buff=0.7).shift(0.6 * LEFT)
        with self.narrate(
            "For our simple lake, every trajectory is a straight line, starting from the moment the snow dam fails."
        ) as n:
            self.play(*towel.debubble("thinking"), FadeIn(start, scale=2), FadeIn(z0_lab), run_time=n.frac(0.3))
            self.play(Write(e30), Create(lines[4]), FadeIn(labels[4]), run_time=n.frac(0.5))

        v_axis = Line(ax.c2p(0, 0), ax.c2p(0, 10.5)).set_stroke(PALETTE["h_L"], 7)
        halt_dot = Dot(lines[4].get_end(), color=PALETTE["h_L"], radius=0.08)
        halt = VGroup(words("meets", 26, color=PALETTE["h_L"]), ceq(r"\zeta", "= 0", size=32),
                      words(": drainage halts", 26, color=PALETTE["h_L"])).arrange(RIGHT, buff=0.1)
        halt.next_to(e30, DOWN, buff=1.6).to_edge(RIGHT, buff=0.5)
        with self.narrate(
            "If the line hits the vertical axis, zeta reaches zero. The lake surface has fallen to the channel "
            "bottom, the flow stops, and water is left in the lake."
        ) as n:
            self.play(Create(v_axis), FadeIn(halt_dot, scale=2), FadeIn(halt), towel.change("plain", look_at=halt_dot),
                      run_time=n.frac(0.4))

        h_axis = Line(ax.c2p(0, 0), ax.c2p(2.2, 0)).set_stroke(PALETTE["h_C"], 7)
        empt = VGroup(words("meets", 26, color=PALETTE["h_C"]), ceq("h_C", "= 0", size=32),
                      words(": lake empties", 26, color=PALETTE["h_C"])).arrange(RIGHT, buff=0.1)
        empt.next_to(halt, DOWN, buff=0.35, aligned_edge=LEFT)
        e32 = ceq(r"\Lambda_C", "=", "-", r"{", r"\alpha", r"\over", r"h_{Li}/", r"\zeta", r"_0 - 1", "}", size=40)
        e32.next_to(e30, DOWN, buff=0.4)
        with self.narrate(
            "If it hits the horizontal axis first, the channel has cut down to the lake bed, and the lake empties. "
            "The dividing line is a critical value, Lambda C. Between Lambda C and zero, drainage is stable, but "
            "still complete."
        ) as n:
            self.play(Create(h_axis), Create(lines[2]), FadeIn(labels[2]), FadeIn(empt), run_time=n.frac(0.25))
            self.play(Create(lines[3]), FadeIn(labels[3]), FadeIn(e32), run_time=n.frac(0.3))
            self.play(Create(lines[1]), Create(lines[0]), FadeIn(labels[0]), FadeIn(labels[1]),
                      towel.change("happy", look_at=lines), run_time=n.frac(0.3))
        self.idle(1.0)


class LakeShape(ExplainerScene):
    """Lakes that narrow as they drain"""

    def construct(self):
        e35 = ceq(r"\tilde\Lambda", "=", r"\alpha", "-", r"{", r"\beta", r"\over", "A_{Li}", "}",
                  r"\left({h_{Li} \over", "h_L", r"}\right)^{p_L-1}", size=46).to_edge(UP, buff=0.5).shift(2.8 * LEFT)
        area = e35[7:12]
        br = Brace(area, DOWN, color=PALETTE["A_L"])
        br_lab = words("one over the current area", 24, color=PALETTE["A_L"]).next_to(br, DOWN, buff=0.1)
        hL = ValueTracker(10.0)
        g = Geo(center=[-3.6, -2.6, 0], k=0.2, W0=2.0, p_L=3, rim=1.0, chan_len=0.01, slope=0.0, below=0.5, far=2.6)
        basin = always_redraw(lambda: g.mobs(hL.get_value(), 10.5))
        top_w = always_redraw(lambda: Line(g.pt(-g.W(hL.get_value()), hL.get_value()), g.pt(g.W(hL.get_value()), hL.get_value()),
                                           color=PALETTE["A_L"], stroke_width=6))
        with self.narrate(
            "Real lakes aren't vertically walled. Usually, the fuller a lake is, the larger its area. Then the lake "
            "area in the stability parameter is replaced by the current area, which shrinks as the lake drains."
        ) as n:
            self.play(FadeIn(basin), Create(top_w), run_time=n.frac(0.25))
            self.play(Write(e35), run_time=n.frac(0.3))
            self.play(GrowFromCenter(br), FadeIn(br_lab), hL.animate.set_value(4.0), run_time=n.frac(0.4))

        ax = Axes(x_range=[0, 3.5, 1], y_range=[0, 10, 5], x_length=5.6, y_length=4.6, tips=False,
                  axis_config={"color": MUTED, "include_ticks": False}).to_edge(RIGHT, buff=0.9).shift(0.6 * DOWN)
        xl = VGroup(words("lake surface above channel bottom", 22), sym(r"\zeta", 30)).arrange(RIGHT, buff=0.12)
        xl.next_to(ax.x_axis, DOWN, buff=0.15)
        yl = sym("h_C", 32).next_to(ax.y_axis, LEFT, buff=0.15)
        trajs = VGroup()
        for i, p in enumerate(np.linspace(1, 3, 11)):
            z, hc = trajectory(replace(FIG7, p_L=p))
            keep = (hc >= 0) & (z <= 3.5)
            pts = [ax.c2p(a, b) for a, b in zip(z[keep], hc[keep])]
            c = VMobject().set_points_smoothly(pts[:: max(1, len(pts) // 120)] + [pts[-1]])
            c.set_stroke(interpolate_color(ManimColor(GOLD), ManimColor(PALETTE["h_L"]), i / 10), 3)
            trajs.add(c)
        p1 = MathTex("p_L = 1", font_size=28, color=GOLD).next_to(trajs[0].get_end(), UP, buff=0.15)
        halted = words("drainage halted", 22).next_to(ax.c2p(0, 2.6), RIGHT, buff=0.15).shift(0.3 * UP)
        emptied = words("lake emptied", 22).next_to(ax.c2p(2.6, 0), UP, buff=0.1)
        incr = VGroup(words("increasing", 22, color=PALETTE["h_L"]), MathTex("p_L", font_size=28, color=PALETTE["h_L"]))
        incr.arrange(RIGHT, buff=0.1).move_to(ax.c2p(2.0, 4.8))
        with self.narrate(
            "Whether drainage starts stable or unstable doesn't depend on the lake's shape. But as the area shrinks, "
            "the lake level falls faster for the same discharge, and catches up with the channel. Drainage always "
            "stabilises, and for more cone shaped lakes it halts before the lake is empty."
        ) as n:
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), hL.animate.set_value(10.0), run_time=n.frac(0.15))
            self.play(Create(trajs[0]), FadeIn(p1), run_time=n.frac(0.2))
            self.play(LaggedStart(*[Create(t) for t in trajs[1:]], lag_ratio=0.2), run_time=n.frac(0.4))
            self.play(FadeIn(halted), FadeIn(incr), run_time=n.frac(0.15))
        self.idle(0.8)


class LakeInput(ExplainerScene):
    """Lakes that keep filling"""

    def construct(self):
        e36 = ceq(r"{d", r"\zeta", r"\over dt}", "=", r"{", "Q_{in}", r"\over", "A_{Li}", "}", "+", r"\Lambda",
                  r"\zeta", "^{3/2}", size=48).to_edge(UP, buff=0.5)
        towel = Towel(height=1.3).to_corner(DL, buff=0.35)
        with self.narrate(
            "Finally, a vertically walled lake that receives meltwater. If Lambda is positive, drainage is unstable "
            "and the lake empties, as before."
        ) as n:
            self.play(Write(e36), run_time=n.frac(0.5))
            self.play(FadeIn(towel, shift=UP), run_time=n.frac(0.2))

        run = simulate(SIM3, days=200)
        zeta = run.h_L - run.h_C
        zstar = (-SIM3.Q_in / (SIM3.A_Li * SIM3.Lambda)) ** (2 / 3)
        ax = Axes(x_range=[0, 20, 5], y_range=[0, 2.0, 0.5], x_length=6.4, y_length=3.4, tips=False,
                  axis_config={"color": MUTED, "font_size": 24}, x_axis_config={"numbers_to_include": [0, 10, 20]},
                  y_axis_config={"include_ticks": False}).shift(1.3 * DOWN + 0.6 * RIGHT)
        xl = words("time (days)", 24).next_to(ax.x_axis, DOWN, buff=0.4)
        yl = sym(r"\zeta", 36).next_to(ax.y_axis, LEFT, buff=0.2)
        keep = run.t <= 20
        curve = VMobject().set_points_smoothly([ax.c2p(t, z) for t, z in zip(run.t[keep][::4], zeta[keep][::4])])
        curve.set_stroke(YELLOW, 5)
        star = DashedLine(ax.c2p(0, zstar), ax.c2p(20, zstar), color=GOLD, dash_length=0.12)
        star_lab = ceq(r"\left(-", "Q_{in}", "/", "A_{Li}", r"\Lambda", r"\right)^{2/3}", size=32).next_to(star, UP, buff=0.12).align_to(star, RIGHT)
        with self.narrate(
            "If Lambda is negative, zeta no longer decays to zero. It relaxes to a positive value, because the input "
            "keeps the lake surface above the bottom of the channel. So incision continues until the lake is "
            "completely empty."
        ) as n:
            self.play(*towel.says("More water in, and it all drains?", side=RIGHT, font_size=24, wrap=16), run_time=n.frac(0.3))
            self.play(*towel.debubble("thinking"), Create(ax), FadeIn(xl), FadeIn(yl), run_time=n.frac(0.15))
            self.play(Create(curve), run_time=n.frac(0.3))
            self.play(Create(star), FadeIn(star_lab), towel.change("happy", look_at=star), run_time=n.frac(0.15))

        e39 = ceq("Q", "=", r"{", "Q_{in}", r"\over", r"1 - ", r"\alpha", "A_{Li}", "/", r"\beta", "}", ">", "Q_{in}", size=46)
        e39.next_to(e36, DOWN, buff=0.35)
        with self.narrate(
            "The discharge settles at a value larger than the input. And the larger the input, the faster the lake "
            "drains, because a higher input maintains a deeper flow in the channel, which incises faster."
        ) as n:
            self.play(Write(e39), run_time=n.frac(0.4))
            self.play(Indicate(e39[11:]), run_time=n.frac(0.3))
        self.idle(0.6)


class Simulations(ExplainerScene):
    """Four simulations"""

    def construct(self):
        runs = [simulate(SIM1, days=110), simulate(SIM2, days=40), simulate(SIM3, days=200), simulate(SIM4, days=120)]
        lakes = [SIM1, SIM2, SIM3, SIM4]
        titles = [
            r"\text{Simulation 1: }\ 1\,\mathrm{km^2},\ \phi_b = 0.01",
            r"\text{Simulation 2: }\ 3\,\mathrm{km^2},\ \phi_b = 0.03",
            r"\text{Simulation 3: }\ 1\,\mathrm{km^2},\ Q_{in} = 5\,\mathrm{m^3\,s^{-1}}",
            r"\text{Simulation 4: }\ 3\,\mathrm{km^2},\ p_L = 3",
        ]

        def panel(i, x):
            lk, run = lakes[i], runs[i]
            s = ValueTracker(0.0)
            g = Geo(center=[x - 0.9, 0.3, 0], k=0.2, W0=1.25, p_L=lk.p_L, rim=1.2, chan_len=2.2, slope=0.09, far=1.6, below=0.8)

            def draw():
                hL, hC, Q, t = run_tracker(run, s.get_value())
                D = lk.outlet(hL - hC)[2] if hL > hC else 0.0
                return g.mobs(max(hL, 0), max(hC, 0.0), D=D)

            sec = always_redraw(draw)
            q_max = max(6.0, float(np.nanmax(run.Q[run.t <= run.t[-1]])) * 1.05) if i != 1 else 30.0
            t_max = run.t[-1]
            ax = Axes(x_range=[0, t_max, t_max], y_range=[0, q_max, q_max], x_length=4.6, y_length=1.7, tips=False,
                      axis_config={"color": MUTED, "include_ticks": False}).move_to([x, -2.55, 0])
            qlab = sym("Q", 28).next_to(ax.y_axis, LEFT, buff=0.1)
            tl = MathTex(f"{t_max:.0f}" + r"\ \mathrm{days}", font_size=22, color=MUTED).next_to(ax.x_axis.get_end(), DOWN, buff=0.1)
            qm = MathTex(f"{q_max:.0f}", font_size=22, color=MUTED).next_to(ax.y_axis.get_end(), LEFT, buff=0.1)
            trace = always_redraw(lambda: _trace(ax, run, s.get_value(), q_max))
            title = MathTex(titles[i], font_size=28).move_to([x, 3.35, 0])
            return s, VGroup(title, sec, ax, qlab, tl, qm, trace)

        with self.narrate(
            "Now the full model, solved numerically, including critical flow when it occurs. We use a ten metre deep "
            "lake, a two metre wide channel, and a one metre snow dam."
        ) as n:
            s1, P1 = panel(0, -3.5)
            s2, P2 = panel(1, 3.5)
            self.play(FadeIn(P1), FadeIn(P2), run_time=n.frac(0.4))

        with self.narrate(
            "In simulation one, a one square kilometre lake with a gently sloping channel drains stably. The "
            "discharge starts at two point eight cubic metres per second and falls. After a hundred days the lake "
            "has dropped only about a metre, and drainage stops."
        ) as n:
            self.play(s1.animate.set_value(1.0), run_time=n.frac(0.85), rate_func=linear)
        with self.narrate(
            "In simulation two, a three square kilometre lake with a steeper channel drains unstably. The discharge "
            "grows, and after twenty two days the channel has cut down to the lake bed."
        ) as n:
            self.play(s2.animate.set_value(1.0), run_time=n.frac(0.85), rate_func=linear)
        self.play(FadeOut(P1), FadeOut(P2))

        with self.narrate(
            "In simulation three, the small lake gets a steady input of five cubic metres per second. The discharge "
            "rises to about six, and the lake drains stably but completely."
        ) as n:
            s3, P3 = panel(2, -3.5)
            inflow = Arrow([-6.5, 2.75, 0], [-5.3, 2.35, 0], buff=0, color=TEXT_COLOR, stroke_width=5)
            in_lab = sym("Q_{in}", 28).next_to(inflow.get_start(), DOWN, buff=0.1)
            self.play(FadeIn(P3), GrowArrow(inflow), FadeIn(in_lab), run_time=n.frac(0.2))
            self.play(s3.animate.set_value(1.0), run_time=n.frac(0.75), rate_func=linear)
        with self.narrate(
            "In simulation four, the large lake is cone shaped. Discharge grows for eleven days, peaks, and falls as "
            "the shrinking lake stabilises, and drainage ends with water left in the lake."
        ) as n:
            s4, P4 = panel(3, 3.5)
            self.play(FadeIn(P4), run_time=n.frac(0.15))
            self.play(s4.animate.set_value(1.0), run_time=n.frac(0.8), rate_func=linear)
        self.idle(0.8)


def _trace(ax, run, s, q_max):
    t_now = s * run.t[-1]
    keep = (run.t <= t_now + 1e-9) & (run.Q <= q_max)
    if keep.sum() < 2:
        return VGroup(Dot(ax.c2p(0, min(run.Q[0], q_max)), radius=0.05, color=TEAL))
    pts = [ax.c2p(t, q) for t, q in zip(run.t[keep][::3], run.Q[keep][::3])]
    line = VMobject().set_points_as_corners(pts).set_stroke(TEAL, 4)
    return VGroup(line, Dot(pts[-1], radius=0.06, color=TEAL))


class Sensitivity(ExplainerScene):
    """Exploring parameter space"""

    def construct(self):
        areas, slopes, h = final_depth_map()
        ax = Axes(x_range=[0, 19, 5], y_range=[0.004, 0.046, 0.01], x_length=7.6, y_length=5.0, tips=False,
                  axis_config={"color": MUTED, "font_size": 24},
                  x_axis_config={"numbers_to_include": [5, 10, 15]},
                  y_axis_config={"numbers_to_include": [0.01, 0.02, 0.03, 0.04], "decimal_number_config": {"num_decimal_places": 2}})
        ax.to_edge(LEFT, buff=1.4).shift(0.2 * DOWN)
        xl = VGroup(words("initial lake area (km²)", 24), sym("A_{Li}", 30)).arrange(RIGHT, buff=0.12)
        xl.next_to(ax.x_axis, DOWN, buff=0.45)
        yl = VGroup(words("channel slope", 24), sym(r"\phi_b", 30)).arrange(RIGHT, buff=0.12).rotate(PI / 2)
        yl.next_to(ax.y_axis, LEFT, buff=0.55)

        lo, hi = np.array(color_to_rgb(BACKGROUND)) * 0.6 + 0.12, np.array(color_to_rgb(BLUE))
        frac = (h / 9.0)[::-1, :]  # rows top to bottom = high slope to low
        rgb = (lo[None, None, :] * (1 - frac[..., None]) + hi[None, None, :] * frac[..., None])
        image = ImageMobject((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
        image.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        x0, x1 = areas[0] / 1e6, areas[-1] / 1e6
        y0, y1 = slopes[0], slopes[-1]
        image.stretch_to_fit_width(ax.c2p(x1, 0)[0] - ax.c2p(x0, 0)[0]).stretch_to_fit_height(ax.c2p(0, y1)[1] - ax.c2p(0, y0)[1])
        image.move_to((ax.c2p(x0, y0) + ax.c2p(x1, y1)) / 2)

        bar = VGroup(*[Rectangle(width=0.35, height=0.4).set_fill(rgb_to_color(lo * (1 - f) + hi * f), 1).set_stroke(width=0)
                       for f in np.linspace(0, 1, 10)]).arrange(UP, buff=0).next_to(ax, RIGHT, buff=0.5).shift(0.3 * UP)
        bar_t = words("final lake depth", 22).next_to(bar, UP, buff=0.15)
        bar_hi = MathTex(r"9\,\mathrm{m}", font_size=22).next_to(bar, RIGHT, buff=0.1).align_to(bar, UP)
        bar_lo = MathTex(r"0\ \text{(empty)}", font_size=22).next_to(bar, RIGHT, buff=0.1).align_to(bar, DOWN)

        lam0 = VMobject().set_points_smoothly([ax.c2p(A, Lake(phi_b=0.01).A_crit / 1e6 * 0.01 / A) for A in np.linspace(1.4, 15.2, 80)])
        lam0.set_stroke(GOLD, 5)
        lam_lab = ceq(r"\Lambda", "= 0", size=30).next_to(ax.c2p(13, 0.0058), UP, buff=0.12)
        with self.narrate(
            "Running the model for a year across many lake areas and channel slopes maps out where lakes empty. The "
            "boundary follows the curve where Lambda is zero."
        ) as n:
            self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=n.frac(0.2))
            self.play(FadeIn(image), FadeIn(bar), FadeIn(bar_t), FadeIn(bar_hi), FadeIn(bar_lo), run_time=n.frac(0.35))
            self.play(Create(lam0), FadeIn(lam_lab), run_time=n.frac(0.35))

        mean_l = DashedLine(ax.c2p(0.8, 0.004), ax.c2p(0.8, 0.046), dash_length=0.08, color=WHITE)
        max_l = DashedLine(ax.c2p(17, 0.004), ax.c2p(17, 0.046), dash_length=0.18, color=WHITE)
        mean_t = MathTex(r"0.8\,\mathrm{km^2}", font_size=24).next_to(mean_l, UP, buff=0.1)
        max_t = MathTex(r"17\,\mathrm{km^2}", font_size=24).next_to(max_l, UP, buff=0.1)
        src = caption("Greenland lake areas: Selmes and others (2011)", size=22).next_to(ax, UP, buff=0.45)
        with self.narrate(
            "Lakes observed in Greenland average about point eight square kilometres, and reach seventeen. In our "
            "model, the average lake drains stably whatever the slope, while the largest lakes drain unstably on all "
            "but the gentlest channels."
        ) as n:
            self.play(Create(mean_l), Create(max_l), FadeIn(mean_t), FadeIn(max_t), FadeIn(src), run_time=n.frac(0.4))
            self.play(Indicate(mean_l), run_time=n.frac(0.2))
            self.play(Indicate(max_l), run_time=n.frac(0.2))

        kink = DashedLine(ax.c2p(0, 0.0312), ax.c2p(19, 0.0312), color=MUTED, dash_length=0.06)
        crit = words("critical flow above", 22, color=MUTED).next_to(ax.c2p(19, 0.0312), UP, buff=0.08).align_to(ax.c2p(19, 0), RIGHT)
        with self.narrate(
            "On slopes steeper than about three percent the flow becomes critical, and the slope stops mattering. "
            "And changing the snow dam height changes how fast lakes drain, but never moves the boundary."
        ) as n:
            self.play(Create(kink), FadeIn(crit), run_time=n.frac(0.4))
            self.play(Indicate(lam0, color=GOLD), run_time=n.frac(0.3))
        self.idle(0.8)


class Discussion(ExplainerScene):
    """Limitations and implications"""

    def construct(self):
        items = [
            "no variation along the channel",
            "no heat carried by the lake water",
            "constant channel width",
            "no ice flow",
            "a single channel",
            "starts with a snow dam, not overtopping",
        ]
        head = heading("Limitations", 40).to_edge(UP, buff=0.6)
        lst = VGroup(*[words(s, 30) for s in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(head, DOWN, buff=0.5)
        with self.narrate(
            "The model has important limitations. It ignores variation along the channel, the heat carried by the "
            "lake water, changes in channel width, ice flow, and drainage through more than one channel. And it "
            "assumes drainage starts with a snow dam, rather than water overtopping the lake's basin."
        ) as n:
            self.play(FadeIn(head), run_time=n.frac(0.1))
            self.play(LaggedStart(*[FadeIn(i, shift=0.2 * RIGHT) for i in lst], lag_ratio=0.5), run_time=n.frac(0.8))
        self.play(FadeOut(head), FadeOut(lst))

        # ice-sheet profile: margin on the left, interior on the right
        xs = np.linspace(-6.5, 6.5, 120)
        surf = lambda x: -2.4 + 3.6 * np.sqrt(np.clip((x + 6.5) / 13, 0, 1))
        sheet = Polygon(*[[x, surf(x), 0] for x in xs], [6.5, -3.2, 0], [-6.5, -3.2, 0]).set_fill(ICE, 1).set_stroke(ICE_DARK, 2)
        lake_now = VGroup(*[Ellipse(width=0.35, height=0.12).set_fill(WATER, 1).set_stroke(BLUE, 1).move_to([x, surf(x) + 0.03, 0])
                            for x in (-5.4, -4.6, -3.8)])
        lake_new = VGroup(*[Ellipse(width=0.8, height=0.16).set_fill(WATER, 1).set_stroke(BLUE, 1).move_to([x, surf(x) + 0.03, 0])
                            for x in (-1.8, -0.4, 1.0)])
        warm = Arrow([-4.0, 2.4, 0], [0.8, 2.4, 0], buff=0, color=ORANGE, stroke_width=5)
        warm_t = words("warming: lakes form further inland", 26).next_to(warm, UP, buff=0.1)
        bigger = words("larger lakes: less stable", 26, color=PALETTE["h_C"]).move_to([3.6, 1.7, 0])
        flatter = words("lower slopes: more stable", 26, color=PALETTE["h_L"]).next_to(bigger, DOWN, buff=0.25)
        warm.shift(0.4 * UP + 1.0 * LEFT)
        warm_t.next_to(warm, UP, buff=0.1)
        with self.narrate(
            "Still, it has implications. As the climate warms, lakes will form further inland on the Greenland ice "
            "sheet. There they tend to be larger, which favours unstable drainage, but channel slopes are lower, "
            "which has the opposite effect."
        ) as n:
            self.play(FadeIn(sheet), FadeIn(lake_now), run_time=n.frac(0.2))
            self.play(GrowArrow(warm), FadeIn(warm_t), FadeIn(lake_new), run_time=n.frac(0.3))
            self.play(FadeIn(bigger), run_time=n.frac(0.2))
            self.play(FadeIn(flatter), run_time=n.frac(0.2))

        bed_arrow = Arrow([-1.8, surf(-1.8) - 0.1, 0], [-1.8, -3.0, 0], buff=0, color=TEAL, stroke_width=4)
        slow = words("slower delivery to the bed", 24, color=TEAL).move_to([-4.3, 1.0, 0])
        with self.narrate("Surface drainage also slows the delivery of lake water to the bed, which can reduce the ice sheet's response.") as n:
            self.play(GrowArrow(bed_arrow), FadeIn(slow), run_time=n.frac(0.5))
        self.play(FadeOut(Group(sheet, lake_now, lake_new, warm, warm_t, bigger, flatter, bed_arrow, slow)))

        niv = img(ASSETS / "nivlisen_fig2a.png", 5.6).shift(0.25 * UP)
        cap = caption("Fig. 2a, Kingslake et al. (2015)").next_to(niv, DOWN, buff=0.2)
        ring = Ellipse(width=2.2, height=1.1, color=YELLOW, stroke_width=4).move_to(img_point(niv, 0.53, 0.82))
        with self.narrate(
            "And on Nivlisen, the most rapid drainage seems to come from some of the largest lakes, where the surface "
            "slope is greatest. That is consistent with our theory."
        ) as n:
            self.play(FadeIn(niv), FadeIn(cap), run_time=n.frac(0.3))
            self.play(Create(ring), run_time=n.frac(0.3))
        self.idle(0.5)


class Conclusions(ExplainerScene):
    """Conclusions"""

    def construct(self):
        e22 = ceq(r"{d", r"\zeta", r"\over dt}", "=", r"\zeta", "^{3/2}", r"\Lambda", size=48)
        l1 = words("Drainage: lake drawdown versus channel incision", 32)
        l2 = words("Larger area, input and slope: unstable, empties", 32)
        l3 = words("With an input, a lake always drains completely", 32)
        block = VGroup(l1, e22, l2, l3).arrange(DOWN, buff=0.45).shift(0.3 * UP)
        towel = Towel(mode="happy", height=1.3).to_corner(DR, buff=0.35)
        with self.narrate(
            "To sum up. Surface drainage of a supraglacial lake is a competition between lake drawdown and channel "
            "incision, and its stability is set by the sign of Lambda."
        ) as n:
            self.play(FadeIn(l1, shift=0.2 * UP), run_time=n.frac(0.4))
            self.play(Write(e22), FadeIn(towel, shift=UP), run_time=n.frac(0.4))
        with self.narrate(
            "Lakes are more prone to drain unstably, and empty completely, when their area, their input and their "
            "channel slope are larger. And lakes with an input always drain completely."
        ) as n:
            self.play(FadeIn(l2, shift=0.2 * UP), run_time=n.frac(0.4))
            self.play(FadeIn(l3, shift=0.2 * UP), towel.sway(), run_time=n.frac(0.4))
        self.idle(0.6)


class End(ExplainerScene):
    """Credits"""

    def construct(self):
        self.end_card(
            "Kingslake, J., Ng, F. and Sole, A. (2015). Modelling channelized surface drainage\n"
            "of supraglacial lakes. Journal of Glaciology, 61(225), 185–199.",
            "doi.org/10.3189/2015JoG14J158",
        )


SCENES = [
    ColdOpen,
    Title,
    Geometry,
    Bernoulli,
    ForceBalance,
    Incision,
    Reduction,
    StabilityParameter,
    PhysicalControls,
    StableButComplete,
    LakeShape,
    LakeInput,
    Simulations,
    Sensitivity,
    Discussion,
    Conclusions,
    End,
]
