"""
callbacks.py — All Dash callbacks for the Treasury Basis Explorer.
Call register_callbacks(app) from app.py to bind all callbacks to the app.
"""
import numpy as np
from dash import Input, Output

from analytics import bprice, conv_factor, carry_decomp, dv01
from data import (
    build_basket, BASKET_SPEC, DEF_FUT, DEF_REPO, DEF_DAYS, AI_SETTLE, REPO_HIST,
)
from charts import (
    fig_basis_waterfall,
    fig_net_basis_bar, fig_implied_repo_bar, fig_cf_scatter, fig_duration_bars,
    fig_carry_decomp, fig_carry_vs_repo, fig_forward_price, fig_repo_history,
    fig_ir_richcap,
    fig_nb_all_bonds,
    fig_pnl_bar, fig_pnl_heatmap, fig_hedge_ratio,
)

# Slider ID → display format string
_SLIDER_FMTS = {
    "repo-rate":  "{:.2f}%",
    "fut-price":  "{:.3f}",
    "rate-shift": "{:+.0f} bp",
    "days-del":   "{:.0f} days",
    "carry-repo": "{:.2f}%",
    "carry-days": "{:.0f} days",
    "ir-repo":    "{:.2f}%",
    "ir-fut":     "{:.3f}",
    "ir-shift":   "{:+.0f} bp",
    "ir-days":    "{:.0f} days",
    "opt-repo":   "{:.2f}%",
    "opt-fut":    "{:.3f}",
    "opt-days":   "{:.0f} days",
    "tr-face":    "${:.0f}MM",
    "tr-repo":    "{:.2f}%",
    "tr-days":    "{:.0f} days",
}


def register_callbacks(app):
    """Bind all @app.callback decorators. Must be called after app.layout is set."""

    # ── Slider value displays ─────────────────────────────────────────────────
    for sid, fmt in _SLIDER_FMTS.items():
        def _make(s, f):
            @app.callback(Output(f"{s}-val", "children"), Input(s, "value"))
            def _disp(v, _f=f):
                return _f.format(v) if v is not None else ""
        _make(sid, fmt)

    # ── Tab 1: Waterfall ──────────────────────────────────────────────────────
    @app.callback(
        Output("fig-waterfall", "figure"),
        Input("repo-rate",  "value"),
        Input("fut-price",  "value"),
        Input("rate-shift", "value"),
        Input("days-del",   "value"),
    )
    def cb_waterfall(repo, fut, shift, days):
        df  = build_basket(fut or DEF_FUT, repo or DEF_REPO, days or DEF_DAYS, shift or 0)
        ctd = df.loc[df["CTD"]].iloc[0]
        return fig_basis_waterfall(ctd["GrossBasis32"], ctd["Carry32"], ctd["NetBasis32"])

    # ── Tab 2: Deliverable Basket ─────────────────────────────────────────────
    @app.callback(
        Output("basket-table",  "data"),
        Output("basket-table",  "style_data_conditional"),
        Output("ctd-label",     "children"),
        Output("ctd-gb",        "children"),
        Output("ctd-carry",     "children"),
        Output("ctd-nb",        "children"),
        Output("ctd-ir",        "children"),
        Output("fig-nb-bar",    "figure"),
        Output("fig-ir-bar",    "figure"),
        Output("fig-cf-scat",   "figure"),
        Output("fig-dur-bars",  "figure"),
        Input("repo-rate",  "value"),
        Input("fut-price",  "value"),
        Input("rate-shift", "value"),
        Input("days-del",   "value"),
    )
    def cb_basket(repo, fut, shift, days):
        df  = build_basket(fut or DEF_FUT, repo or DEF_REPO, days or DEF_DAYS, shift or 0)
        ctd = df.loc[df["CTD"]].iloc[0]
        disp_cols = [
            "Bond", "Coupon", "CleanPx", "YTM", "CF", "CFxFut",
            "GrossBasis32", "Carry32", "NetBasis32", "ImplRepo", "DV01", "ModDur", "CTD",
        ]
        cond = [{"if": {"filter_query": f'{{Bond}} = "{ctd["Bond"]}"'},
                 "backgroundColor": "#1c2b1a", "color": "#f59e0b", "fontWeight": "700"}]
        return (
            df[disp_cols].to_dict("records"), cond,
            ctd["Bond"],
            f"{ctd['GrossBasis32']:.3f}",
            f"{ctd['Carry32']:.3f}",
            f"{ctd['NetBasis32']:.3f}",
            f"{ctd['ImplRepo']:.3f}%",
            fig_net_basis_bar(df),
            fig_implied_repo_bar(df, repo or DEF_REPO),
            fig_cf_scatter(df),
            fig_duration_bars(df),
        )

    # ── Tab 3: Carry ──────────────────────────────────────────────────────────
    @app.callback(
        Output("fig-carry-decomp",  "figure"),
        Output("fig-carry-vs-repo", "figure"),
        Output("fig-forward-px",    "figure"),
        Output("fig-repo-hist",     "figure"),
        Output("c-ci", "children"),
        Output("c-fc", "children"),
        Output("c-nc", "children"),
        Output("c-be", "children"),
        Input("carry-bond", "value"),
        Input("carry-repo", "value"),
        Input("carry-days", "value"),
    )
    def cb_carry(bond_idx, repo_pct, days):
        idx  = int(bond_idx) if bond_idx is not None else 4
        rpct = repo_pct or DEF_REPO
        d    = days or DEF_DAYS
        c, n, ytm0 = BASKET_SPEC[idx][1], BASKET_SPEC[idx][2], BASKET_SPEC[idx][3]
        px  = bprice(c, ytm0 / 100, n)
        fp  = px + AI_SETTLE
        car, ci, fc = carry_decomp(fp, c, rpct / 100, d)
        be  = c * 360 / (fp * 365)
        return (
            fig_carry_decomp(fp, c, rpct, d),
            fig_carry_vs_repo(fp, c, d),
            fig_forward_price(fp, c, d, rpct),
            fig_repo_history(REPO_HIST),
            f"${ci:.4f}",
            f"${fc:.4f}",
            f"${car:+.4f}",
            f"{be * 100:.3f}%",
        )

    # ── Tab 4: Implied Repo ───────────────────────────────────────────────────
    @app.callback(
        Output("fig-ir-bar2",    "figure"),
        Output("fig-ir-richcap", "figure"),
        Output("ir-ctd",    "children"),
        Output("ir-spread", "children"),
        Output("ir-rc",     "children"),
        Input("ir-repo",  "value"),
        Input("ir-fut",   "value"),
        Input("ir-shift", "value"),
        Input("ir-days",  "value"),
    )
    def cb_ir(repo, fut, shift, days):
        r, f = repo or DEF_REPO, fut or DEF_FUT
        df   = build_basket(f, r, days or DEF_DAYS, shift or 0)
        ctd  = df.loc[df["CTD"]].iloc[0]
        sp   = ctd["ImplRepo"] - r
        return (
            fig_implied_repo_bar(df, r),
            fig_ir_richcap(df, r),
            f"{ctd['ImplRepo']:.3f}%",
            f"{sp:+.3f}%",
            "CHEAP ▲" if sp > 0 else "RICH ▼",
        )

    # ── Tab 5: Delivery Options ───────────────────────────────────────────────
    @app.callback(
        Output("fig-opt-nb", "figure"),
        Input("opt-repo", "value"),
        Input("opt-fut",  "value"),
        Input("opt-days", "value"),
    )
    def cb_delivery(repo, fut, days):
        df = build_basket(fut or DEF_FUT, repo or DEF_REPO, days or DEF_DAYS)
        return fig_nb_all_bonds(df)

    # ── Tab 6: Basis Trading ──────────────────────────────────────────────────
    @app.callback(
        Output("fig-pnl-bar",  "figure"),
        Output("fig-pnl-heat", "figure"),
        Output("fig-hedge",    "figure"),
        Output("tr-dv01-b",    "children"),
        Output("tr-dv01-f",    "children"),
        Output("tr-hedge",     "children"),
        Output("tr-max-g",     "children"),
        Output("tr-max-l",     "children"),
        Input("tr-face", "value"),
        Input("tr-repo", "value"),
        Input("tr-days", "value"),
    )
    def cb_trading(face_mm, repo_pct, days):
        fm = face_mm or 10
        r  = repo_pct or DEF_REPO
        d  = days or DEF_DAYS
        df = build_basket(DEF_FUT, r, d)
        ctd = df.loc[df["CTD"]].iloc[0]

        ctd_dv01 = ctd["DV01"]
        ctd_cf   = ctd["CF"]
        fut_dv01 = ctd_dv01 / ctd_cf
        hedge    = ctd_dv01 / fut_dv01 / ctd_cf

        c, n, ytm0 = BASKET_SPEC[4][1], BASKET_SPEC[4][2], BASKET_SPEC[4][3]
        cfv   = conv_factor(c, n)
        ytm0a = ytm0 / 100
        dv_b  = dv01(c, ytm0a, n)
        px0   = bprice(c, ytm0a, n)
        nb0   = (px0 - cfv * DEF_FUT) - carry_decomp(px0 + AI_SETTLE, c, r / 100, d)[0]

        pnls = []
        for sh in np.linspace(-150, 150, 121):
            px_n  = bprice(c, ytm0a + sh / 1e4, n)
            fut_n = DEF_FUT - dv_b / cfv * sh
            nb_n  = (px_n - cfv * fut_n) - carry_decomp(px_n + AI_SETTLE, c, r / 100, d)[0]
            pnls.append((nb_n - nb0) * fm * 1e6 / 100)

        return (
            fig_pnl_bar(fm, r, d),
            fig_pnl_heatmap(fm, d),
            fig_hedge_ratio(df),
            f"${ctd_dv01 * fm * 10:,.0f}",
            f"${fut_dv01 * fm * 10:,.0f}",
            f"{hedge:.4f}",
            f"${max(pnls):,.0f}",
            f"${min(pnls):,.0f}",
        )
