"""
data.py — Deliverable basket specification, default market parameters, and
          synthetic time-series generators for the Treasury Basis Explorer.

All data is hypothetical/synthetic and representative of a Jun-2026 10-Year
T-Note futures contract with yields in the 4.28–4.35% range.
"""
import numpy as np
import pandas as pd
from analytics import (
    bprice, conv_factor, accrued_interest,
    carry_decomp, gross_basis, implied_repo, dv01, mod_duration, dollar_convexity,
)

# ─────────────────────────────────────────────────────────────────────────────
# MARKET DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
DEF_REPO  = 4.30     # repo rate (%)
DEF_DAYS  = 79       # days to Jun-30-2026 delivery
AI_SETTLE = 1.20     # approximate accrued interest at settlement ($)
NOTIONAL  = 100_000  # contract face value ($)

# ─────────────────────────────────────────────────────────────────────────────
# DELIVERABLE BASKET SPECIFICATION
# Representative Jun-2026 10yr T-Note futures basket (CME eligibility:
# 6½–10 years remaining maturity at first delivery day → n = 13–20 periods).
#
# The wide coupon range (1.75–6.5%) reflects the full spectrum of bonds
# issued across rate cycles (2020 low-rate era through 2023 high-rate era).
# This breadth directly reproduces the call/put/straddle basis option profiles
# from Burghardt et al. Chapter 2 (Exhibits 2.7, 2.8).
#
# format: (label, coupon%, semi-annual-periods, base-YTM%)
# ─────────────────────────────────────────────────────────────────────────────
BASKET_SPEC = [
    # Low-coupon / high-duration cluster (2020-2021 era issuance, n=14-20)
    # CF << 1 → CTD candidates when yields fall toward 3%
    ("1.750% Nov-33",  1.750, 15, 4.30),   # 7.5yr — lowest coupon, highest DV01
    ("2.250% Feb-34",  2.250, 16, 4.30),   # 8yr
    ("2.875% Aug-33",  2.875, 15, 4.30),   # 7.5yr
    # Mid-coupon cluster (2022 era, near CTD zone at current 4.3% yields)
    ("3.500% Feb-33",  3.500, 14, 4.29),   # 7yr
    ("4.000% Nov-32",  4.000, 13, 4.28),   # 6.5yr — CTD at current rates
    ("4.250% Feb-34",  4.250, 16, 4.31),   # 8yr
    # High-coupon / lower-duration cluster (2023-2024 era, CF ≈ 1 or > 1)
    # CTD candidates when yields rise above 5%
    ("4.750% Aug-34",  4.750, 17, 4.32),   # 8.5yr
    ("5.000% Feb-35",  5.000, 18, 4.33),   # 9yr
    ("5.500% Aug-35",  5.500, 19, 4.34),   # 9.5yr
    ("6.500% Feb-36",  6.500, 20, 4.35),   # 10yr — highest coupon, lowest DV01/CF
]

# ─────────────────────────────────────────────────────────────────────────────
# BOOK OPTION-PROFILE ILLUSTRATION BONDS  (Burghardt et al. Ch.2 Exhibits 2.7, 2.8)
# Three bonds spanning the full duration spectrum to demonstrate call/put/straddle
# basis profiles — directly analogous to the 5½%, 7⅝%, 8⅞% T-bond examples
# in the book (adapted here for 10yr T-note futures with 6% CF reference rate).
#
# These are members of the basket above; we reference them by coupon/n/ytm so the
# option-profile chart uses identical pricing to the basket table.
# ─────────────────────────────────────────────────────────────────────────────
OPTION_PROFILE_BONDS = [
    # (label, coupon%, n_periods, base_ytm%, profile_type)
    #
    # Analog of book's 5½% T-bond (Exhibit 2.7):
    # Low coupon, high duration bond.  DV01/CF >> Futures DV01
    # → basis WIDENS as yields fall (like a call on futures)
    ("1.750% Nov-33  (Low-Coupon / High-Duration)",  1.750, 15, 4.30, "call"),
    #
    # Analog of book's 7⅝% T-bond (Straddle exhibit):
    # Current CTD.  DV01/CF = Futures DV01 (by definition)
    # → basis U-shaped, minimal at current yield (straddle payoff)
    ("4.000% Nov-32  (Medium-Coupon — Current CTD)", 4.000, 13, 4.28, "straddle"),
    #
    # Analog of book's 8⅞% T-bond (Exhibit 2.8):
    # High coupon, SAME SHORT maturity as CTD (n=13).  DV01/CF < Futures DV01
    # → basis WIDENS as yields rise (like a put on futures)
    # NOTE: A bond with the SAME maturity but HIGHER coupon has lower modified
    # duration, reducing DV01/CF below the CTD's ratio — the put-option condition.
    ("6.500% Nov-32  (High-Coupon / Same Maturity)",  6.500, 13, 4.30, "put"),
]


# ─────────────────────────────────────────────────────────────────────────────
# FAIR FUTURES PRICE (derived from basket)
# ─────────────────────────────────────────────────────────────────────────────
def fair_futures(repo_pct: float = DEF_REPO, days: int = DEF_DAYS,
                 opt_32nds: float = 6.0) -> float:
    """Compute the fair (market) futures price from the deliverable basket.

    Theoretical no-option futures = min_i[ fwd_clean_i / CF_i ].
    The market futures trades BELOW this (delivery options have value to the short).
    We subtract opt_32nds/32 / CF_ctd as the delivery option premium, so the CTD
    has a net basis ≈ opt_32nds (representing embedded option value).

    Parameters
    ----------
    repo_pct  : repo rate in percent (e.g. 4.30)
    days      : days to delivery
    opt_32nds : assumed delivery option premium in 32nds (default 6)
    """
    repo = repo_pct / 100
    candidates = []
    for _, c, n, ytm0 in BASKET_SPEC:
        ytm  = ytm0 / 100
        px   = bprice(c, ytm, n)
        cfv  = conv_factor(c, n)
        fp   = px + AI_SETTLE
        ci   = c * days / 365
        fc   = fp * repo * days / 360
        fwd_clean = px + fc - ci          # forward clean price
        candidates.append((fwd_clean / cfv, cfv))
    min_theo, min_cf = min(candidates, key=lambda x: x[0])
    # Subtract delivery-option premium so CTD has net basis ≈ opt_32nds
    return round(min_theo - (opt_32nds / 32) / min_cf, 3)


DEF_FUT = fair_futures()   # ≈ 110.0 at base parameters


# ─────────────────────────────────────────────────────────────────────────────
# BASKET BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_basket(fut_price: float = DEF_FUT, repo_pct: float = DEF_REPO,
                 days: int = DEF_DAYS, shift_bp: float = 0.0) -> pd.DataFrame:
    """Build deliverable basket DataFrame with full analytics.

    Parameters
    ----------
    fut_price : futures price
    repo_pct  : repo rate in percent
    days      : days to delivery
    shift_bp  : parallel yield curve shift in basis points
    """
    repo = repo_pct / 100
    rows = []
    for label, c, n, ytm0 in BASKET_SPEC:
        ytm   = (ytm0 + shift_bp / 100) / 100
        px    = bprice(c, ytm, n)
        cfv   = conv_factor(c, n)
        ai_s  = AI_SETTLE
        ai_d  = ai_s + accrued_interest(c, days)
        fp    = px + ai_s
        gb    = gross_basis(px, fut_price, cfv)
        car, ci, fc = carry_decomp(fp, c, repo, days)
        nb    = gb - car
        ir    = implied_repo(fp, fut_price, cfv, c, ai_d, days)
        dv    = dv01(c, ytm, n)
        md    = mod_duration(c, ytm, n)
        dc    = dollar_convexity(c, ytm, n)
        rows.append(dict(
            Bond=label, Coupon=c, Periods=n,
            CleanPx=round(px, 4),
            YTM=round(ytm * 100, 3),
            CF=cfv,
            CFxFut=round(cfv * fut_price, 4),
            GrossBasis32=round(gb * 32, 3),
            Carry32=round(car * 32, 3),
            NetBasis32=round(nb * 32, 3),
            ImplRepo=round(ir * 100, 3),
            DV01=round(dv, 4),
            ModDur=round(md, 3),
            DolConv=round(dc, 2),
            CouponIncome32=round(ci * 32, 3),
            FinancingCost32=round(fc * 32, 3),
            # raw floats used by callbacks
            _gb=gb, _nb=nb, _car=car, _ir=ir, _fp=fp, _c=c, _ytm=ytm, _dv=dv,
        ))
    df = pd.DataFrame(rows)
    df["CTD"] = df["ImplRepo"] == df["ImplRepo"].max()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC TIME-SERIES GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
_rng = np.random.default_rng(42)


def gen_basis_history(n_days: int = 90) -> pd.DataFrame:
    """Simulate basis convergence as delivery approaches (90 → 1 days left)."""
    days_left = np.arange(n_days, 0, -1)
    ytm_path  = 4.30 + np.cumsum(_rng.normal(0, 0.008, n_days))
    ytm_path  = np.clip(ytm_path, 1.0, 9.0)
    fut_base  = DEF_FUT + np.cumsum(_rng.normal(0, 0.025, n_days))
    fut_base  = np.clip(fut_base, 95.0, 130.0)

    c, n_per = 4.000, 13          # CTD bond: 4.000% Nov-32
    repo     = DEF_REPO / 100
    gross_b, carry_b, net_b, prices = [], [], [], []

    for d, ytm, fut in zip(days_left, ytm_path / 100, fut_base):
        px  = bprice(c, ytm, n_per)
        cfv = conv_factor(c, n_per)
        fp  = px + AI_SETTLE
        gb  = gross_basis(px, fut, cfv)
        car, _, _ = carry_decomp(fp, c, repo, float(d))
        gross_b.append(gb * 32)
        carry_b.append(car * 32)
        net_b.append((gb - car) * 32)
        prices.append(px)

    idx = pd.date_range("2026-01-01", periods=n_days, freq="B")
    return pd.DataFrame({
        "DaysLeft":     days_left,
        "YTM":          ytm_path,
        "CashPrice":    prices,
        "FuturesPrice": fut_base,
        "GrossBasis":   gross_b,
        "Carry":        carry_b,
        "NetBasis":     net_b,
    }, index=idx)


def gen_yield_curve() -> pd.DataFrame:
    """Representative Treasury yield curve (Apr-2026 hypothetical)."""
    tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]
    yields = [5.30, 5.25, 5.10, 4.80, 4.60, 4.45, 4.40, 4.35, 4.55, 4.65]
    return pd.DataFrame({"Tenor": tenors, "Yield": yields})


def gen_repo_history(n: int = 252) -> pd.DataFrame:
    """Simulate one year of daily repo (SOFR-proxy) rates."""
    dates = pd.date_range("2025-04-01", periods=n, freq="B")
    path  = 5.30 + np.cumsum(_rng.normal(0, 0.012, n))
    return pd.DataFrame({"Date": dates, "Repo": np.clip(path, 3.5, 6.5)})


def gen_ctd_switch(ytm_range: tuple = (-200, 200), n: int = 81) -> pd.DataFrame:
    """Identify CTD bond across a range of parallel yield shifts."""
    shifts = np.linspace(ytm_range[0], ytm_range[1], n)
    rows   = []
    for sh in shifts:
        df  = build_basket(shift_bp=sh)
        ctd = df.loc[df["ImplRepo"].idxmax()]
        rows.append({"Shift": sh, "CTD": ctd["Bond"],
                     "ImplRepo": ctd["ImplRepo"], "NetBasis": ctd["NetBasis32"]})
    return pd.DataFrame(rows)


def gen_option_value(n: int = 81) -> pd.DataFrame:
    """Approximate quality-option value vs yield shift.
    Option value ≈ max(0, excess net basis created by the futures being below
    the theoretical no-option price) captured by the cheapest basket spread.
    """
    shifts   = np.linspace(-200, 200, n)
    rows     = []
    for sh in shifts:
        df  = build_basket(shift_bp=sh)
        # Quality option ≈ spread between CTD net basis and second-cheapest bond
        sorted_nb = df["NetBasis32"].sort_values()
        opt_val   = max(0.0, sorted_nb.iloc[1] - sorted_nb.iloc[0])
        rows.append({"Shift": sh,
                     "OptionValue":  opt_val,
                     "CTDNetBasis":  df.loc[df["CTD"], "NetBasis32"].values[0],
                     "GrossBasis":   df.loc[df["CTD"], "GrossBasis32"].values[0]})
    return pd.DataFrame(rows)


# ─── Pre-compute expensive series at import time ─────────────────────────────
HIST       = gen_basis_history()
YLD_CURVE  = gen_yield_curve()
REPO_HIST  = gen_repo_history()
CTD_SWITCH = gen_ctd_switch()
OPT_VALUE  = gen_option_value()
