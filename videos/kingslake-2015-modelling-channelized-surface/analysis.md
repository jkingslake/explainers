# Analysis: Kingslake, Ng & Sole (2015), *Modelling channelized surface drainage of supraglacial lakes*

J. Glaciol. 61(225), 185–199. doi:10.3189/2015JoG14J158. Own paper: narration says "we".
Framing, order, notation and explanations follow the paper; section numbers below refer to it.

## 1. The question (Sections 1–2)

Supraglacial lakes can drain to the bed of ice sheets, affecting ice dynamics, or over their
surface, relocating surface water. Because surface-to-bed drainage is the only way to open new
pathways to the bed of cold, thick ice, where lakes are, and how big they are, controls which
parts of the bed receive meltwater. The paper focuses on surface drainage through a single
channel that forms by melting due to the turbulent dissipation of heat in the flowing water.
Motivating observations: in West Greenland (Fig 1, Landsat, 30 June and 7 July 2001) lake B
drains over the surface into lake A and lake C drains completely; on the Nivlisen ice shelf,
East Antarctica (Fig 2, MODIS/Landsat, 2007/08), lakes on the ice-sheet flank near the
grounding line drain rapidly, and the water travels up to 70 km at 1.7–6.8 m min⁻¹ and floods
~260 km² (~3.3 % of the shelf), nearly every year, but not in the cool summer of 2008/09.
Previous models (Walder & Costa 1996; Raymond & Nolan 2000; Mayer & Schuler 2005; Vincent et
al. 2010) simplified the flow depth by assuming wide, shallow flow or critical flow. Raymond &
Nolan introduced stable drainage (discharge decreases with time) and unstable drainage (discharge
increases), with the criterion that the initial incision rate must exceed the initial rate of
lake-surface lowering. The novelty here: flow depth from Bernoulli's equation plus a force
balance (no wide-shallow or critical-flow assumption), and a detailed analysis of the physical
origin of stable and unstable drainage and of which parameters affect stability and why.

## 2. Takeaway (abstract, Section 7)

Modelled lake drainage can be stable or unstable. During stable drainage the lake level is drawn
down faster than the channel incises, so discharge decreases with time and can stop before the
lake is empty. During unstable drainage the channel incises faster, discharge grows unstably and
the lake always empties. Lakes are more prone to drain unstably when their initial area, their
input and their channel slope are larger.

## 3. Setup and assumptions (Section 3, list on p. 189)

The paper's five stated assumptions:
1. Drainage is controlled entirely by the flow through one point in the channel near the lake,
   the "lake outlet" (no along-channel dimension).
2. Flow at the lake outlet is steady and uniform: it changes slowly in time and along the channel
   (pseudo-steady plug flow).
3. The energy used in melting is ignored in the balance of potential and kinetic energy as water
   flows from the lake to the outlet (Bernoulli).
4. Melt is restricted to, and spread evenly across, the floor of the channel, so the channel's
   width and slope are constant.
5. Heat dissipated by the water flowing through the outlet is used locally for melting.
Also: lake at 0 °C (friction is the only heat source); rectangular channel of constant width w;
constant uniform slope φ_b; lake hypsometry Eqn (1); constant input Q_in; no melting within the
lake; drainage initiated by failure of a snow dam (observed by Tedesco et al. 2013), so the
channel floor starts ζ0 below the lake surface. The authors call these "restrictive", but the
model "still yields useful mechanistic insights".

## 4. Notation and palette (paper's symbols)

| Symbol | Meaning | Units | Typical | Colour |
|---|---|---|---|---|
| ζ | height of lake surface above channel bottom, h_L − h_C | m | ζ0 = 1 m | YELLOW |
| h_L | lake depth (surface above lake bed) | m | h_Li = 10 m | BLUE |
| h_C | height of channel bottom above lake bed | m | 9 m at start | RED |
| Q | discharge at the lake outlet | m³ s⁻¹ | 1–50 | TEAL |
| A_Li (A_L) | reference / initial lake area (current area) | m² | 0.05–30 km² | GREEN |
| Λ | drainage stability parameter, α − β/A_Li | m⁻¹ᐟ² s⁻¹ | ±10⁻⁶ | GOLD |
| α | coefficient in channel incision, dh_C/dt = −αζ^(3/2) | | | PINK |
| β | coefficient in discharge, Q = βζ^(3/2) | | | ORANGE |
| φ_b | channel slope | – | 0.005–0.1 | PURPLE |
| w | channel width | m | 2 | MAROON |
| f_R | hydraulic roughness (Darcy–Weisbach) | – | 0.25 | LIGHT_BROWN #CD853F |
| v, D | surface flow velocity, depth of flow at outlet | m s⁻¹, m | | text colour |
| Q_in, p_L | lake input; lake-shape parameter | | | text colour |
| g, L, ρ_w, ρ_i | 9.8 m s⁻², 334 kJ kg⁻¹, 1000 kg m⁻³, ice density | | | muted |

## 5. The model (Section 3)

**3.1 Lake evolution.** Hypsometry (h_L/h_Li)^p_L = V_L/V_Li (Eqn 1), with
A_Li = p_L V_Li/h_Li; p_L = 1 vertically walled, 1–3 bowl, 3 cone, >3 horn; a surveyed
Greenland lake fits p_L ≈ 1.5. Combined with dV_L/dt = Q_in − Q:
dh_L/dt = (1/A_Li)(h_Li/h_L)^(p_L−1)(Q_in − Q) (Eqn 2).

**3.2 Bernoulli's equation.** z + u²/2g = constant (Eqn 3) along a surface streamline on the
channel centre line, from stagnant lake water (u = 0, z = h_L) to the lake outlet
(u = v, z = h_C + D): h_L = (h_C + D) + v²/2g (Eqn 4). Plug flow in a rectangular channel:
Q = vwD (Eqn 5), so h_L − h_C = D + Q²/(2gw²D²) (Eqn 6). Fig 4's "Bernoulli curve" (D against Q)
has a subcritical branch (dD/dQ < 0, Fr < 1) and a supercritical branch (dD/dQ > 0, Fr > 1)
meeting at the critical point C where Q is maximum: D_C = (2/3)(h_L − h_C),
Q_C = (g w² D_C³)^½ (Eqn 7), with Fr = v (gD)^(−½).

**3.3 Force balance.** Shear stress τ_F = (1/8) f_R ρ_w v² (Darcy–Weisbach, Eqn 8) balances the
along-channel gravitational driving stress τ_G = ρ_w g D φ_b (Eqn 9) on a slab of water of unit
length, unit width and height D. Eliminating v with Eqn 5:
Q = (8gφ_b/f_R)^½ w D^(3/2) (Eqn 10). Fig 4: dashed (rougher, gentler) and dotted (steeper,
smoother) force-balance curves cut the Bernoulli curve at A (subcritical) and B (supercritical).

**3.4 Subcritical and supercritical flow.** When the solution is supercritical, discharge is
assumed to be controlled by a transition through critical flow at the outlet, and Eqn (7) is used.

**3.5 Channel incision.** Lake at 0 °C, so the only heat source is frictional dissipation.
Ice mass melted per unit channel length per unit time m = τ_F v w / L (Eqn 11; Walder & Costa
1996), all at the channel bottom: dh_C/dt = −f_R ρ_w v³ / (8 L ρ_i) (Eqn 12).
Equations (2), (5), (6), (7), (10), (12) complete the model.

## 6. Derivations (Section 4; all checked in `checks.py`)

* ζ = h_L − h_C. Recast Eqns 6 and 10 in terms of v: D = ζ − v²/2g (Eqn 13),
  D = v² f_R/(8gφ_b) (Eqn 14). Eliminate D: v² = ζ · 2g/(1 + f_R/4φ_b) (Eqn 15).
* Into Eqn 12: dh_C/dt = −αζ^(3/2) (Eqn 16), α = (f_R ρ_w/8Lρ_i)(2g/(1 + f_R/4φ_b))^(3/2) (Eqn 17).
* Q = vwD = v³ w f_R/(8gφ_b) (Eqn 18) ⇒ Q = βζ^(3/2) (Eqn 19),
  β = (2g/(1 + f_R/4φ_b))^(3/2) w f_R/(8gφ_b) (Eqn 20).
* Into Eqn 2: dh_L/dt = (1/A_Li)(h_Li/h_L)^(p_L−1)[Q_in − βζ^(3/2)] (Eqn 21). The model is now
  a pair of ODEs for h_L and h_C.
* dζ/dt = (1/A_Li)(h_Li/h_L)^(p_L−1)(Q_in − βζ^(3/2)) + αζ^(3/2) (Eqn 22): **the two competing
  mechanisms**: changes in lake level from the imbalance between input and discharge (first
  term) and downward incision by frictional melting (second term).

**4.1 Vertically sided lake, no input (p_L = 1, Q_in = 0).** dζ/dt = ζ^(3/2)(α − β/A_Li) (Eqn 25).
Drainage stability parameter Λ = α − β/A_Li (Eqn 26). Λ > 0: dζ/dt > 0, ζ increases unstably;
the channel incises faster than the lake surface is drawn down; positive feedback because Q
increases with ζ (Eqn 19); discharge grows unboundedly; the lake always empties. Λ < 0: ζ and Q
always decrease; the lake surface, initially ζ0 above the channel, is drawn down faster than the
channel is incised; stable. Integrating: ζ = (1/√ζ0 − Λt/2)^(−2) (Eqn 27),
Q = β(1/√ζ0 − Λt/2)^(−3) (Eqn 28); for Λ > 0 both blow up at t_b = 2/(Λ√ζ0), but the lake runs
out of water first. Fig 5: Q(t) for six areas (f_R = 0.25, w = 2 m, φ_b = 0.01): Λ = 0 at
A_Li = 6.2 km²; larger lakes grow, smaller decay.

**4.1.2 Physical controls on stability (the paper's explanations).**
Λ = (f_R ρ_w/8Lρ_i)(2g/(1 + f_R/4φ_b))^(3/2) [1 − (ρ_i L/ρ_w g) w/(A_Li φ_b)] (Eqn 29).
* Area A_Li: for a given outflow, the incision rate is independent of lake area (Eqn 23),
  whereas the larger the lake, the slower its level drops ⇒ larger area encourages instability.
* Slope φ_b: increases flow velocity, increasing both incision and drawdown (the factor outside
  the brackets: faster change either way); for drawdown this is slightly compensated by a
  decrease in flow depth (the second term in the brackets decreases) ⇒ net effect promotes
  unstable drainage.
* Width w: incision rate independent of w, but increasing w accelerates drawdown by increasing
  discharge for a given flow velocity (Eqn 5) ⇒ promotes stable drainage.
* Roughness f_R: absent from the brackets ⇒ no effect on stability. Decreasing f_R raises flow
  velocity (affecting both), decreases flow depth (compensating the faster flow's discharge),
  and this is balanced by a decrease in incision from a lower shear stress and so less heat.
* Snow-dam height ζ0: not in Λ ⇒ no effect on stability; it sets the initial discharge, how
  fast the lake empties and, during stable drainage, whether it empties at all.
* Table 1 summarises these.

**4.1.3 Stable but complete drainage.** Phase space h_C–ζ (Fig 6): dh_C/dζ = −α/Λ (Eqn 30), a
straight line from (ζ0, h_Li − ζ0). For Λ < 0 the slope is positive; a gentle trajectory meets
the vertical axis (ζ = 0): drainage halts with water left; a steep one meets the horizontal axis
(h_C = 0): the lake empties. h_final = (h_Li − ζ0) + ζ0 α/Λ (Eqn 31). Critical
Λ_C = −α/(h_Li/ζ0 − 1) (Eqn 32): Λ_C ≤ Λ ≤ 0 gives stable but complete drainage.

**4.2 Non-vertically sided lake (p_L > 1, Q_in = 0).** dζ/dt = ζ^(3/2) Λ̃ (Eqn 34) with
Λ̃ = α − (β/A_Li)(h_Li/h_L)^(p_L−1) (Eqn 35). Initially Λ̃ = Λ, so whether drainage starts
stable or unstable does not depend on shape; as h_L falls the area A_Li(h_L/h_Li)^(p_L−1)
falls, so Λ̃ falls and always drops below zero before the lake empties: drainage stabilises.
This can halt drainage, or only slow the final stages if h_C is already near zero (Fig 7, 11
values of p_L from 1 to 3; the three highest halt). Physically, drawdown for a given discharge
speeds up with no change in incision, so drawdown "catches up".

**4.3 Vertically sided lake with input (p_L = 1, Q_in > 0).** dζ/dt = Q_in/A_Li + Λζ^(3/2)
(Eqn 36). Λ > 0: always positive ⇒ unstable, empties. Λ < 0: ζ relaxes to (−Q_in/A_LiΛ)^(2/3);
the input keeps the lake surface above the channel bottom, so stable drainage and incision
continue until the lake empties. Q = −βQ_in/(A_LiΛ) (Eqn 38) = Q_in/(1 − αA_Li/β) (Eqn 39) > Q_in,
and dh_L/dt = (Q_in/A_Li)(1 − 1/(1 − αA_Li/β)) (Eqn 40): a higher input drains the lake faster,
because it maintains deeper flow and faster incision (numerically this also holds when unstable).

**4.4 Summary.** Λ < −α/(h_Li/ζ0 − 1): stable, halts with water left; −α/(h_Li/ζ0 − 1) ≤ Λ ≤ 0:
stable but complete; Λ > 0: unstable. Larger area, steeper slope, narrower channel ⇒ unstable;
roughness affects only the magnitude of Λ. Shape: Λ̃ falls and stabilises. Input: always empties.

## 7. Scales and regimes

* Subcritical solution: Fr² = v²/gD = 8φ_b/f_R, so with f_R = 0.25 flow is subcritical for
  φ_b < 0.031; paper Fig 10 shows the critical-flow kink at φ_b ≈ 0.032, beyond which drainage
  does not depend on φ_b (Eqn 7 has no φ_b).
* Λ magnitude ~10⁻⁷–10⁻⁶ m⁻¹ᐟ² s⁻¹; with ζ0 = 1 m, |Λ|√ζ0 gives drainage timescales of weeks
  (sim 2: t_b = 2/(Λ√ζ0) ≈ 44 days; the lake empties first).
* f_R = 0.25 from Manning n' = 0.050 m⁻¹ᐟ³ s (Mernild et al. 2006) via f_R = 8gn'²/R_H^(1/3).

## 8. Results, figure by figure

* Fig 1 (Greenland): lake B → lake A over the surface; lake C drains completely.
* Fig 2 (Nivlisen): floods to 70 km; inset temperatures; no flood in 2008/09.
* Fig 3: model geometry before and during drainage.
* Fig 4: Bernoulli and force-balance curves.
* Fig 5: Q(t) for Λ from −5×10⁻⁶ to 2.7×10⁻⁷.
* Fig 6: phase-space trajectories for five Λ (three fates).
* Fig 7: phase-space trajectories for 11 values of p_L.
* Fig 8: sim 1 (A_Li = 1 km², φ_b = 0.01) stable, Q from 2.8 down; after 100 days the level has
  dropped < 1 m [our run: 1.19 m; see note]; sim 2 (3 km², 0.03) unstable, Q from 3.4 up;
  channel at lake bed after 22 days.
* Fig 9: sim 3 (sim 1 + Q_in = 5 m³ s⁻¹) Q → 5.97 m³ s⁻¹, empties; sim 4 (sim 2 with p_L = 3)
  Q rises 11 days, peaks, falls; drainage ends after ~40 days.
* Fig 10: h_final and T_E over (A_Li, φ_b), (A_Li, ζ0), (φ_b, ζ0); green Λ = 0 curves; Selmes et al.
  (2011) mean 0.8 km² and max 17 km² lakes bracket the boundary; ζ0 does not move the boundary;
  small stable-but-complete region (Fig 10f) and unstable-but-incomplete region (Fig 10d, an
  artefact of 1-year runs); kink at φ_b ≈ 0.032 (critical flow).

## 9. Reproduction (`model.py`)

Full model, RK45 (paper: forward Euler; subcritical/critical switch). ρ_i is not stated in the
paper; ρ_i = 900 kg m⁻³ reproduces every quoted number:
sim 1 Λ = −2.37×10⁻⁶ (paper −2.4×10⁻⁶), Λ_C = −5.13×10⁻⁸ (−5.1×10⁻⁸), Q0 = 2.83 (2.8);
sim 2 Λ = 5.30×10⁻⁷ (5.3×10⁻⁷), Q0 = 3.41 (3.4), channel reaches lake bed at 21.5 d (22 d);
sim 3 Q → 5.97 (5.97); sim 4 peak 5.6 m³ s⁻¹ at 10.8 d (11 d), final depth 4.6 m; Fig 5 legend Λ values.
Note: sim 1's lake drops 1.19 m before stalling (Eqn 31 gives the same), whereas the text says
"after 100 days the lake level has dropped <1 m"; Fig 8c shows a final level ≈ 8.8 m, consistent
with ~1.2 m. Treat the "<1 m" as a slip in the text; the video shows the model value.
Sim 4: the run reaches Q = 0.002 m³ s⁻¹ only at ~93 days, though Fig 9d is flat after ~40 days.

## 10. Limitations and open questions (Section 6)

No along-channel variation (a melt–slope–discharge feedback could operate along channels); no
sensible heat in lake water (affects lake shape and incision, may be needed for realism); constant
channel width (deep, vertical-walled channels observed but unexplained); drainage initiated by a
snow dam, not by overtopping without a channel (needs 2D modelling of channel formation); a single
channel (N identical channels give N times the discharge, but unequal channels compete and outflow
may concentrate in one, which may explain single large channels in Figs 1–2); ice flow ignored
(uplift out of the basin raises the channel bottom; flow around the channel raises the bottom and
narrows it); only subcritical flow analysed analytically (critical flow independent of slope and
roughness; competition qualitatively similar).

## 11. Aha moments (the paper's)

1. Surface drainage is a competition between drawdown of the lake surface and incision of the
   channel by frictional heat (Eqn 22).
2. The sign of one quantity, the drainage stability parameter Λ = α − β/A_Li, decides stable
   (discharge falls) versus unstable (discharge grows unboundedly) drainage.
3. Larger lakes and steeper channels promote unstable drainage, wider channels stable; roughness
   and snow-dam height do not affect stability (Eqn 29, Table 1).
4. Stable drainage can halt with water still in the lake (Λ < Λ_C), or be stable but complete.
5. Lakes whose area shrinks as they drain stabilise; lakes with an input always empty
   completely, faster with more input.

## 12. Likely confusions (towel beats)

* "The water is at zero degrees, where does the heat come from?" (Friction, Section 3.5.)
* "Why does a bigger lake make drainage *less* stable?" (Its level drops more slowly.)
* "The roughness doesn't matter?!"
* "Why would drainage stop with water still in the lake?" (ζ reaches zero.)
* "More water coming in, and it empties completely?"

## 13. Notes beyond the paper (not used in the video)

* With τ_F = τ_G, incision = ρ_w g φ_b Q/(ρ_i L w) and drawdown = Q/A, so their ratio
  R = (ρ_w g/ρ_i L)(φ_b A/w) is independent of Q; Λ = α(1 − 1/R). Equivalent to Eqn 29.
* Critical area A_c = (ρ_i L/ρ_w g) w/φ_b ≈ 30.7 km × w/φ_b; L/g ≈ 34 km.
* Eqn 31 can be read as a geometric series: lake drop ζ0/(1 − R).
* Eqn 39 equals Q_in/(1 − R).
* In the critical-flow regime the analogous ratio is (ρ_w g/ρ_i L)(f_R/8)(A/w).

### Typos found in the paper (cross-references; physics consistent)
* Fig 5 caption: Q(t) "calculated using Eqn (32)": should be (28).
* Fig 6 caption: "Λ_C is defined in Eqn (36)": should be (32).
* Section 4.1.2: "absent from the square brackets in Eqn (33)": should be (29).
* Section 4.1.2 and Table 1 call the shear stress τ_b; Eqn 8 names it τ_F.
* Section 5: time-stepping "Eqns (12) and (16)": lake equation is (2)/(21).
* Section 5.1: sim 1 "dropped <1 m" vs model 1.19 m (Fig 8c agrees with the model).
* Section 5.2: 17 km² lake unstable for φ_b > 0.003; Eqn 29 gives 0.0036.
* Table 1, roughness row: the entries ("Increase, partially compensated by decrease in D";
  "Increase, partially compensated by decrease in τ_b") describe *decreasing* f_R, as in the
  Section 4.1.2 text. For increasing f_R with f_R/4φ_b > 2 (all the paper's runs), both α and
  β fall (each ∝ x/(1+x)^(3/2), x = f_R/4φ_b), so drawdown and incision both slow. The stability
  entry ("None") is right. The video phrases this row as "smoother channel", following the text.
* Fig 5: every curve starts at 1.0 on an axis labelled Q (m³ s⁻¹), but with the caption's
  parameters Q0 = β ζ0^(3/2) = 2.8 m³ s⁻¹ for ζ0 = 1 m. The curve shapes (e.g. 8 km² reaching
  ≈1.66 and 15 km² ≈5 at day 35) match ζ0 = 1 m with Q shown relative to Q0; the video plots Q/Q0.
* Fig 7 parameters are not given; A_Li = 4.6 km², φ_b = 0.03 reproduces "the three highest p_L halt".
