"""Kingslake, Ng & Sole (2015): channelized surface drainage of a supraglacial lake.

A lake of depth h_L drains through a channel whose floor sits at height h_C above the lake
bed. zeta = h_L - h_C is the lake surface's height above the channel floor (the head
that drives the flow). Two things change zeta:

  * the lake surface falls as water leaves:    dh_L/dt = (Q_in - Q) / A_L(h_L)
  * the channel floor melts down by friction:  dh_C/dt = -(f_R rho_w / (8 L rho_i)) v^3

Everything the video animates is computed here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp

G = 9.8  # m s^-2
L_F = 334e3  # latent heat of fusion, J kg^-1
RHO_W = 1000.0  # kg m^-3
RHO_I = 900.0  # kg m^-3; not stated in the paper, this value reproduces all its quoted numbers
DAY = 86400.0


@dataclass(frozen=True)
class Lake:
    A_Li: float = 1e6  # initial (reference) lake area, m^2
    h_Li: float = 10.0  # initial (reference) lake depth, m
    p_L: float = 1.0  # hypsometry: 1 vertical walls, 3 cone
    Q_in: float = 0.0  # meltwater input, m^3 s^-1
    w: float = 2.0  # channel width, m
    phi_b: float = 0.01  # channel slope
    f_R: float = 0.25  # Darcy-Weisbach roughness
    zeta0: float = 1.0  # snow-dam height = initial head, m

    # ---- subcritical outlet hydraulics (Bernoulli + force balance)
    @property
    def velocity_factor(self) -> float:
        """v^2 = zeta * this  (Eqn 15)."""
        return 2 * G / (1 + self.f_R / (4 * self.phi_b))

    @property
    def alpha(self) -> float:
        """Incision: dh_C/dt = -alpha zeta^(3/2)  (Eqn 17)."""
        return self.f_R * RHO_W / (8 * L_F * RHO_I) * self.velocity_factor**1.5

    @property
    def beta(self) -> float:
        """Discharge: Q = beta zeta^(3/2)  (Eqn 20)."""
        return self.velocity_factor**1.5 * self.w * self.f_R / (8 * G * self.phi_b)

    @property
    def Lambda(self) -> float:
        """Drainage stability parameter  (Eqn 26)."""
        return self.alpha - self.beta / self.A_Li

    @property
    def A_crit(self) -> float:
        """Lake area at which Lambda = 0: (rho_i L / rho_w g) * (w / phi_b)  (Eqn 29)."""
        return RHO_I * L_F / (RHO_W * G) * self.w / self.phi_b

    @property
    def Lambda_C(self) -> float:
        """Most negative Lambda that still empties a vertical-walled lake  (Eqn 32)."""
        return -self.alpha / (self.h_Li / self.zeta0 - 1)

    @property
    def froude_sq(self) -> float:
        """Fr^2 = 8 phi_b / f_R in the subcritical solution: critical when phi_b > f_R/8."""
        return 8 * self.phi_b / self.f_R

    # ---- full model (with the critical-flow switch)
    def outlet(self, zeta: float) -> tuple[float, float, float]:
        """(Q, v, D) at the lake outlet for head zeta."""
        zeta = max(zeta, 0.0)
        if self.froude_sq <= 1:  # subcritical: Eqns (15), (19)
            v = np.sqrt(self.velocity_factor * zeta)
            Q = self.beta * zeta**1.5
            D = Q / (v * self.w) if v > 0 else 0.0
        else:  # supercritical solution -> control by critical flow, Eqn (7)
            D = 2 * zeta / 3
            v = np.sqrt(G * D)
            Q = np.sqrt(G * self.w**2 * D**3)
        return Q, v, D

    def area(self, h_L: float) -> float:
        return self.A_Li * (max(h_L, 1e-9) / self.h_Li) ** (self.p_L - 1)

    def rhs(self, t, y):
        h_L, h_C = y
        Q, v, _ = self.outlet(h_L - h_C)
        dhL = (self.Q_in - Q) / self.area(h_L)
        dhC = -self.f_R * RHO_W / (8 * L_F * RHO_I) * v**3
        return [dhL, dhC]


@dataclass
class Run:
    t: np.ndarray  # days
    h_L: np.ndarray
    h_C: np.ndarray
    Q: np.ndarray
    emptied: bool


def simulate(lake: Lake, days: float = 365, n: int = 2000) -> Run:
    """Start with a full lake whose channel floor is zeta0 below its surface (the snow dam
    has just failed). Stop when the lake empties or the discharge falls below 0.002 m^3/s."""

    def empty(t, y):
        return y[0]

    def trickle(t, y):
        return lake.outlet(y[0] - y[1])[0] - 0.002

    empty.terminal = trickle.terminal = True
    empty.direction = trickle.direction = -1
    sol = solve_ivp(
        lake.rhs,
        (0, days * DAY),
        [lake.h_Li, lake.h_Li - lake.zeta0],
        events=[empty, trickle],
        max_step=DAY / 8,
        rtol=1e-8,
        atol=1e-10,
        dense_output=True,
    )
    t = np.linspace(0, sol.t[-1], n)
    h_L, h_C = sol.sol(t)
    Q = np.array([lake.outlet(a - b)[0] for a, b in zip(h_L, h_C)])
    return Run(t / DAY, h_L, h_C, Q, emptied=bool(len(sol.t_events[0])))


def analytic_Q(lake: Lake, t_days: np.ndarray) -> np.ndarray:
    """Eqn (28): vertical walls, no input. Blows up at t_b = 2 / (Lambda sqrt(zeta0))."""
    t = np.asarray(t_days) * DAY
    denom = 1 / np.sqrt(lake.zeta0) - lake.Lambda * t / 2
    return np.where(denom > 0, lake.beta / np.maximum(denom, 1e-12) ** 3, np.inf)


def phase_line(lake: Lake, zeta: np.ndarray) -> np.ndarray:
    """h_C as a function of zeta for a vertical-walled lake: a straight line of slope
    -alpha/Lambda through (zeta0, h_Li - zeta0)  (Eqn 30)."""
    return lake.h_Li - lake.zeta0 - lake.alpha / lake.Lambda * (zeta - lake.zeta0)


def h_final(lake: Lake) -> float:
    """Eqn (31)."""
    return (lake.h_Li - lake.zeta0) + lake.zeta0 * lake.alpha / lake.Lambda


def bernoulli_Q(D: np.ndarray, zeta: float, w: float) -> np.ndarray:
    """Eqn (6) solved for Q: the Bernoulli curve of Fig 4."""
    return w * D * np.sqrt(np.maximum(2 * G * (zeta - D), 0))


def force_balance_Q(D: np.ndarray, phi_b: float, f_R: float, w: float) -> np.ndarray:
    """Eqn (10): the force-balance curves of Fig 4."""
    return np.sqrt(8 * G * phi_b / f_R) * w * D**1.5


def trajectory(lake: Lake, days: float = 365) -> tuple[np.ndarray, np.ndarray]:
    """(zeta, h_C) along a simulated drainage path: the h_C-zeta phase space of Figs 6-7."""
    r = simulate(lake, days=days)
    return r.h_L - r.h_C, r.h_C


def _final_depth(args):
    A, phi = args
    r = simulate(Lake(A_Li=A, phi_b=phi), days=365, n=50)
    return 0.0 if r.emptied else max(float(r.h_L[-1]), 0.0)


def final_depth_map(cache: str = "assets/fig10a.npz"):
    """Fig 10a: final lake depth after year-long runs over initial area and channel slope
    (Q_in = 0, w = 2 m, p_L = 1, zeta0 = 1 m). Cached, since it takes a minute or two."""
    from multiprocessing import Pool
    from pathlib import Path

    path = Path(__file__).parent / cache
    if path.exists():
        d = np.load(path)
        return d["areas"], d["slopes"], d["h_final"]
    areas = np.linspace(0.05e6, 19e6, 48)
    slopes = np.linspace(0.004, 0.046, 36)
    jobs = [(A, phi) for phi in slopes for A in areas]
    with Pool() as pool:
        h = np.array(pool.map(_final_depth, jobs)).reshape(len(slopes), len(areas))
    path.parent.mkdir(exist_ok=True)
    np.savez(path, areas=areas, slopes=slopes, h_final=h)
    return areas, slopes, h


# The paper's four simulations (Section 5.1)
SIM1 = Lake(A_Li=1e6, phi_b=0.01)  # stable, stalls
SIM2 = Lake(A_Li=3e6, phi_b=0.03)  # unstable, empties
SIM3 = replace(SIM1, Q_in=5.0)  # stable but complete, thanks to input
SIM4 = replace(SIM2, p_L=3.0)  # unstable, then stabilised by shrinking area
FIG7 = Lake(A_Li=4.6e6, phi_b=0.03)  # Fig 7 (parameters not given): three highest p_L halt


if __name__ == "__main__":
    import time

    t0 = time.time()
    areas, slopes, h = final_depth_map()
    print(f"Fig 10a map {h.shape} in {time.time() - t0:.0f}s; emptied fraction {np.mean(h == 0):.2f}")
    for p in np.linspace(1, 3, 11):
        z, hc = trajectory(replace(SIM2, p_L=p))
        print(f"  p_L={p:.1f}: ends zeta={z[-1]:.2f} h_C={hc[-1]:.2f}")
    for name, lake in [("sim1", SIM1), ("sim2", SIM2), ("sim3", SIM3), ("sim4", SIM4)]:
        r = simulate(lake, days=120)
        print(
            f"{name}: Lambda={lake.Lambda:.2e}  Lambda_C={lake.Lambda_C:.2e}  A_c={lake.A_crit / 1e6:.2f} km2  "
            f"Q0={r.Q[0]:.2f}  Qmax={r.Q.max():.2f} at t={r.t[r.Q.argmax()]:.1f} d  "
            f"end t={r.t[-1]:.1f} d  h_L end={r.h_L[-1]:.2f}  h_C end={r.h_C[-1]:.2f}  emptied={r.emptied}"
        )
