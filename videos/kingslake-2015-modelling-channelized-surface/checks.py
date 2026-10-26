"""Symbolic and numerical checks of every derivation used in the video.

Run: ../../.venv/bin/python checks.py   (prints OK lines; raises on any failure)
"""

import sympy as sp

from model import G, L_F, RHO_I, RHO_W, SIM1, SIM2, SIM3, Lake, simulate

g, w, phi, fR, rw, ri, Lf, A, zeta, v, D, Q, Qin, t, z0, hLi, hL, p, VLi = sp.symbols(
    "g w phi_b f_R rho_w rho_i L A_Li zeta v D Q Q_in t zeta_0 h_Li h_L p_L V_Li", positive=True
)
Lam = sp.symbols("Lambda", real=True)


def ok(name, expr):
    assert sp.simplify(expr) == 0, f"{name}: {sp.simplify(expr)}"
    print(f"OK  {name}")


# Bernoulli at the outlet (Eqn 6, with Q = v w D) and force balance tau_F = tau_G (Eqns 8-9)
bernoulli = sp.Eq(zeta, D + v**2 / (2 * g))
force = sp.Eq(fR * rw * v**2 / 8, rw * g * D * phi)

# Eqn (10): Q = sqrt(8 g phi / f_R) w D^(3/2)
v_force = sp.solve(force, v)[0]
ok("Eqn 10 discharge from force balance", v_force * w * D - sp.sqrt(8 * g * phi / fR) * w * D**sp.Rational(3, 2))

# Eqn (15): v^2 = zeta 2g / (1 + f_R / (4 phi))
D_force = sp.solve(force, D)[0]
v2_expr = sp.solve(sp.Eq(zeta, D_force + v**2 / (2 * g)), v)[0] ** 2
ok("Eqn 15 velocity", v2_expr - zeta * 2 * g / (1 + fR / (4 * phi)))

# Eqns (16)-(17): dh_C/dt = -f_R rho_w v^3/(8 L rho_i) = -alpha zeta^(3/2)
alpha = fR * rw / (8 * Lf * ri) * (2 * g / (1 + fR / (4 * phi))) ** sp.Rational(3, 2)
ok("Eqn 16-17 incision", fR * rw / (8 * Lf * ri) * v2_expr ** sp.Rational(3, 2) - alpha * zeta ** sp.Rational(3, 2))

# Eqns (18)-(20): Q = v w D with D from force balance = beta zeta^(3/2)
beta = (2 * g / (1 + fR / (4 * phi))) ** sp.Rational(3, 2) * w * fR / (8 * g * phi)
Q_expr = (v * w * D_force).subs(v, sp.sqrt(v2_expr))
ok("Eqn 19-20 discharge", Q_expr - beta * zeta ** sp.Rational(3, 2))

# The incision is the frictional heat: tau_F v / (rho_i L) with tau_F = rho_w g D phi
ok(
    "incision = gravitational power / latent heat",
    (fR * rw * v**2 / 8 * v / (ri * Lf)).subs(v, sp.sqrt(v2_expr))
    - (rw * g * phi * (Q_expr / w) / (ri * Lf)),
)

# Consistency check for Eqn 29 (see analysis.md section 13, notes beyond the paper): the
# ratio of incision to drawdown rate is independent of discharge and roughness.
incision = rw * g * phi * Q / (w * ri * Lf)
drawdown = Q / A
ratio = sp.simplify(incision / drawdown)
ok("rate ratio = rho_w g phi A / (rho_i L w)", ratio - rw * g * phi * A / (ri * Lf * w))
ok("alpha/beta*A equals the same ratio", alpha * A / beta - ratio)

# Eqn (29): Lambda = alpha (1 - (rho_i L / rho_w g) w / (A phi))
Lambda = alpha - beta / A
ok("Eqn 29 expansion", Lambda - alpha * (1 - (ri * Lf / (rw * g)) * w / (A * phi)))
A_crit = ri * Lf / (rw * g) * w / phi
ok("critical area makes Lambda vanish", Lambda.subs(A, A_crit))

# Eqns (27)-(28): zeta(t) solves d zeta/dt = Lambda zeta^(3/2), zeta(0) = zeta_0
zeta_t = 1 / (1 / sp.sqrt(z0) - Lam * t / 2) ** 2
# before blow-up the bracket is positive, so zeta^(3/2) = bracket^-3
ok("Eqn 27 solves Eqn 25", sp.diff(zeta_t, t) - Lam / (1 / sp.sqrt(z0) - Lam * t / 2) ** 3)
assert sp.simplify(zeta_t.subs(t, 0) - z0) == 0
print("OK  Eqn 27 initial condition")
b = sp.symbols("beta", positive=True)
s_ = sp.symbols("s", positive=True)  # the bracket 1/sqrt(zeta_0) - Lambda t / 2
ok("Eqn 28 discharge", b * (1 / s_**2) ** sp.Rational(3, 2) - b / s_**3)

# Eqns (30)-(32): phase-plane slope, final channel height, critical Lambda
al = sp.symbols("alpha", positive=True)
slope = (-al * zeta ** sp.Rational(3, 2)) / (Lam * zeta ** sp.Rational(3, 2))
ok("Eqn 30 phase slope", slope + al / Lam)
h_final = (hLi - z0) + (-al / Lam) * (0 - z0)
ok("Eqn 31 final height", h_final - ((hLi - z0) + z0 * al / Lam))
Lam_C = sp.solve(sp.Eq(h_final, 0), Lam)[0]
ok("Eqn 32 critical Lambda", Lam_C + al / (hLi / z0 - 1))

# Eqns (36)-(39): input Q_in > 0, vertical walls, Lambda < 0: zeta relaxes to a fixed point
bb = sp.symbols("beta", positive=True)
Lneg = sp.symbols("Lambda_neg", negative=True)
zstar = (-Qin / (A * Lneg)) ** sp.Rational(2, 3)
ok("Eqn 36 fixed point", Qin / A + Lneg * zstar ** sp.Rational(3, 2))
Qstar = bb * zstar ** sp.Rational(3, 2)
ok("Eqn 38", Qstar + bb * Qin / (A * Lneg))
ok("Eqn 39", (Qstar - Qin / (1 - al * A / bb)).subs(Lneg, al - bb / A))

# Eqn (1)-(2): hypsometry gives A_L = dV/dh = A_Li (h/h_Li)^(p_L-1) with A_Li = p_L V_Li/h_Li
V = VLi * (hL / hLi) ** p
ok("hypsometry area", sp.diff(V, hL) - (p * VLi / hLi) * (hL / hLi) ** (p - 1))

# Critical flow (Eqn 7) and the Froude number of the subcritical solution
Dsym = sp.symbols("D", positive=True)
Qb = sp.sqrt(2 * g * (zeta - Dsym)) * w * Dsym  # Bernoulli curve, Eqn (6)
Dc = sp.solve(sp.diff(Qb, Dsym), Dsym)[0]
ok("Eqn 7 critical depth", Dc - 2 * zeta / 3)
ok("Eqn 7 critical discharge", Qb.subs(Dsym, Dc) - sp.sqrt(g * w**2 * Dc**3))
Fr2 = v2_expr / (g * D_force.subs(v, sp.sqrt(v2_expr)))
ok("Froude^2 = 8 phi / f_R", Fr2 - 8 * phi / fR)

# ------------------------------------------------------------------ numbers in the paper
print()
print(f"rho_i L / (rho_w g) = {RHO_I * L_F / (RHO_W * G) / 1e3:.1f} km   (L/g = {L_F / G / 1e3:.1f} km)")
for name, lake, paper in [
    ("sim1", SIM1, dict(Lambda=-2.4e-6, Lambda_C=-5.1e-8, Q0=2.8)),
    ("sim2", SIM2, dict(Lambda=5.3e-7, Q0=3.4)),
]:
    Q0 = lake.beta * lake.zeta0**1.5
    print(f"{name}: Lambda {lake.Lambda:.2e} (paper {paper['Lambda']:.1e}), Q0 {Q0:.2f} (paper {paper['Q0']})", end="")
    if "Lambda_C" in paper:
        print(f", Lambda_C {lake.Lambda_C:.2e} (paper {paper['Lambda_C']:.1e})", end="")
    print()
print(f"sim3 Q* = {SIM3.Q_in / (1 - SIM3.A_Li / SIM3.A_crit):.2f} m3/s (paper 5.97)")
print(f"Fig 5 legend: A_c = {Lake(phi_b=0.01).A_crit / 1e6:.2f} km2 (paper: Lambda = 0 at 6.2 km2)")
for A_km2, paper in [(15, 2.7e-7), (8, 1e-7), (4, -2e-7), (2, -9e-7), (0.5, -5e-6)]:
    print(f"   A={A_km2:>4} km2  Lambda={Lake(A_Li=A_km2 * 1e6).Lambda:.1e}  (paper {paper:.0e})")
print(f"subcritical while phi_b < f_R/8 = {0.25 / 8:.4f} (paper: kink at phi_b ~ 0.032)")
print(f"Selmes max lake 17 km2 unstable for phi_b > {RHO_I * L_F / (RHO_W * G) * 2 / 17e6:.4f} (paper: 0.003)")
r2 = simulate(SIM2, days=40)
import numpy as np

i0 = np.argmax(r2.h_C <= 0)
print(f"sim2: channel reaches lake bed after {r2.t[i0]:.1f} days (paper: 22 days); Q then {r2.Q[i0]:.1f} m3/s")
for rho_i, gg in [(900, 9.8), (917, 9.8), (910, 9.81), (917, 9.81)]:
    al_ = 0.25 * 1000 / (8 * 334e3 * rho_i) * (2 * gg / (1 + 0.25 / 0.12)) ** 1.5
    Ac = rho_i * 334e3 / (1000 * gg) * 2 / 0.03
    print(f"   sim2 Lambda with rho_i={rho_i}, g={gg}: {al_ * (1 - Ac / 3e6):.2e}")
