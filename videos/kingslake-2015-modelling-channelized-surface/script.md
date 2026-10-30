# Script: Modelling channelized surface drainage of supraglacial lakes

Follows the paper's framing and order (Sections 1–7), its notation (ζ, h_L, h_C, Q, α, β, Λ,
Λ̃, Λ_C, p_L, φ_b, w, f_R) and its own explanations. First person plural (own paper).
Target ≈ 14 min. Palette: analysis.md §4.

## ColdOpen — Lakes that drain over the ice (≈60 s)

**Visual:** Fig 1c (30 June 2001), labels A, B, C. Crossfade to Fig 1d (7 July 2001). Indicate B → A path, then C. Caption: "Landsat 7. Fig. 1, Kingslake et al. (2015)".

**Narration:** Every summer, meltwater collects in hollows on the surface of the Greenland ice sheet, forming lakes.
**Narration:** These two satellite images were taken a week apart. In that week, lake B drained across the ice surface into lake A. And lake C drained away completely.
**Visual:** Fig 2a (Nivlisen), push in on the flood paths. Caption.
**Narration:** In East Antarctica, we found lakes near the grounding line of the ice sheet draining across the Nivlisen ice shelf, with water travelling up to seventy kilometres, nearly every summer.
**Visual:** Simple lake + channel sketch; two outcomes: discharge falls (stable) vs grows (unstable).
**Narration:** Lakes can drain down to the bed of an ice sheet, or over its surface, through a channel that the flowing water melts into the ice. We wanted to understand that surface drainage. When does it fizzle out, and when does it run away and empty the lake?

## Title — Title (≈8 s)

**Narration:** That's the question of our twenty fifteen paper in the Journal of Glaciology.

## Geometry — The model lake (≈70 s)

**Visual:** Build Fig 3: ice, lake, lake depth h_L (BLUE), snow dam at the lake outlet, channel with slope φ_b (PURPLE), channel bottom height h_C (RED), ζ (YELLOW). Dam fails; water flows, Q (TEAL), depth of flow D.
**Narration:** Here is our model. A lake of depth h L drains through a channel cut into the ice surface.
**Narration:** We ignore the length of the channel, and assume the discharge is controlled at a single point near the lake, which we call the lake outlet.
**Narration:** The bottom of the channel there sits at a height h C above the lake bed. Drainage begins when a dam of wet snow in the channel fails, and water starts to flow, with discharge Q.
**Visual:** Lake shapes for p_L = 1, 2, 3 (vertical walls, bowl, cone); equation (1) then (2).
**Narration:** The lake's shape is described by a single parameter, p L. A lake with vertical walls has p L equal to one. Bowl shaped lakes have p L between one and three, and a cone has p L of three.
**Narration:** Water conservation then tells us how the lake depth changes: d h L by d t equals the input minus the discharge, divided by the lake's area.

## Bernoulli — From the lake into the channel (≈55 s)

**Visual:** Streamline from still lake water to the outlet. Eqn 3 → 4 → 6. Bernoulli curve (D vs Q) from the model; subcritical and supercritical branches meeting at C.
**Narration:** To find the discharge, we follow the water along a streamline on its surface, from the still body of the lake out into the channel.
**Narration:** Bernoulli's equation says that height plus velocity squared over two g stays the same. So the lake level equals the height of the water in the channel, plus the velocity head.
**Narration:** With discharge equal to velocity times width times depth, this gives the classic curve from open channel hydraulics. It has a subcritical branch and a supercritical branch, which meet at a critical point where the discharge is greatest.

## ForceBalance — Friction and gravity (≈60 s)

**Visual:** Slab of water on slope: τ_F (f_R, LIGHT_BROWN) vs τ_G (φ_b, PURPLE). Eqns 8, 9 → 10. Two force-balance curves on Fig 4, points A and B.
**Narration:** Bernoulli alone doesn't fix the flow. We also balance the forces on the water in the channel.
**Narration:** Friction from the ice, set by the hydraulic roughness f R, balances the pull of gravity along the channel slope, phi b.
**Narration:** That gives a second relationship between discharge and flow depth. Where it crosses the Bernoulli curve, both are satisfied.
**Narration:** For a rough, gently sloping channel, the crossing is on the subcritical branch, at A. For a steep, smooth channel it's supercritical, at B. In that case, we assume the flow passes through the critical point at the outlet, and use the critical flow equations instead.

## Incision — Melting the channel (≈50 s)

**Visual:** Heat from friction (wavy arrows) into the channel bottom; ice melts; h_C decreases. Eqn 11 → 12.
TOWEL: confused, "The water is at zero degrees. Where does the heat come from?"
**Narration:** Finally, the channel itself. We assume the lake is at zero degrees, so the only source of heat is friction in the turbulent flow.
**Narration:** The heat dissipated by that friction melts ice, and we assume it all goes into the channel bottom. So the channel bottom lowers at a rate proportional to the velocity cubed.
**Visual:** five assumptions list, compact.
**Narration:** These assumptions are restrictive, but as we'll see, the model gives useful insight into how drainage works.

## Reduction — Two competing mechanisms (≈70 s)

**Visual:** ζ = h_L − h_C. Eqns 13, 14 → 15 → 16 (α, PINK) and 19 (β, ORANGE). Eqn 22, first term braced "lake level", second "channel incision".
**Narration:** Now the analysis. Define zeta as the height of the lake surface above the bottom of the channel.
**Narration:** Combining Bernoulli and the force balance, the flow velocity squared is proportional to zeta.
**Narration:** So both the channel incision rate and the discharge go like zeta to the power three halves, with coefficients we call alpha and beta.
**Narration:** Putting these into the lake equation reduces the whole model to two ordinary differential equations. And subtracting them tells us how zeta changes.
**Narration:** This equation contains the two competing mechanisms that control drainage. The first term is the lake level changing, because of the imbalance between input and discharge. The second is the channel incising into the ice.

## StabilityParameter — Stable and unstable drainage (≈75 s)

**Visual:** p_L = 1, Q_in = 0 → Eqn 25; bracket becomes Λ (GOLD) (Eqn 26). Feedback loop. Eqn 28; Fig 5 recreated with six lake areas.
**Narration:** Start with the simplest lake: vertical walls, and no input of water. Then d zeta by d t is zeta to the three halves, times alpha minus beta over the lake area.
**Narration:** We call that bracket the drainage stability parameter, Lambda.
**Narration:** If Lambda is positive, zeta grows. The channel incises faster than the lake surface is drawn down. And since discharge increases with zeta, there's a positive feedback, and the discharge grows unboundedly. We call this unstable drainage. The lake always empties.
**Narration:** If Lambda is negative, the lake surface is drawn down faster than the channel incises, so zeta and the discharge decrease. This is stable drainage.
**Narration:** The equation can be solved exactly. Here's the discharge over time for lakes of different areas. Above about six square kilometres, Lambda is positive, and discharge grows. Below, it decays.

## PhysicalControls — What controls stability (≈80 s)

**Visual:** Eqn 29 expanded. Highlight A_Li, φ_b, w; then f_R and ζ0 absent. Build Table 1 row by row.
TOWEL: surprised, "Bigger lakes are less stable?"
**Narration:** So what controls stability? First, the lake area. For a given outflow, the channel incision rate doesn't depend on the lake's area. But the larger the lake, the slower its level drops. So larger lakes encourage unstable drainage.
**Narration:** A steeper channel makes the water flow faster, which speeds up both incision and drawdown. For drawdown this is partly compensated by a shallower flow, so the net effect is to promote unstable drainage.
**Narration:** A wider channel doesn't change the incision rate, but it carries more water for a given velocity, which speeds up drawdown. So wider channels promote stable drainage.
**Narration:** Interestingly, the roughness of the channel doesn't appear in the square brackets, so it doesn't affect stability. A smoother channel speeds the flow, but makes it shallower, and the lower shear stress means less heat for incision. The effects balance.
**Narration:** And the height of the snow dam doesn't appear at all. It sets how fast the lake drains, but not whether drainage is stable.

## StableButComplete — Stopping with water left behind (≈60 s)

**Visual:** h_C–ζ phase space (Fig 6), trajectories from (ζ0, h_Li − ζ0) for five Λ. Eqn 30, Eqn 32.
TOWEL: "Why would drainage stop with water still in the lake?"
**Narration:** During stable drainage, does the lake empty? Let's plot the height of the channel bottom against zeta.
**Narration:** For our simple lake, every trajectory is a straight line, starting from the moment the snow dam fails.
**Narration:** If the line hits the vertical axis, zeta reaches zero. The lake surface has fallen to the channel bottom, the flow stops, and water is left in the lake.
**Narration:** If it hits the horizontal axis first, the channel has cut down to the lake bed, and the lake empties. The dividing line is a critical value, Lambda C. Between Lambda C and zero, drainage is stable, but still complete.

## LakeShape — Lakes that narrow as they drain (≈45 s)

**Visual:** Λ̃ (Eqn 35); area shrinks as h_L falls; Fig 7 trajectories for p_L from 1 to 3 from model.
**Narration:** Real lakes aren't vertically walled. Usually, the fuller a lake is, the larger its area. Then the lake area in the stability parameter is replaced by the current area, which shrinks as the lake drains.
**Narration:** Whether drainage starts stable or unstable doesn't depend on the lake's shape. But as the area shrinks, the lake level falls faster for the same discharge, and catches up with the channel. Drainage always stabilises, and for more cone shaped lakes it halts before the lake is empty.

## LakeInput — Lakes that keep filling (≈55 s)

**Visual:** p_L = 1, Q_in > 0, Eqn 36; ζ relaxing to (−Q_in/A_LiΛ)^(2/3); Eqn 39 Q > Q_in.
TOWEL: confused, "More water in, and it drains completely?"
**Narration:** Finally, a vertically walled lake that receives meltwater. If Lambda is positive, drainage is unstable and the lake empties, as before.
**Narration:** If Lambda is negative, zeta no longer decays to zero. It relaxes to a positive value, because the input keeps the lake surface above the bottom of the channel. So incision continues until the lake is completely empty.
**Narration:** The discharge settles at a value larger than the input. And the larger the input, the faster the lake drains, because a higher input maintains a deeper flow in the channel, which incises faster.

## Simulations — Four simulations (≈75 s)

**Visual:** Side-by-side animated cross-sections with hydrographs: sim 1 (1 km², φ_b 0.01) and sim 2 (3 km², 0.03); then sim 3 (input 5) and sim 4 (p_L = 3).
**Narration:** Now the full model, solved numerically, including critical flow when it occurs. We use a ten metre deep lake, a two metre wide channel, and a one metre snow dam.
**Narration:** In simulation one, a one square kilometre lake with a gently sloping channel drains stably. The discharge starts at two point eight cubic metres per second and falls. After a hundred days the lake has dropped only about a metre, and drainage stops.
**Narration:** In simulation two, a three square kilometre lake with a steeper channel drains unstably. The discharge grows, and after twenty two days the channel has cut down to the lake bed.
**Narration:** In simulation three, the small lake gets a steady input of five cubic metres per second. The discharge rises to about six, and the lake drains stably but completely.
**Narration:** In simulation four, the large lake is cone shaped. Discharge grows for eleven days, peaks, and falls as the shrinking lake stabilises, and drainage ends with water left in the lake.

## Sensitivity — Exploring parameter space (≈55 s)

**Visual:** Fig 10a recreated: final lake depth over A_Li and φ_b from year-long runs, green Λ = 0 curve, Selmes et al. lines at 0.8 and 17 km², crosses for sims 1 and 2. Kink near φ_b ≈ 0.032.
**Narration:** Running the model for a year across many lake areas and channel slopes maps out where lakes empty. The boundary follows the curve where Lambda is zero.
**Narration:** Lakes observed in Greenland average about point eight square kilometres, and reach seventeen. In our model, the average lake drains stably whatever the slope, while the largest lakes drain unstably on all but the gentlest channels.
**Narration:** On slopes steeper than about three percent the flow becomes critical, and the slope stops mattering. And changing the snow dam height changes how fast lakes drain, but never moves the boundary.

## Discussion — Limitations and implications (≈60 s)

**Visual:** Limitations list. Then ice sheet profile: lakes inland, larger area (less stable) but lower slopes (more stable). Nivlisen image again.
**Narration:** The model has important limitations. It ignores variation along the channel, the heat carried by the lake water, changes in channel width, ice flow, and drainage through more than one channel. And it assumes drainage starts with a snow dam, rather than water overtopping the lake's basin.
**Narration:** Still, it has implications. As the climate warms, lakes will form further inland on the Greenland ice sheet. There they tend to be larger, which favours unstable drainage, but channel slopes are lower, which has the opposite effect.
**Narration:** Surface drainage also slows the delivery of lake water to the bed, which can reduce the ice sheet's response.
**Narration:** And on Nivlisen, the most rapid drainage seems to come from some of the largest lakes, where the surface slope is greatest. That is consistent with our theory.

## Conclusions — Conclusions (≈30 s)

**Narration:** To sum up. Surface drainage of a supraglacial lake is a competition between lake drawdown and channel incision, and its stability is set by the sign of Lambda.
**Narration:** Lakes are more prone to drain unstably, and empty completely, when their area, their input and their channel slope are larger. And lakes with an input always drain completely.

## End — Credits (≈10 s)

end_card: Kingslake, J., Ng, F. and Sole, A. (2015). Modelling channelized surface drainage of supraglacial lakes. Journal of Glaciology, 61(225), 185–199. doi.org/10.3189/2015JoG14J158
