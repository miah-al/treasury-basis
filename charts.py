"""
charts.py — Plotly figure builders for the Treasury Basis Explorer.
Every function returns a go.Figure ready for dcc.Graph.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from theme import C, FONT, PLOT_LAYOUT
from analytics import (
    bprice, conv_factor, carry_decomp, gross_basis, dv01,
    implied_repo as impl_repo_fn,
)
from data import BASKET_SPEC, OPTION_PROFILE_BONDS, DEF_FUT, DEF_REPO, DEF_DAYS, AI_SETTLE, build_basket


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _layout(fig: go.Figure, title: str = "", height: int = 360) -> go.Figure:
    fig.update_layout(
        **PLOT_LAYOUT,
        height=height,
        title=dict(text=title, font=dict(size=13, color=C["blue2"]), x=0, xref="paper"),
    )
    return fig


def _graph_cfg():
    return {"displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "displaylogo": False}


def _ctd_colors(df):
    return [C["amber"] if v else C["blue"] for v in df["CTD"]]


# ─── Tab 1 — Overview ─────────────────────────────────────────────────────────

def fig_cash_vs_futures(df_hist):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["CashPrice"],
        name="Cash (Clean)", line=dict(color=C["blue"], width=1.8)))
    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["FuturesPrice"],
        name="Futures", line=dict(color=C["amber"], width=1.8, dash="dot")))
    _layout(fig, "Cash Price vs Futures Price (CTD Bond)", height=300)
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return fig


def fig_basis_convergence(df_hist):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist["DaysLeft"], y=df_hist["GrossBasis"],
        name="Gross Basis", line=dict(color=C["blue"], width=2)))
    fig.add_trace(go.Scatter(x=df_hist["DaysLeft"], y=df_hist["Carry"],
        name="Carry", line=dict(color=C["green"], width=1.5, dash="dash")))
    fig.add_trace(go.Scatter(x=df_hist["DaysLeft"], y=df_hist["NetBasis"],
        name="Net Basis", line=dict(color=C["amber"], width=2)))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"], line_width=1)
    _layout(fig, "Basis Convergence to Delivery (32nds)", height=320)
    fig.update_xaxes(autorange="reversed", title="Days to Delivery")
    fig.update_yaxes(title="32nds per $100")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return fig


def fig_basis_waterfall(gb32, carry32, nb32):
    fig = go.Figure(go.Waterfall(
        measure=["absolute", "relative", "total"],
        x=["Gross Basis", "− Carry", "= Net Basis"],
        y=[gb32, -carry32, nb32],
        connector={"line": {"color": C["border2"]}},
        increasing={"marker": {"color": C["blue"]}},
        decreasing={"marker": {"color": C["red"]}},
        totals={"marker":   {"color": C["amber"]}},
        text=[f"{v:+.3f}" for v in [gb32, -carry32, nb32]],
        textposition="outside",
    ))
    _layout(fig, "Basis Decomposition — CTD Bond (32nds)", height=300)
    fig.update_yaxes(title="32nds per $100")
    return fig


def fig_yield_curve(df_yc):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_yc["Tenor"], y=df_yc["Yield"],
        mode="lines+markers", line=dict(color=C["cyan"], width=2),
        marker=dict(size=7, color=C["blue2"]),
        hovertemplate="Tenor: %{x}yr<br>Yield: %{y:.2f}%<extra></extra>"))
    fig.add_hrect(y0=DEF_REPO - 0.1, y1=DEF_REPO + 0.1,
                  fillcolor="rgba(245,158,11,0.1)", line_width=0,
                  annotation_text="Repo", annotation_position="top right",
                  annotation=dict(font=dict(color=C["amber"], size=10)))
    _layout(fig, "Treasury Yield Curve vs Repo Rate", height=300)
    fig.update_xaxes(title="Tenor (years)")
    fig.update_yaxes(title="Yield (%)")
    return fig


# ─── Tab 2 — Deliverable Basket ───────────────────────────────────────────────

def fig_net_basis_bar(df):
    fig = go.Figure(go.Bar(
        x=df["Bond"], y=df["NetBasis32"],
        marker_color=_ctd_colors(df),
        text=df["NetBasis32"], textposition="outside", texttemplate="%{text:.1f}",
        hovertemplate="<b>%{x}</b><br>Net Basis: %{y:.3f} 32nds<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"], line_width=1)
    _layout(fig, "Net Basis by Bond (32nds) — amber = CTD (lowest)", height=340)
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title="32nds per $100")
    return fig


def fig_implied_repo_bar(df, actual_repo):
    fig = go.Figure(go.Bar(
        x=df["Bond"], y=df["ImplRepo"],
        marker_color=_ctd_colors(df),
        hovertemplate="<b>%{x}</b><br>Impl. Repo: %{y:.3f}%<extra></extra>",
    ))
    fig.add_hline(y=actual_repo, line_dash="dash", line_color=C["red"], line_width=1.5,
                  annotation_text=f"Actual Repo {actual_repo:.2f}%",
                  annotation_position="top right",
                  annotation=dict(font=dict(color=C["red"], size=11)))
    _layout(fig, "Implied Repo Rate by Bond — CTD has highest value", height=340)
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title="Rate (%)")
    return fig


def fig_cf_scatter(df):
    """CF × Futures vs Clean Price — bond positions relative to the 45° line."""
    x, y   = df["CleanPx"], df["CFxFut"]
    r      = np.array([min(x.min(), y.min()) - 0.5, max(x.max(), y.max()) + 0.5])
    fig    = go.Figure()
    fig.add_trace(go.Scatter(x=r, y=r, mode="lines",
        line=dict(color=C["muted"], dash="dot", width=1), name="45° line", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text",
        marker=dict(size=9, color=_ctd_colors(df), line=dict(width=1, color=C["border2"])),
        text=df["Bond"], textposition="top center", textfont=dict(size=9, color=C["muted"]),
        customdata=np.stack([df["Bond"], df["GrossBasis32"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>Clean Px: %{x:.4f}<br>"
                      "CF×Fut: %{y:.4f}<br>Gross Basis: %{customdata[1]:.2f} 32nds"
                      "<extra></extra>", name="Bonds",
    ))
    _layout(fig, "CF × Futures vs Clean Price  (below 45° line → positive gross basis)", height=380)
    fig.update_xaxes(title="Clean Cash Price ($)")
    fig.update_yaxes(title="CF × Futures Price ($)")
    return fig


def fig_duration_bars(df):
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["DV01 ($ per bp)", "Modified Duration (yr)"])
    colors = _ctd_colors(df)
    fig.add_trace(go.Bar(x=df["Bond"], y=df["DV01"], marker_color=colors,
        hovertemplate="<b>%{x}</b><br>DV01: $%{y:.4f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=df["Bond"], y=df["ModDur"], marker_color=colors,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>ModDur: %{y:.3f}yr<extra></extra>"), row=1, col=2)
    fig.update_layout(**PLOT_LAYOUT, height=310,
        title=dict(text="DV01 & Modified Duration by Bond",
                   font=dict(size=13, color=C["blue2"]), x=0, xref="paper"))
    for ax in ["xaxis", "xaxis2"]:
        fig.update_layout({ax: {"tickangle": -30}})
    return fig


def fig_basis_vs_yield_shift():
    """Net basis of every basket bond across parallel yield shifts."""
    shifts = np.linspace(-200, 200, 61)
    fig    = go.Figure()
    # Approximate futures price movement: CTD DV01 × shift / CF_ctd
    c0, n0, ytm0 = BASKET_SPEC[4][1], BASKET_SPEC[4][2], BASKET_SPEC[4][3]  # CTD
    cf0 = conv_factor(c0, n0)
    dv0 = dv01(c0, ytm0 / 100, n0)

    for label, c, n, ytm_base in BASKET_SPEC:
        nbs = []
        for sh in shifts:
            ytm     = (ytm_base + sh / 100) / 100
            fut_adj = DEF_FUT - dv0 / cf0 * sh         # futures co-moves with rates
            px      = bprice(c, ytm, n)
            cfv     = conv_factor(c, n)
            fp      = px + AI_SETTLE
            gb      = gross_basis(px, fut_adj, cfv)
            car, _, _ = carry_decomp(fp, c, DEF_REPO / 100, DEF_DAYS)
            nbs.append((gb - car) * 32)
        fig.add_trace(go.Scatter(x=shifts, y=nbs, name=label,
            line=dict(width=1.5), mode="lines",
            hovertemplate=f"<b>{label}</b><br>Shift: %{{x:.0f}}bp<br>"
                          "Net Basis: %{y:.2f} 32nds<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"], line_width=1)
    fig.add_vline(x=0, line_dash="dash", line_color=C["muted"], line_width=1,
                  annotation_text="Current", annotation_position="top",
                  annotation=dict(font=dict(color=C["muted"], size=10)))
    _layout(fig, "Net Basis vs Yield Shift — Identifies CTD at Each Level", height=400)
    fig.update_xaxes(title="Parallel Yield Shift (bp)")
    fig.update_yaxes(title="Net Basis (32nds)")
    return fig


# ─── Tab 3 — Carry ────────────────────────────────────────────────────────────

def fig_carry_decomp(full_price, coupon_pct, repo_pct, days):
    """Coupon income and financing cost over the holding period."""
    dr  = np.arange(1, days + 1)
    ci  = coupon_pct * dr / 365
    fc  = full_price * (repo_pct / 100) * dr / 360
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dr, y=ci, name="Coupon Income",
        line=dict(color=C["green"], width=1.8)))
    fig.add_trace(go.Scatter(x=dr, y=fc, name="Financing Cost",
        fill="tonexty", fillcolor="rgba(239,68,68,0.10)",
        line=dict(color=C["red"], width=1.8)))
    fig.add_trace(go.Scatter(x=dr, y=ci - fc, name="Net Carry",
        line=dict(color=C["amber"], width=2, dash="dash")))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"], line_width=1)
    _layout(fig, "Carry Decomposition: Coupon Income vs Financing Cost ($)", height=320)
    fig.update_xaxes(title="Days Held")
    fig.update_yaxes(title="$ per $100 face")
    return fig


def fig_carry_vs_repo(full_price, coupon_pct, days):
    """Net carry sensitivity to repo rate — highlights break-even repo."""
    repos   = np.linspace(0.5, 8.0, 200)
    carries = [carry_decomp(full_price, coupon_pct, r / 100, days)[0] for r in repos]
    be_repo = coupon_pct * 360 / (full_price * 365)   # break-even repo
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=repos, y=carries, mode="lines",
        line=dict(color=C["blue"], width=2), fill="tozeroy",
        fillcolor="rgba(16,185,129,0.08)",
        hovertemplate="Repo: %{x:.2f}%<br>Carry: $%{y:.4f}<extra></extra>", name="Carry"))
    fig.add_vline(x=be_repo * 100, line_dash="dash", line_color=C["amber"],
                  annotation_text=f"Break-even {be_repo*100:.2f}%",
                  annotation_position="top left",
                  annotation=dict(font=dict(color=C["amber"], size=11)))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"], line_width=1)
    _layout(fig, "Carry vs Repo Rate — Break-even analysis", height=320)
    fig.update_xaxes(title="Repo Rate (%)")
    fig.update_yaxes(title="$ Carry per $100 face")
    return fig


def fig_forward_price(full_price, coupon_pct, days_max, repo_pct):
    """Forward clean price vs days to delivery for multiple repo rates."""
    dr  = np.arange(1, days_max + 1)
    ai_at_del = AI_SETTLE + coupon_pct / 2 * (dr / 182.5)
    fig = go.Figure()
    for r_pct, color in [(2.0, C["green"]), (repo_pct, C["blue"]), (7.0, C["red"])]:
        r   = r_pct / 100
        ci  = coupon_pct * dr / 365
        fwd = full_price * (1 + r * dr / 360) - ci - ai_at_del
        lbl = f"Repo {r_pct:.1f}%{' (current)' if r_pct == repo_pct else ''}"
        fig.add_trace(go.Scatter(x=dr, y=fwd, name=lbl,
            line=dict(color=color, width=1.8 if r_pct == repo_pct else 1.2)))
    fig.add_hline(y=full_price - AI_SETTLE, line_dash="dot", line_color=C["muted"],
                  annotation_text="Spot clean", annotation_position="right",
                  annotation=dict(font=dict(color=C["muted"], size=10)))
    _layout(fig, "Forward (Clean) Price vs Days to Delivery", height=320)
    fig.update_xaxes(title="Days to Delivery")
    fig.update_yaxes(title="Forward Clean Price ($)")
    return fig


def fig_repo_history(df_repo):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_repo["Date"], y=df_repo["Repo"],
        line=dict(color=C["blue"], width=1.5), fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)", name="Repo Rate",
        hovertemplate="%{x|%Y-%m-%d}<br>Repo: %{y:.2f}%<extra></extra>"))
    _layout(fig, "Historical Repo Rate (hypothetical, %)", height=280)
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title="Rate (%)")
    return fig


# ─── Tab 4 — Implied Repo ─────────────────────────────────────────────────────

def fig_ir_richcap(df, actual_repo):
    """Implied repo minus actual repo — green = cheap, red = rich."""
    spread = df["ImplRepo"] - actual_repo
    colors = [C["green"] if s > 0 else C["red"] for s in spread]
    fig = go.Figure(go.Bar(x=df["Bond"], y=spread, marker_color=colors,
        text=[f"{s:+.2f}%" for s in spread], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Spread: %{y:+.3f}%<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"])
    _layout(fig, "Implied Repo − Actual Repo  (green = cheap to deliver)", height=320)
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title="Spread (%)")
    return fig


# ─── Tab 5 — Delivery Options ─────────────────────────────────────────────────

def fig_ctd_switch(df_switch):
    ctd_names = df_switch["CTD"].unique().tolist()
    palette   = [C["blue"], C["amber"], C["green"], C["purple"],
                 C["cyan"], C["red"], C["indigo"]]
    color_map = dict(zip(ctd_names, palette))
    fig = go.Figure()
    for nm in ctd_names:
        m = df_switch["CTD"] == nm
        fig.add_trace(go.Scatter(
            x=df_switch.loc[m, "Shift"], y=df_switch.loc[m, "ImplRepo"],
            name=nm, mode="markers+lines",
            line=dict(color=color_map.get(nm, C["blue"]), width=1.2),
            marker=dict(size=4)))
    fig.add_vline(x=0, line_dash="dash", line_color=C["muted"], line_width=1,
                  annotation_text="Current", annotation_position="top",
                  annotation=dict(font=dict(color=C["muted"], size=10)))
    _layout(fig, "CTD Switching: Best Implied Repo vs Yield Shift", height=360)
    fig.update_xaxes(title="Parallel Yield Shift (bp)")
    fig.update_yaxes(title="CTD Implied Repo (%)")
    return fig


def fig_option_value(df_opt):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_opt["Shift"], y=df_opt["OptionValue"],
        fill="tozeroy", fillcolor="rgba(139,92,246,0.15)",
        line=dict(color=C["purple"], width=2), name="Quality Option Value"))
    fig.add_trace(go.Scatter(x=df_opt["Shift"], y=df_opt["CTDNetBasis"],
        line=dict(color=C["amber"], width=1.5, dash="dash"), name="CTD Net Basis"))
    fig.add_vline(x=0, line_dash="dash", line_color=C["muted"], line_width=1)
    _layout(fig, "Delivery Quality Option Value vs Yield Shift (32nds)", height=340)
    fig.update_xaxes(title="Parallel Yield Shift (bp)")
    fig.update_yaxes(title="32nds per $100")
    return fig


def fig_nb_all_bonds(df):
    """Net basis bar chart for delivery options tab (option perspective)."""
    fig = go.Figure(go.Bar(
        x=df["Bond"], y=df["NetBasis32"],
        marker_color=_ctd_colors(df),
        text=df["NetBasis32"], textposition="outside", texttemplate="%{text:.1f}",
        hovertemplate="<b>%{x}</b><br>Net Basis: %{y:.2f} 32nds<extra></extra>",
    ))
    fig.add_annotation(x=0.5, y=0.97, xref="paper", yref="paper",
        text="Net basis = delivery option value for each bond | CTD has minimum",
        showarrow=False, font=dict(color=C["muted"], size=11))
    _layout(fig, "Net Basis = Embedded Option Value by Bond (32nds)", height=320)
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title="32nds per $100")
    return fig


# ─── Tab 6 — Basis Trading ────────────────────────────────────────────────────

def fig_pnl_bar(face_mm, repo_pct, days):
    """P&L of long basis trade (long CTD, short CF-adjusted futures) vs rate shift."""
    c, n, ytm0 = BASKET_SPEC[4][1], BASKET_SPEC[4][2], BASKET_SPEC[4][3]  # CTD
    cfv        = conv_factor(c, n)
    ytm0a      = ytm0 / 100
    px0        = bprice(c, ytm0a, n)
    gb0        = gross_basis(px0, DEF_FUT, cfv)
    car0, _, _ = carry_decomp(px0 + AI_SETTLE, c, repo_pct / 100, days)
    nb0        = gb0 - car0
    dv_bond    = dv01(c, ytm0a, n)

    shifts = np.linspace(-150, 150, 121)
    pnls   = []
    for sh in shifts:
        ytm_new = ytm0a + sh / 1e4
        fut_new = DEF_FUT - dv_bond / cfv * sh
        px_new  = bprice(c, ytm_new, n)
        gb_new  = gross_basis(px_new, fut_new, cfv)
        car_new, _, _ = carry_decomp(px_new + AI_SETTLE, c, repo_pct / 100, days)
        pnls.append((gb_new - car_new - nb0) * face_mm * 1e6 / 100)

    colors = [C["green"] if p >= 0 else C["red"] for p in pnls]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=shifts, y=pnls, marker_color=colors, showlegend=False,
        hovertemplate="Shift: %{x:.0f}bp<br>P&L: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=shifts, y=pnls, line=dict(color=C["amber"], width=1.5),
        showlegend=False, hoverinfo="skip"))
    fig.add_hline(y=0, line_dash="dot", line_color=C["muted"])
    _layout(fig, f"Long Basis Trade P&L — ${face_mm}MM face | {days}d carry", height=340)
    fig.update_xaxes(title="Parallel Yield Shift (bp)")
    fig.update_yaxes(title="P&L ($)")
    return fig


def fig_pnl_heatmap(face_mm, days):
    """P&L heatmap: yield shift × repo change."""
    c, n, ytm0 = BASKET_SPEC[4][1], BASKET_SPEC[4][2], BASKET_SPEC[4][3]
    cfv        = conv_factor(c, n)
    ytm0a      = ytm0 / 100
    px0        = bprice(c, ytm0a, n)
    gb0        = gross_basis(px0, DEF_FUT, cfv)
    car0, _, _ = carry_decomp(px0 + AI_SETTLE, c, DEF_REPO / 100, days)
    nb0        = gb0 - car0
    dv_bond    = dv01(c, ytm0a, n)

    shifts   = np.linspace(-150, 150, 31)
    repo_chg = np.linspace(-1.5, 1.5, 21)
    z = np.zeros((len(repo_chg), len(shifts)))
    for j, sh in enumerate(shifts):
        for i, rc in enumerate(repo_chg):
            ytm_new = ytm0a + sh / 1e4
            fut_new = DEF_FUT - dv_bond / cfv * sh
            px_new  = bprice(c, ytm_new, n)
            gb_new  = gross_basis(px_new, fut_new, cfv)
            car_new, _, _ = carry_decomp(px_new + AI_SETTLE, c, (DEF_REPO + rc) / 100, days)
            z[i, j] = (gb_new - car_new - nb0) * face_mm * 1e6 / 100

    fig = go.Figure(go.Heatmap(
        x=shifts, y=repo_chg, z=z, zmid=0,
        colorscale=[[0, C["red"]], [0.5, "#1e2d44"], [1, C["green"]]],
        colorbar=dict(title=dict(text="P&L ($)", font=dict(color=C["muted"])),
                      tickfont=dict(color=C["text"])),
        hovertemplate="Yield Shift: %{x:.0f}bp<br>Repo Chg: %{y:+.2f}%<br>"
                      "P&L: $%{z:,.0f}<extra></extra>",
    ))
    _layout(fig, "P&L Heatmap — Yield Shift × Repo Change", height=360)
    fig.update_xaxes(title="Parallel Yield Shift (bp)")
    fig.update_yaxes(title="Repo Rate Change (%)")
    return fig


def fig_hedge_ratio(df):
    """DV01-neutral futures hedge ratio per bond in the basket."""
    ctd_row  = df.loc[df["CTD"]].iloc[0]
    fut_dv01 = ctd_row["DV01"] / ctd_row["CF"]
    hedge    = df["DV01"] / fut_dv01 / df["CF"]
    fig = go.Figure(go.Bar(
        x=df["Bond"], y=hedge, marker_color=_ctd_colors(df),
        text=[f"{h:.4f}" for h in hedge], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Hedge Ratio: %{y:.4f}<extra></extra>",
    ))
    _layout(fig, "DV01-Neutral Futures Hedge Ratio (contracts per $100k face)", height=320)
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(title="Futures per Bond")
    return fig


# ─── Tab 5 — Option Profile Exhibits (Burghardt Ch. 2) ───────────────────────

def fig_basis_option_profiles():
    """
    Reproduces Exhibits 2.7, 2.8, and the straddle from Burghardt, Belton,
    Lane & Papa — Chapter 2.

    Three-row × two-column layout:
      Left  panel: Price/CF (bond) vs theoretical futures price across yield shifts.
                   The vertical distance between the two lines IS the gross basis.
      Right panel: Net basis (32nds) vs yield shift — the option-payoff shape.

    Key intuition:
      Low-coupon / high-duration bond  →  Price/CF curve is MORE convex than
        futures (which tracks the CTD).  At large yield FALLS the bond wins;
        at yield RISES the CTD takes over → call-option payoff shape.
      High-coupon / low-duration bond  →  CF is large (price at 6% ref rate
        above par).  CF×Futures falls fast when yields rise; bond holds value
        better → put-option payoff shape.
      Medium-coupon CTD bond           →  bond IS the reference; futures
        tracks it exactly at par.  Any move away from current yield opens
        a gap → U-shaped straddle payoff.
    """
    shifts   = np.linspace(-250, 250, 201)
    repo     = DEF_REPO / 100
    days     = DEF_DAYS

    # Theoretical futures at each parallel shift = min_i( fwd_clean_i / CF_i )
    # over the BASKET (not the profile bonds themselves).
    theo_futures = []
    for sh in shifts:
        best = float("inf")
        for _, bc, bn, bytm0 in BASKET_SPEC:
            bytm = (bytm0 + sh / 100) / 100
            bpx  = bprice(bc, bytm, bn)
            bcf  = conv_factor(bc, bn)
            bfp  = bpx + AI_SETTLE
            bci  = bc * days / 365
            bfc  = bfp * repo * days / 360
            bfwd = bpx + bfc - bci          # forward clean price
            best = min(best, bfwd / bcf)
        theo_futures.append(best)

    # ── Subplot grid ──────────────────────────────────────────────────────────
    profile_labels = [b[0] for b in OPTION_PROFILE_BONDS]
    subtitle_pairs = [
        (f"Price/CF vs Futures — {profile_labels[0].split('  ')[0]}",
         "Exhibit 2.7 Analog: ΔGross Basis  (Call Option — gains when yields FALL ▼)"),
        (f"Price/CF vs Futures — {profile_labels[1].split('  ')[0]}",
         "Straddle Analog: ΔGross Basis  (gains when yields move EITHER way ∪)"),
        (f"Price/CF vs Futures — {profile_labels[2].split('  ')[0]}",
         "Exhibit 2.8 Analog: ΔGross Basis  (Put Option — gains when yields RISE ▲)"),
    ]
    all_subtitles = [s for pair in subtitle_pairs for s in pair]

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=all_subtitles,
        vertical_spacing=0.11,
        horizontal_spacing=0.08,
    )

    profile_colors = [C["blue"], C["amber"], C["red"]]
    fill_colors    = [
        "rgba(59,130,246,0.12)",
        "rgba(245,158,11,0.12)",
        "rgba(239,68,68,0.12)",
    ]

    for row_idx, ((label, c, n, ytm_base, ptype), col, fc) in enumerate(
            zip(OPTION_PROFILE_BONDS, profile_colors, fill_colors), start=1):

        cfv   = conv_factor(c, n)
        ytm0  = ytm_base / 100

        px_cf_vals = []
        gb_vals    = []   # gross basis in 32nds

        for sh, theo_f in zip(shifts, theo_futures):
            ytm = ytm0 + sh / 1e4
            px  = bprice(c, ytm, n)
            gb  = (px - cfv * theo_f) * 32   # gross basis in 32nds (can be negative)
            gb_vals.append(gb)
            px_cf_vals.append(px / cfv)

        # Normalise right panel to Δ from current level (shift=0)
        # This reveals the option-payoff SHAPE regardless of starting sign.
        gb0       = gb_vals[len(shifts) // 2]     # value at shift = 0
        delta_gb  = [v - gb0 for v in gb_vals]

        # ── Left panel: Price/CF vs Futures ──────────────────────────────────
        fig.add_trace(go.Scatter(
            x=shifts, y=px_cf_vals,
            name=f"{c:.3f}% Bond (Price÷CF)",
            line=dict(color=col, width=2.2),
            hovertemplate="Shift: %{x:.0f}bp<br>Price/CF: %{y:.4f}<extra></extra>",
        ), row=row_idx, col=1)

        fig.add_trace(go.Scatter(
            x=shifts, y=theo_futures,
            name="Theoretical Futures" if row_idx == 1 else None,
            showlegend=(row_idx == 1),
            line=dict(color=C["muted"], dash="dot", width=1.5),
            hovertemplate="Shift: %{x:.0f}bp<br>Futures: %{y:.4f}<extra></extra>",
        ), row=row_idx, col=1)

        # shade the gap between Price/CF and Futures
        fig.add_trace(go.Scatter(
            x=shifts, y=theo_futures, fill=None, showlegend=False,
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
        ), row=row_idx, col=1)
        fig.add_trace(go.Scatter(
            x=shifts, y=px_cf_vals, fill="tonexty", showlegend=False,
            fillcolor=fc, line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
        ), row=row_idx, col=1)

        # ── Right panel: ΔGross Basis from current (32nds) ────────────────────
        # Plotting the CHANGE in gross basis clearly reveals the option payoff:
        #   Call  → ΔGB > 0 when yields fall  (like a call gaining on rally)
        #   Put   → ΔGB > 0 when yields rise  (like a put gaining on selloff)
        #   Straddle → ΔGB > 0 for large moves in either direction (long gamma)
        fig.add_trace(go.Scatter(
            x=shifts, y=delta_gb,
            name=f"{ptype.title()} profile",
            fill="tozeroy", fillcolor=fc,
            line=dict(color=col, width=2.2),
            hovertemplate=(
                "Shift: %{x:.0f}bp<br>"
                "ΔGross Basis: %{y:+.2f} 32nds<extra></extra>"
            ),
        ), row=row_idx, col=2)

        fig.add_hline(y=0,  line_dash="dot",  line_color=C["muted"], line_width=1,
                      row=row_idx, col=2)
        fig.add_vline(x=0,  line_dash="dash", line_color=C["muted"], line_width=1,
                      annotation_text="Current yield",
                      annotation_font=dict(color=C["muted"], size=9),
                      annotation_position="top",
                      row=row_idx, col=2)
        fig.add_vline(x=0,  line_dash="dash", line_color=C["muted"], line_width=1,
                      row=row_idx, col=1)

    # ── Global layout ─────────────────────────────────────────────────────────
    layout_kw = dict(PLOT_LAYOUT)
    layout_kw["legend"] = dict(orientation="h", y=-0.04, font=dict(size=10))
    fig.update_layout(
        **layout_kw,
        height=900,
        title=dict(
            text="Basis as Embedded Option  —  Burghardt et al. Exhibits 2.7, 2.8 & Straddle",
            font=dict(size=13, color=C["blue2"]), x=0, xref="paper",
        ),
        showlegend=True,
    )
    for row in range(1, 4):
        fig.update_xaxes(title_text="Yield Shift (bp)",  row=row, col=1)
        fig.update_xaxes(title_text="Yield Shift (bp)",  row=row, col=2)
        fig.update_yaxes(title_text="Price / CF  ($)",   row=row, col=1)
        fig.update_yaxes(title_text="ΔGross Basis from Current (32nds)", row=row, col=2)

    return fig
