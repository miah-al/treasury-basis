"""
analytics.py — Bond mathematics: pricing, carry, basis, implied repo, risk
All functions use real (not percentage) yields unless stated otherwise.
Coupons are in dollars per $100 (or $1) face; n_periods = semi-annual count.
"""
import numpy as np


# ─── Bond Pricing ─────────────────────────────────────────────────────────────

def bprice(coupon, ytm, n_periods, face=100.0):
    """Semi-annual bond price.

    Parameters
    ----------
    coupon    : annual coupon payment in same units as face (e.g. 4.125 for $4.125/yr)
    ytm       : annual yield (decimal, e.g. 0.0435)
    n_periods : number of semi-annual periods remaining
    face      : face / par value
    """
    c2, y2 = coupon / 2, ytm / 2
    if n_periods <= 0:
        return face
    if abs(y2) < 1e-12:
        return c2 * n_periods + face
    pv_c = c2 * (1 - (1 + y2) ** -n_periods) / y2
    pv_f = face * (1 + y2) ** -n_periods
    return pv_c + pv_f


def ytm_solve(price, coupon, n_periods, face=100.0):
    """Newton-Raphson YTM solver (returns decimal yield)."""
    y = coupon / max(price, 1)
    for _ in range(80):
        c2, y2 = coupon / 2, y / 2
        p  = bprice(coupon, y, n_periods, face)
        dp = sum(-(i * c2) * 0.5 / (1 + y2) ** (i + 1) for i in range(1, n_periods + 1))
        dp += -n_periods * face * 0.5 / (1 + y2) ** (n_periods + 1)
        delta = (p - price) / (dp + 1e-15)
        y -= delta
        if abs(delta) < 1e-10:
            break
    return max(y, -0.5)


# ─── CME/CBOT Conversion Factor ───────────────────────────────────────────────

def conv_factor(coupon_pct, n_periods, ref_rate=0.06):
    """CME conversion factor: price at 6% yield per $1 face.

    coupon_pct : coupon in percent, e.g. 4.125
    n_periods  : semi-annual periods remaining at delivery (rounded to nearest 3 months)
    """
    return round(bprice(coupon_pct / 100, ref_rate, n_periods, 1.0), 4)


# ─── Accrued Interest ─────────────────────────────────────────────────────────

def accrued_interest(coupon_pct, days_since_coupon, days_in_period=182.5):
    """Act/Act accrued interest (simplified, assumes equal coupon periods).

    coupon_pct : annual coupon in percent (e.g. 4.125)
    """
    return (coupon_pct / 2) * (days_since_coupon / days_in_period)


# ─── Carry ────────────────────────────────────────────────────────────────────

def carry_decomp(full_price, coupon_pct, repo_rate, days):
    """Carry decomposition: (total, coupon_income, financing_cost) per $100 face.

    full_price  : full (dirty) cash price
    coupon_pct  : annual coupon in percent
    repo_rate   : annualised repo rate (decimal, e.g. 0.043)
    days        : days to delivery
    """
    ci = coupon_pct * days / 365          # coupon income (Act/365)
    fc = full_price * repo_rate * days / 360  # financing cost (Act/360)
    return ci - fc, ci, fc


# ─── Basis ────────────────────────────────────────────────────────────────────

def gross_basis(clean_price, futures_price, cf_val):
    """Gross basis = clean cash price − CF × futures price (dollars per $100)."""
    return clean_price - cf_val * futures_price


def net_basis(gb, carry):
    """Net basis = gross basis − carry."""
    return gb - carry


# ─── Implied Repo ─────────────────────────────────────────────────────────────

def implied_repo(full_price, futures_price, cf_val, coupon_pct, ai_delivery, days):
    """Implied repo rate (annualised, Act/360).

    Returns the financing rate that makes the delivery trade break even:
        full_price × (1 + r × d/360) = CF × futures + AI_del + coupon_income

    Higher implied repo → cheaper to deliver (CTD has the highest value).
    """
    invoice = cf_val * futures_price + ai_delivery
    ci = coupon_pct * days / 365
    if full_price <= 0 or days <= 0:
        return 0.0
    return (invoice + ci - full_price) / (full_price * days / 360)


# ─── Risk Measures ────────────────────────────────────────────────────────────

def dv01(coupon_pct, ytm, n_periods, face=100.0):
    """Dollar value of 1bp (0.01%) decline in yield per $100 face."""
    return (bprice(coupon_pct, ytm - 1e-4, n_periods, face) -
            bprice(coupon_pct, ytm + 1e-4, n_periods, face)) / 2


def dollar_convexity(coupon_pct, ytm, n_periods, face=100.0):
    """Dollar convexity (second-order price sensitivity) per $100 face."""
    p  = bprice(coupon_pct, ytm, n_periods, face)
    pu = bprice(coupon_pct, ytm + 1e-4, n_periods, face)
    pd = bprice(coupon_pct, ytm - 1e-4, n_periods, face)
    return (pu + pd - 2 * p) / (1e-4 ** 2)


def mod_duration(coupon_pct, ytm, n_periods, face=100.0):
    """Modified duration (years)."""
    p = bprice(coupon_pct, ytm, n_periods, face)
    return dv01(coupon_pct, ytm, n_periods, face) * 1e4 / p


def forward_clean_price(full_price, coupon_pct, repo_rate, days, ai_delivery):
    """Theoretical forward clean price (invoice price minus AI at delivery)."""
    ci = coupon_pct * days / 365
    fwd_full = full_price * (1 + repo_rate * days / 360) - ci
    return fwd_full - ai_delivery
