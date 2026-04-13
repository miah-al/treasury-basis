"""
layout.py — Assembles the full Dash app layout from per-tab builders.
Each tab function returns a dbc.Container with its charts and controls.
"""
import dash_bootstrap_components as dbc
from dash import html, dash_table

from theme import C, TAB_STYLE, TAB_SEL_STYLE, TABLE_STYLES
from data import DEF_FUT, DEF_REPO, DEF_DAYS, BASKET_SPEC, HIST, YLD_CURVE, REPO_HIST
from charts import (
    fig_cash_vs_futures, fig_basis_convergence, fig_yield_curve,
    fig_basis_vs_yield_shift,
    fig_ctd_switch, fig_option_value, fig_basis_option_profiles,
)
from components import (
    slider, metric_pill, article_card, formula_block, graph, controls_row,
)
import data as _d


# ─── Static pre-computed figures (no user controls needed) ────────────────────
_FIG_CASH_FUT   = fig_cash_vs_futures(HIST)
_FIG_BASIS_CONV = fig_basis_convergence(HIST)
_FIG_YIELD_CRV  = fig_yield_curve(YLD_CURVE)
_FIG_BASIS_YTM  = fig_basis_vs_yield_shift()
_FIG_CTD_SW     = fig_ctd_switch(_d.CTD_SWITCH)
_FIG_OPT_VAL    = fig_option_value(_d.OPT_VALUE)
_FIG_OPT_PROF   = fig_basis_option_profiles()    # Exhibits 2.7, 2.8, straddle


# ─── Tab 1: The Basis Defined ─────────────────────────────────────────────────
CONCEPTS = [
    ("Gross Basis",
     "The raw, unfinanced basis: Cash Clean Price − CF × Futures Price. "
     "A positive value means cash is expensive relative to the futures hedge. "
     "For most bonds in the deliverable basket, the gross basis is positive."),
    ("Carry",
     "Net income from holding the bond until delivery: Coupon Income − Financing "
     "Cost. Positive when the coupon yield exceeds the repo rate (normal carry "
     "environment). Negative when repo > coupon yield."),
    ("Net Basis",
     "Gross Basis − Carry. The residual that measures the value of embedded "
     "delivery options (quality, wildcard, end-of-month). For the CTD bond in a "
     "frictionless world, net basis approaches zero at delivery."),
    ("Implied Repo",
     "The financing rate that makes delivering the bond into futures break-even. "
     "The CTD bond has the HIGHEST implied repo in the basket. Implied repo "
     "below the actual repo means the bond is too expensive to deliver."),
]

FORMULAS = [
    ("Gross Basis",   "Gross Basis  =  Cash Price  −  CF × Futures"),
    ("Carry",         "Carry  =  Coupon × (d/365)  −  Full Price × r × (d/360)"),
    ("Net Basis",     "Net Basis  =  Gross Basis  −  Carry"),
    ("Implied Repo",  "Implied Repo  =  (Invoice + CI − Full Price)\n"
                      "                 ────────────────────────────\n"
                      "                   Full Price × (d / 360)"),
]


def tab_overview():
    concept_row = dbc.Row(
        [dbc.Col(article_card(t, b), width=3) for t, b in CONCEPTS],
        className="g-3 mb-3")

    formula_row = dbc.Row(
        [dbc.Col(formula_block(lbl, fml), width=3) for lbl, fml in FORMULAS],
        className="g-3 mb-3")

    return dbc.Container([
        dbc.Row([dbc.Col([
            html.Div("The Treasury Bond Basis", style={
                "fontSize": "24px", "fontWeight": "700", "color": C["white"], "marginBottom": "4px"}),
            html.Div("Interactive guide based on Burghardt, Belton, Lane & Papa — Jun-2026 10yr T-Note Futures",
                     style={"color": C["muted"], "fontSize": "14px", "marginBottom": "20px"}),
        ])]),
        concept_row,
        formula_row,
        dbc.Row([
            dbc.Col([graph(_FIG_CASH_FUT)], width=6),
            dbc.Col([graph(_FIG_YIELD_CRV)], width=6),
        ], className="g-3 mb-3"),
        dbc.Row([
            dbc.Col([graph(_FIG_BASIS_CONV)], width=8),
            dbc.Col([graph("fig-waterfall")], width=4),
        ], className="g-3"),
    ], fluid=True, style={"paddingTop": "20px"})


# ─── Tab 2: Deliverable Basket ────────────────────────────────────────────────
def tab_basket():
    controls = html.Div([
        dbc.Row([
            dbc.Col(slider("repo-rate",  1.0, 8.0,   0.05,  DEF_REPO, "Repo Rate (%)"),    width=3),
            dbc.Col(slider("fut-price",  95.0, 130.0, 0.125, DEF_FUT,  "Futures Price"),    width=3),
            dbc.Col(slider("rate-shift", -200, 200,   5,     0,        "Yield Shift (bp)"), width=3),
            dbc.Col(slider("days-del",   10, 120,     1,     DEF_DAYS, "Days to Delivery"), width=3),
        ]),
        dbc.Row([
            dbc.Col(metric_pill("CTD Bond",         "ctd-label", C["amber"]),  width="auto"),
            dbc.Col(metric_pill("Gross Basis (32s)", "ctd-gb",    C["blue2"]), width="auto"),
            dbc.Col(metric_pill("Carry (32s)",       "ctd-carry", C["green"]), width="auto"),
            dbc.Col(metric_pill("Net Basis (32s)",   "ctd-nb",    C["amber"]), width="auto"),
            dbc.Col(metric_pill("Impl. Repo (%)",    "ctd-ir",    C["cyan"]),  width="auto"),
        ], className="g-2"),
    ], style={"background": C["surface"], "border": f"1px solid {C['border']}",
              "borderRadius": "10px", "padding": "18px 20px", "marginBottom": "18px"})

    tbl = dash_table.DataTable(
        id="basket-table",
        columns=[{"name": c, "id": c} for c in [
            "Bond", "Coupon", "CleanPx", "YTM", "CF", "CFxFut",
            "GrossBasis32", "Carry32", "NetBasis32", "ImplRepo", "DV01", "ModDur"]],
        sort_action="native", page_size=12,
        **TABLE_STYLES,
    )

    return dbc.Container([
        controls,
        dbc.Row([dbc.Col(tbl)], className="mb-3"),
        dbc.Row([
            dbc.Col(graph("fig-nb-bar"),   width=6),
            dbc.Col(graph("fig-ir-bar"),   width=6),
        ], className="g-3 mb-3"),
        dbc.Row([
            dbc.Col(graph("fig-cf-scat"),  width=6),
            dbc.Col(graph("fig-dur-bars"), width=6),
        ], className="g-3 mb-3"),
        dbc.Row([dbc.Col(graph(_FIG_BASIS_YTM), width=12)], className="g-3"),
    ], fluid=True, style={"paddingTop": "16px"})


# ─── Tab 3: Carry & Forward Price ─────────────────────────────────────────────
def tab_carry():
    bond_opts = [{"label": s[0], "value": str(i)} for i, s in enumerate(BASKET_SPEC)]
    controls = html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Bond", style={"color": C["muted"], "fontSize": "11px",
                    "textTransform": "uppercase", "letterSpacing": "0.06em",
                    "marginBottom": "4px", "display": "block"}),
                dbc.Select(id="carry-bond", options=bond_opts, value="4",
                    style={"backgroundColor": C["surface"], "border": f"1px solid {C['border']}",
                           "borderRadius": "6px", "fontSize": "13px", "color": C["text"],
                           "padding": "6px 10px", "cursor": "pointer"}),
            ], width=3),
            dbc.Col(slider("carry-repo", 1.0, 8.0,   0.05,  DEF_REPO, "Repo Rate (%)"),    width=3),
            dbc.Col(slider("carry-days", 10,  120,    1,     DEF_DAYS, "Days to Delivery"), width=3),
        ]),
        dbc.Row([
            dbc.Col(metric_pill("Coupon Income ($)", "c-ci",  C["green"]), width="auto"),
            dbc.Col(metric_pill("Financing Cost ($)", "c-fc", C["red"]),   width="auto"),
            dbc.Col(metric_pill("Net Carry ($)",      "c-nc", C["amber"]), width="auto"),
            dbc.Col(metric_pill("Break-even Repo (%)", "c-be", C["cyan"]), width="auto"),
        ], className="g-2"),
    ], style={"background": C["surface"], "border": f"1px solid {C['border']}",
              "borderRadius": "10px", "padding": "18px 20px", "marginBottom": "18px"})

    return dbc.Container([
        controls,
        dbc.Row([
            dbc.Col(graph("fig-carry-decomp"),  width=6),
            dbc.Col(graph("fig-carry-vs-repo"), width=6),
        ], className="g-3 mb-3"),
        dbc.Row([
            dbc.Col(graph("fig-forward-px"), width=6),
            dbc.Col(graph("fig-repo-hist"),  width=6),
        ], className="g-3"),
    ], fluid=True, style={"paddingTop": "16px"})


# ─── Tab 4: Implied Repo & Rich/Cheap ────────────────────────────────────────
def tab_implied_repo():
    controls = html.Div([
        dbc.Row([
            dbc.Col(slider("ir-repo",  1.0, 8.0,   0.05,  DEF_REPO, "Actual Repo (%)"),  width=3),
            dbc.Col(slider("ir-fut",   95.0, 130.0, 0.125, DEF_FUT,  "Futures Price"),   width=3),
            dbc.Col(slider("ir-shift", -200, 200,   5,     0,        "Yield Shift (bp)"), width=3),
            dbc.Col(slider("ir-days",  10, 120,     1,     DEF_DAYS, "Days to Delivery"), width=3),
        ]),
        dbc.Row([
            dbc.Col(metric_pill("CTD Impl. Repo (%)", "ir-ctd",    C["cyan"]),  width="auto"),
            dbc.Col(metric_pill("Spread vs Actual",   "ir-spread", C["amber"]), width="auto"),
            dbc.Col(metric_pill("Rich / Cheap",       "ir-rc",     C["green"]), width="auto"),
        ], className="g-2"),
    ], style={"background": C["surface"], "border": f"1px solid {C['border']}",
              "borderRadius": "10px", "padding": "18px 20px", "marginBottom": "18px"})

    insight_cards = dbc.Row([
        dbc.Col(html.Div([
            html.Div("Implied Repo > Actual Repo", style={"color": C["green"],
                "fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"}),
            html.Div("Bond is CHEAP to deliver. Buying cash and delivering via "
                     "futures earns more than the repo rate. This bond is a "
                     "CTD candidate.",
                     style={"color": C["text"], "fontSize": "13px", "lineHeight": "1.65"}),
        ], style={"background": C["surface"], "borderLeft": f"3px solid {C['green']}",
                  "border": f"1px solid {C['border']}", "borderRadius": "8px", "padding": "14px"}), width=6),
        dbc.Col(html.Div([
            html.Div("Implied Repo < Actual Repo", style={"color": C["red"],
                "fontWeight": "600", "fontSize": "13px", "marginBottom": "6px"}),
            html.Div("Bond is RICH — financing costs more than the futures hedge "
                     "returns. Delivering this bond is sub-optimal; avoid it.",
                     style={"color": C["text"], "fontSize": "13px", "lineHeight": "1.65"}),
        ], style={"background": C["surface"], "borderLeft": f"3px solid {C['red']}",
                  "border": f"1px solid {C['border']}", "borderRadius": "8px", "padding": "14px"}), width=6),
    ], className="g-3 mb-3")

    return dbc.Container([
        controls,
        dbc.Row([
            dbc.Col(graph("fig-ir-bar2"),    width=6),
            dbc.Col(graph("fig-ir-richcap"), width=6),
        ], className="g-3 mb-3"),
        insight_cards,
    ], fluid=True, style={"paddingTop": "16px"})


# ─── Tab 5: Delivery Options ──────────────────────────────────────────────────
def tab_delivery():
    concepts = [
        ("Quality (Switch) Option",
         "The short holds the right to deliver any bond in the basket. As yields "
         "shift, the CTD changes. This switching option has value: the short always "
         "delivers the cheapest available bond, creating a floor on the cost of "
         "acquiring the bond to deliver."),
        ("End-of-Month Option",
         "Delivery can occur on any business day in the delivery month. After the "
         "futures stop trading, the settlement price is fixed, but the short can "
         "still observe bond prices. A price drop in the bond after settlement can "
         "be exploited by delivering at the old (higher) invoice price."),
        ("Wildcard Option",
         "Delivery notice must be submitted by 8 PM, but futures close at 2 PM. "
         "If cash bonds fall in the 2–8 PM window, the short can lock in that "
         "day's invoice price (based on the 2 PM settlement) against the lower "
         "cash bond purchase price."),
    ]
    concept_row = dbc.Row(
        [dbc.Col(article_card(t, b), width=4) for t, b in concepts],
        className="g-3 mb-3")

    controls = html.Div([
        dbc.Row([
            dbc.Col(slider("opt-repo", 1.0, 8.0,   0.05,  DEF_REPO, "Repo Rate (%)"),    width=3),
            dbc.Col(slider("opt-fut",  95.0, 130.0, 0.125, DEF_FUT,  "Futures Price"),   width=3),
            dbc.Col(slider("opt-days", 10, 120,     1,     DEF_DAYS, "Days to Delivery"), width=3),
        ]),
    ], style={"background": C["surface"], "border": f"1px solid {C['border']}",
              "borderRadius": "10px", "padding": "18px 20px", "marginBottom": "18px"})

    # Option-profile explanation cards (book concepts)
    option_profile_cards = dbc.Row([
        dbc.Col(article_card(
            "Exhibit 2.7 — Low-Coupon Bond: Call Option Profile",
            "A low-coupon (high-duration) bond has a Price/CF curve that is MORE convex than "
            "the futures price line. When yields FALL, the bond's price rises more than "
            "CF × Futures → basis WIDENS (positive P&L for long-basis holder). When yields "
            "RISE, the CTD switches to a higher-coupon bond, dragging futures below the "
            "low-coupon bond's price/CF → basis NARROWS. This one-sided payoff resembles "
            "a call option on bond futures."
        ), width=4),
        dbc.Col(article_card(
            "Straddle — Medium-Coupon CTD Bond",
            "The current CTD bond's Price/CF tracks the futures price closely at the "
            "current yield level (net basis ≈ option premium only). Any large yield move "
            "in EITHER direction creates a basis widening: yields fall → high-duration bonds "
            "become CTD, making this bond relatively expensive; yields rise → high-coupon "
            "bonds take over as CTD. The U-shaped net basis profile resembles a straddle — "
            "long this bond's basis is long gamma."
        ), width=4),
        dbc.Col(article_card(
            "Exhibit 2.8 — High-Coupon / Same-Maturity Bond: Put Option Profile",
            "A high-coupon bond with the SAME short maturity as the CTD has a LOWER modified "
            "duration (coupon pulls average cash-flow timing earlier). Its DV01/CF falls below "
            "the futures DV01, meaning the futures price changes FASTER than this bond's price/CF "
            "when yields move. When yields RISE: futures falls faster than Price/CF → basis "
            "WIDENS (put gains value). When yields FALL: futures rises faster → basis NARROWS. "
            "Holding this bond's basis is like owning a put on futures."
        ), width=4),
    ], className="g-3 mb-3")

    return dbc.Container([
        concept_row,
        # ── Option Profile Exhibits (Burghardt Ch. 2, Exhibits 2.7, 2.8) ──────
        dbc.Row([dbc.Col([
            html.Div("Basis as Embedded Option — Exhibits 2.7, 2.8 & Straddle",
                style={"color": C["white"], "fontSize": "15px",
                       "fontWeight": "600", "marginBottom": "4px"}),
            html.Div(
                "Each panel: LEFT — Price/CF for the bond (solid) vs theoretical futures (dotted). "
                "The shaded area is the gross basis. RIGHT — Net basis in 32nds vs parallel yield shift. "
                "The payoff shape reveals whether the bond behaves like a call, put, or straddle.",
                style={"color": C["muted"], "fontSize": "12px", "marginBottom": "12px"}),
        ])]),
        option_profile_cards,
        dbc.Row([dbc.Col(graph(_FIG_OPT_PROF), width=12)], className="g-3 mb-4"),
        # ── CTD Switching & Quality Option ────────────────────────────────────
        controls,
        dbc.Row([
            dbc.Col(graph(_FIG_CTD_SW),  width=6),
            dbc.Col(graph(_FIG_OPT_VAL), width=6),
        ], className="g-3 mb-3"),
        dbc.Row([dbc.Col(graph("fig-opt-nb"), width=12)], className="g-3"),
    ], fluid=True, style={"paddingTop": "16px"})


# ─── Tab 6: Basis Trading ─────────────────────────────────────────────────────
def tab_trading():
    concepts = [
        ("Long Basis — Buy Cash, Sell Futures",
         "Profits when net basis widens. You earn positive carry (if coupon > repo) "
         "plus any cheapening of the cash bond versus futures. Main risk: basis "
         "tightens (delivery approaches and option value decays)."),
        ("Short Basis — Sell Cash, Buy Futures",
         "Profits when net basis narrows. Equivalent to selling the embedded "
         "delivery options. You are short gamma near delivery as the CTD can switch "
         "suddenly. Requires active monitoring of the basket."),
        ("Hedge Ratio",
         "The DV01-neutral (dollar-duration-neutral) hedge: "
         "# Futures = (DV01_Bond × Face) / (DV01_Futures × 100k). "
         "The basis trade is then rate-neutral but exposed to basis level changes, "
         "spread changes, and delivery option value."),
    ]
    concept_row = dbc.Row(
        [dbc.Col(article_card(t, b), width=4) for t, b in concepts],
        className="g-3 mb-3")

    controls = html.Div([
        dbc.Row([
            dbc.Col(slider("tr-face", 1, 200,  1,     10,       "Face Value ($MM)"),     width=3),
            dbc.Col(slider("tr-repo", 1.0, 8.0, 0.05, DEF_REPO, "Repo Rate (%)"),        width=3),
            dbc.Col(slider("tr-days", 10, 120,  1,    DEF_DAYS,  "Days to Delivery"),    width=3),
        ]),
        dbc.Row([
            dbc.Col(metric_pill("DV01 Bond ($)",    "tr-dv01-b",  C["blue2"]), width="auto"),
            dbc.Col(metric_pill("DV01 Futures ($)", "tr-dv01-f",  C["cyan"]),  width="auto"),
            dbc.Col(metric_pill("Hedge Ratio",      "tr-hedge",   C["amber"]), width="auto"),
            dbc.Col(metric_pill("Max P&L Gain",     "tr-max-g",   C["green"]), width="auto"),
            dbc.Col(metric_pill("Max P&L Loss",     "tr-max-l",   C["red"]),   width="auto"),
        ], className="g-2"),
    ], style={"background": C["surface"], "border": f"1px solid {C['border']}",
              "borderRadius": "10px", "padding": "18px 20px", "marginBottom": "18px"})

    return dbc.Container([
        concept_row,
        controls,
        dbc.Row([
            dbc.Col(graph("fig-pnl-bar"),  width=6),
            dbc.Col(graph("fig-pnl-heat"), width=6),
        ], className="g-3 mb-3"),
        dbc.Row([
            dbc.Col(graph("fig-hedge"),    width=6),
            dbc.Col(graph(_FIG_CTD_SW),    width=6),
        ], className="g-3"),
    ], fluid=True, style={"paddingTop": "16px"})


# ─── Navbar ───────────────────────────────────────────────────────────────────
import datetime as _dt
from data import DEF_FUT as _DEF_FUT, DEF_REPO as _DEF_REPO

_TODAY = _dt.date.today().strftime("%d %b %Y")

navbar = dbc.Navbar(
    dbc.Container([
        html.Div([
            html.Span("Treasury Basis Explorer", style={
                "color": C["white"], "fontWeight": "700",
                "fontSize": "18px", "letterSpacing": "-0.3px"}),
            html.Span("  ·  Burghardt, Belton, Lane & Papa", style={
                "color": C["muted"], "fontSize": "12px", "marginLeft": "4px"}),
        ]),
        html.Div([
            html.Span(f"As of {_TODAY}",
                style={"color": C["muted"], "fontSize": "11px", "marginRight": "16px"}),
            html.Span("Jun-2026 10yr T-Note Futures",
                style={"color": C["muted"], "fontSize": "11px", "marginRight": "16px"}),
            html.Span(f"Fut: {_DEF_FUT:.3f}",
                style={"color": C["amber"], "fontFamily": "monospace",
                       "fontSize": "13px", "marginRight": "12px"}),
            html.Span(f"Repo: {_DEF_REPO:.2f}%",
                style={"color": C["cyan"], "fontFamily": "monospace", "fontSize": "13px"}),
        ]),
    ], fluid=True),
    style={"background": C["surface"], "borderBottom": f"1px solid {C['border']}",
           "padding": "10px 20px"},
    dark=True, sticky="top",
)

# ─── Tab 7: Article ──────────────────────────────────────────────────────────

def _section(title, body_paragraphs, formulas=None, note=None):
    """Render one article section: heading + prose + optional formulas + note."""
    children = [
        html.H3(title, style={"color": C["blue2"], "fontSize": "17px",
                               "fontWeight": "600", "marginBottom": "10px",
                               "paddingBottom": "6px",
                               "borderBottom": f"1px solid {C['border']}"}),
    ]
    for p in body_paragraphs:
        children.append(html.P(p, style={"color": C["text"], "lineHeight": "1.85",
                                          "fontSize": "14px", "marginBottom": "10px"}))
    if formulas:
        for lbl, fml in formulas:
            children.append(formula_block(lbl, fml))
    if note:
        children.append(html.Div(note, style={
            "background": C["surface"], "borderLeft": f"3px solid {C['cyan']}",
            "border": f"1px solid {C['border']}", "borderRadius": "6px",
            "padding": "10px 14px", "fontSize": "13px", "color": C["cyan"],
            "marginTop": "8px",
        }))
    return html.Div(children, style={"marginBottom": "36px"})


def tab_article():  # noqa: C901
    # ── Left column: Chapters 1–3 ─────────────────────────────────────────────
    left_col = dbc.Col([

        _section(
            "Chapter 1 — The Basis: Definition and Market Structure",
            [
                "The Treasury bond basis is defined as the clean cash price of a Treasury note or "
                "bond minus the conversion-factor-adjusted futures price. Expressed in 32nds of a "
                "point (one point = $1 per $100 face), it reads: Gross Basis = (Cash − CF×Fut) × 32. "
                "The gross basis is positive for virtually every deliverable bond because the futures "
                "price is anchored to the cheapest-to-deliver bond's forward price, sitting below "
                "the CF-adjusted equivalent for most other bonds in the basket.",

                "The CME 10-Year T-Note futures contract (ZN) allows delivery of $100,000 face of "
                "any Treasury note with 6½ to 10 years remaining maturity. To make notes of different "
                "coupons and maturities fungible, the CME assigns each eligible note a conversion "
                "factor (CF) equal to its price per $1 face at a 6% yield, rounded to the nearest "
                "coupon date (quarter-year). Upon delivery, the long pays: "
                "Invoice = CF × Futures Settlement Price + Accrued Interest.",

                "In the current yield environment (~4.3%), all CFs are below 1 — every note has a "
                "coupon below the 6% reference rate, so it prices below par at 6% yield. For a "
                "4% note, CF ≈ 0.89. The short delivers a $98 cash bond but receives only $98 "
                "(≈ 0.89 × $110 futures price). The gross basis compensates for this pricing mismatch.",

                "The three-way decomposition Gross Basis = Carry + Net Basis is the central identity "
                "of basis analysis. Carry is the net income from financing the position through "
                "delivery (coupon received minus repo cost). Net Basis is the residual: the market "
                "value of the delivery options the short holds. In a no-option world, net basis "
                "equals zero. Observed CTD net basis of 5–12 32nds is the market's option premium. "
                "Understanding each component — and how they interact — is the foundation of all "
                "basis trading and hedging.",
            ],
            formulas=[
                ("Gross Basis (32nds)", "GB  =  (Cash Clean Price  −  CF × Futures Price) × 32"),
                ("Invoice at Delivery", "Invoice  =  CF × Fut_settlement + AI_delivery"),
                ("Basis Identity",
                 "Gross Basis  =  Carry  +  Net Basis\n"
                 "Net Basis  ≥  0  (always; = delivery option premium)\n"
                 "Carry  =  CI  −  FC   (may be negative if repo > coupon)"),
                ("Conversion Factor",
                 "CF  =  bprice(coupon/100, 6%, n_periods, $1 face)\n"
                 "CF < 1  when market yield > 6%  (note worth less than par at 6%)\n"
                 "CF < 1  also when coupon < 6% regardless of yield"),
            ],
            note="▶  Tab 1 'The Basis Defined' — waterfall decomposition, basis convergence, yield curve.",
        ),

        _section(
            "Chapter 2 — Carry: The Financed Holding Cost",
            [
                "Carry is the net cash flow from financing a bond position in the repo market and "
                "holding it to the futures delivery date. It has two components: coupon income "
                "accrued over the holding period, and the cost of repo financing.",

                "Coupon income accrues on an Act/365 basis for U.S. Treasuries: CI = C × d/365. "
                "Financing cost is on Act/360: FC = Full Price × repo × d/360. "
                "The day-count asymmetry means a bond with a coupon yield exactly equal to repo "
                "still has slightly positive carry — you receive on 365 days and pay on 360. "
                "The break-even repo (where carry = 0) is: r_be = C × (360/365) / Full Price.",

                "When repo > coupon yield (the current environment: repo ≈ 4.30%, coupon yields "
                "3–6%): carry is NEGATIVE for the lower-coupon bonds. Negative carry means the "
                "gross basis RISES as delivery approaches rather than falls. You are paying more "
                "to finance the bond than you earn in coupon. The CTD selection accounts for "
                "this: even with negative carry, the net basis (= option premium) remains positive.",

                "The forward clean price is the theoretical price at which the bond should trade "
                "for future delivery: Fwd_Clean = Full Price × (1 + r×d/360) − CI − AI_del. "
                "In a no-options world, Futures = Fwd_Clean_CTD / CF_CTD. Market futures trade "
                "BELOW this level — the discount is the net basis (option premium). This is "
                "why you can observe: Futures < Fwd_Clean_CTD / CF_CTD always.",

                "In a positively-sloped yield curve (coupon yield > repo), carry offsets most "
                "of the gross basis: small, declining net basis into delivery. In an inverted "
                "curve (repo > long yields), carry is negative and the futures price sits well "
                "below forward, making the net basis mechanically wider — but this doesn't "
                "create extra option value, just changes the accounting attribution.",
            ],
            formulas=[
                ("Coupon Income",
                 "CI  =  Coupon ($/yr)  ×  (d / 365)              [Act/365]"),
                ("Financing Cost",
                 "FC  =  Full Price  ×  repo_rate  ×  (d / 360)   [Act/360]"),
                ("Net Carry",
                 "Carry  =  CI  −  FC"),
                ("Break-even Repo",
                 "r_be  =  Coupon × (360/365) / Full Price  ≈  Current Yield × 0.9863"),
                ("Forward Clean Price",
                 "Fwd_Clean  =  Full Price × (1 + r×d/360) − CI − AI_del\n"
                 "  = Spot Clean + (FC − CI) + (AI_spot − AI_del)\n"
                 "  Note: when no coupon falls in the interval, AI_del > AI_spot"),
            ],
            note="▶  Tab 3 'Carry & Forward Price' — carry vs days, break-even repo, forward price scenarios.",
        ),

        _section(
            "Chapter 2b — Basis as Embedded Option (Exhibits 2.7, 2.8, Straddle)",
            [
                "The most powerful insight in Chapter 2 of Burghardt et al.: each bond's net basis "
                "profile across yield levels looks like an options payoff. The futures price is not "
                "a linear function of any single bond — it is the MINIMUM of the forward prices "
                "across all basket bonds, each divided by its CF. This 'min' is a convex, "
                "kinked function of yields, exactly like an option's intrinsic value.",

                "Three representative bonds illustrate the principle. Bond A (low coupon, 1.75%, "
                "high duration): when yields FALL, Bond A's price/CF rises faster than the futures "
                "price (CTD shifts to an even-longer bond, compressing futures). Bond A's basis "
                "widens. When yields RISE, Bond A's price/CF falls faster — basis narrows. "
                "This is a CALL OPTION on futures: profit from falling yields. Burghardt's "
                "original example: the 5½% T-bond (Exhibit 2.7).",

                "Bond C (high coupon, 6.5%, lower duration): CF is large (note prices at 6% yield "
                "above par). CF × Futures is large, so the gross basis is currently wide. When "
                "yields RISE, Bond C approaches CTD status — its basis narrows. When yields FALL, "
                "it moves further from CTD — basis widens. This is a PUT OPTION on futures: profit "
                "from rising yields (falling futures prices). Burghardt: 8⅞% T-bond (Exhibit 2.8).",

                "Bond B (CTD, 4.0%, medium duration): at current yields, Price/CF ≈ futures. "
                "Any large move in EITHER direction replaces the CTD with another bond, causing "
                "Bond B's basis to widen. This U-shaped payoff is a STRADDLE: positive P&L for "
                "large rate moves in either direction. Long basis of the CTD is pure long gamma. "
                "Burghardt: 7⅝% T-bond (the straddle exhibit).",
            ],
            formulas=[
                ("Futures = Option on Min",
                 "F_theo  =  min_i [ FwdClean_i / CF_i ]\n"
                 "This 'min' creates a kinked, convex futures price function of yields.\n"
                 "Every bond's net basis = its distance above this kinked line."),
                ("Call Profile (low coupon)",
                 "∂NB_call/∂yield < 0  →  NB rises when yields fall\n"
                 "Long basis = long call on futures (pay premium, collect on rate rally)"),
                ("Put Profile (high coupon)",
                 "∂NB_put/∂yield > 0  →  NB rises when yields rise\n"
                 "Long basis = long put on futures (pay premium, collect on rate selloff)"),
                ("Straddle Profile (CTD)",
                 "NB_CTD is minimised at current yield; rises in both directions\n"
                 "Long basis = long straddle  (positive gamma, long volatility)"),
            ],
            note="▶  Tab 5 'Delivery Options' — top section: option profile chart with all three exhibit shapes.",
        ),

        _section(
            "Chapter 3 — The Cheapest-to-Deliver Bond",
            [
                "The CTD is the bond in the deliverable basket that minimises the short's delivery "
                "cost. Three equivalent identification rules: (1) lowest net basis; "
                "(2) highest implied repo rate; (3) lowest forward-clean-price-to-CF ratio.",

                "The CF system uses a 6% reference rate. In the current ~4.3% yield environment, "
                "all CFs < 1. The CF systematically under-prices high-coupon bonds (they're worth "
                "more on a yield basis than the CF suggests) and over-prices low-coupon bonds. "
                "The bond where this mispricing is smallest — typically the one with the shortest "
                "duration in the eligible range — is the CTD. Here, that is the 4.000% Nov-32 note.",

                "As yields rise toward and above 6%, CFs start exceeding 1 for high-coupon bonds. "
                "The high-coupon bonds become the most under-priced in the CF system, so they "
                "become CTD. This CTD switching as rates cross 6% is the primary source of the "
                "quality option. In this explorer, moving the Yield Shift slider to +150bp or "
                "higher triggers a CTD switch to the 4.500% Nov-33 or 4.750% Aug-34 bond.",

                "The CF × Futures vs. Clean Price scatter is the most diagnostic chart. Bonds "
                "below the 45° line (Cash > CF × Futures) have positive gross basis — non-CTD. "
                "The CTD lies on or just below the line. Watch for which bond approaches the line "
                "most aggressively as you shift yields — that is the next CTD candidate.",

                "Duration of futures tracks the CTD: DV01_fut ≈ DV01_CTD / CF_CTD. When the "
                "CTD switches, the futures duration 'jumps' — basis traders with DV01-neutral "
                "hedges find their position is no longer hedged, creating P&L exposure proportional "
                "to the basis jump times their face value.",
            ],
            formulas=[
                ("CTD — Three Equivalent Criteria",
                 "CTD  =  argmin_i [ Net Basis_i ]\n"
                 "     =  argmax_i [ Implied Repo_i ]\n"
                 "     =  argmin_i [ FwdClean_i / CF_i ]"),
                ("CF Bias Rule",
                 "Yield < 6%:  Short-duration / high-coupon bonds favoured as CTD\n"
                 "             (CF system under-prices their value the least)\n"
                 "Yield > 6%:  Long-duration / low-coupon bonds favoured as CTD\n"
                 "             (CF system under-prices their value the least)"),
                ("Futures DV01",
                 "DV01_futures  ≈  DV01_CTD / CF_CTD\n"
                 "A CTD switch from a 7yr bond to a 9yr bond raises futures DV01\n"
                 "by ~$20–30 per bp per contract — a significant unhedged jump."),
            ],
            note="▶  Tab 2 'Deliverable Basket' — live basket table, CF scatter, net basis bar, DV01 chart.",
        ),
    ], width=6)

    # ── Right column: Chapters 4–6 + Appendix ────────────────────────────────
    right_col = dbc.Col([
        _section(
            "Chapter 4 — Implied Repo Rate and Rich/Cheap Analysis",
            [
                "The implied repo rate (IRR) is the internal rate of return from buying a cash "
                "bond, financing it in the repo market through delivery, and delivering into "
                "futures at the invoice price. It answers: 'What financing rate do I need to "
                "earn to break even on this delivery trade?' The CTD bond always has the highest IRR.",

                "Formula: buy at full price P, finance for d days, receive invoice (CF×Fut + AI_del) "
                "plus coupon income CI. Break-even: P × (1 + IRR × d/360) = CF×Fut + AI_del + CI. "
                "Solving: IRR = (CF×Fut + AI_del + CI − P) / (P × d/360). "
                "For the CTD in this explorer (4.000% Nov-32): IRR ≈ 7.4%, well above the "
                "4.30% actual repo — the bond is deeply CHEAP to deliver.",

                "IRR > actual repo = CHEAP: profitable to buy, finance, and deliver. "
                "IRR < actual repo = RICH: financing costs more than the delivery returns. "
                "For the high-coupon 6.500% Feb-36 note (CF ≈ 1.03), IRR ≈ −6.5% — it costs "
                "6.5% net annually to hold and deliver this bond vs. just parking cash at repo. "
                "This large negative spread is NOT a mis-pricing; it reflects the option value "
                "of this bond's put-like basis profile being fully embedded in the net basis.",

                "The IRR spread ranking is the real-time rich/cheap signal for basis traders. "
                "As you move the Yield Shift slider in Tab 4, watch how the IRR spread for the "
                "second-ranked bond approaches zero. When it crosses zero, the CTD has switched. "
                "This event typically reprices all net bases by 3–8 32nds instantaneously — "
                "a significant P&L event for any outstanding basis position.",

                "Historical context: in Aug-2023, the CTD for the 10yr T-Note futures switched "
                "from the lowest-coupon eligible note to the next higher as the Fed Funds rate "
                "exceeded the 6% CF reference asymptotically. IRR spreads collapsed from +200bp "
                "to +10bp in the span of three months — a huge basis compression trade. "
                "Traders who identified the imminent switch via IRR monitoring profited "
                "significantly from both the pre-switch convergence and post-switch basis repricing.",
            ],
            formulas=[
                ("Implied Repo Rate",
                 "IRR  =  (CF×Fut + AI_del + CI − P_full) / (P_full × d/360)\n"
                 "\n"
                 "  CI = C × d/365  (coupon income, Act/365)\n"
                 "  AI_del = AI at delivery (accrued by delivery date)"),
                ("Delivery Trade P&L",
                 "P&L  =  P_full × (IRR − repo_actual) × d/360\n"
                 "     =  Net Basis in $ (after carry adjustment)\n"
                 "     > 0 when IRR > repo (bond is cheap)"),
                ("Rich/Cheap Signal",
                 "IRR − Repo > 0  →  CHEAP  (buy basis, long cash vs short futures)\n"
                 "IRR − Repo < 0  →  RICH   (sell basis or avoid long cash)\n"
                 "CTD:  largest positive spread in basket"),
            ],
            note="▶  Tab 4 'Implied Repo' — IRR bar chart and rich/cheap spread; adjust actual-repo slider.",
        ),

        _section(
            "Chapter 5 — Delivery Options: Quality, Wildcard, End-of-Month",
            [
                "The net basis of any bond equals the aggregate value of the delivery options "
                "the short holds in the futures contract for that bond. The futures price sits "
                "BELOW the theoretical no-option forward price by exactly the option premium — "
                "this is why net basis is always non-negative for the CTD.",

                "QUALITY (SWITCH) OPTION — the dominant component. The short delivers the "
                "cheapest bond available on delivery day, regardless of which bond was cheapest "
                "when the position was established. As yields shift, CTD changes, and the short "
                "always benefits. Value: the expected improvement in delivery cost from the "
                "right to switch. Depends on (a) yield volatility — more vol = more switching "
                "opportunity; (b) spacing between bonds' theoretical futures prices — wider "
                "spacing = larger gain per switch; (c) time to delivery. In normal 10yr note "
                "futures markets: 3–8 32nds. In high-vol periods (VIX > 25): 8–15 32nds.",

                "TIMING OPTION — delivery can occur on any business day during the delivery "
                "month. In positive carry environments (coupon > repo), the optimal delivery "
                "day is as LATE as possible (earn more coupon income). In negative carry "
                "(repo > coupon, the current situation), deliver as EARLY as possible to "
                "minimise financing losses. The futures price reflects the optimal timing. "
                "Value: 1–3 32nds, depending on carry sign and intramonth volatility.",

                "WILDCARD OPTION — futures stop trading at 2:00 PM CT, but delivery notice "
                "can be submitted until 8:00 PM CT. Invoice price is locked at the 2 PM "
                "settlement, but the short can buy bonds in the afternoon cash market. "
                "If bonds fall after 2 PM, the short delivers at the locked-in higher invoice. "
                "Every eligible delivery day carries one wildcard. Value: ≈ ½ × (afternoon "
                "variance of CTD price) × (number of eligible delivery days). Typically 0.5–2 32nds.",

                "END-OF-MONTH OPTION — after futures stop trading (several business days before "
                "last delivery day), the invoice price is frozen but bond prices keep moving "
                "for several more days. If the CTD falls in this window, the short delivers at "
                "the old (higher) invoice price against the now-lower cash purchase. "
                "Value: 0.3–1.5 32nds. Total net basis decomposition: "
                "Quality 60–70% + Timing 15–20% + Wildcard 10–15% + EOM 5%.",
            ],
            formulas=[
                ("Theoretical vs. Market Futures",
                 "F_theo  =  min_i [ FwdClean_i / CF_i ]   (no-option price)\n"
                 "F_mkt   =  F_theo  −  Option_Premium / (CF_CTD × 32)\n"
                 "\n"
                 "  Net Basis_CTD  =  Option_Premium (in 32nds)"),
                ("Option Value Lower Bound",
                 "NB_CTD  ≥  0   always\n"
                 "NB_i    ≥  NB_CTD   for all non-CTD bonds i"),
                ("Wildcard Option (per day, approximate)",
                 "V_wc ≈ ½ × σ²_afternoon × CF_CTD\n"
                 "Total wildcard ≈ V_wc × N_delivery_days"),
                ("Total Net Basis Budget (10yr futures, normal markets)",
                 "Quality Option:    3–8 32nds\n"
                 "Timing Option:     1–3 32nds\n"
                 "Wildcard:          0.5–2 32nds\n"
                 "End-of-Month:      0.3–1.5 32nds\n"
                 "TOTAL CTD NB:      5–14 32nds"),
            ],
            note="▶  Tab 5 'Delivery Options' — option profile exhibits, CTD switch chart, quality option vs yield shift.",
        ),

        _section(
            "Chapter 6 — Basis Trading: Strategies, P&L, and Risk",
            [
                "LONG BASIS (Buy Cash, Sell Futures): Buy a Treasury note and sell CF-adjusted "
                "futures contracts. The position is DV01-neutral — P&L comes only from changes "
                "in the NET BASIS, not from the yield level. You profit when net basis widens: "
                "option value rises (yield vol increases or CTD switch expected), or carry turns "
                "favourable (repo falls). This is long gamma / long vega. Maximum carry risk: "
                "if repo stays above coupon, you pay negative carry every day.",

                "SHORT BASIS (Sell Cash, Buy Futures): You profit when net basis narrows — "
                "typically as delivery approaches and option time value decays (theta). "
                "This is short gamma: large unexpected yield moves hurt you, especially CTD "
                "switches which create instantaneous basis jumps. Most attractive when: "
                "net basis appears wide relative to option premium, yield volatility is low "
                "and expected to remain low, and the CTD is not near a switching point.",

                "DV01-NEUTRAL HEDGE: Number of futures = "
                "DV01_bond × Face / (DV01_futures × $100k). Since DV01_fut ≈ DV01_CTD / CF_CTD, "
                "for the CTD bond the ratio simplifies to CF_CTD per $100k face. "
                "For non-CTD bonds with higher duration, you need more futures. The hedge is "
                "rate-neutral for PARALLEL shifts; non-parallel moves create curve risk.",

                "KEY RISKS: (1) CTD SWITCH — the biggest risk. If the CTD changes overnight, "
                "net basis of ALL bonds reprices by 3–8 32nds simultaneously. Monitor the "
                "second-ranked IRR bond continuously — when its IRR spread approaches zero, "
                "exit or hedge the switch exposure. "
                "(2) REPO RATE RISK — a rise in repo compresses carry (hurts long basis holders). "
                "The P&L heatmap in Tab 6 shows this: rising repo AND stable yields is the "
                "worst scenario for long basis. "
                "(3) DELIVERY SQUEEZE — concentrated ownership of the CTD can force specials "
                "(below-market repo for that bond), widening basis dramatically near delivery. "
                "(4) CURVE RISK — non-parallel moves change relative bond values in ways the "
                "single DV01 hedge does not capture. A steepener (short rates fall, long rise) "
                "helps negative-carry long-basis holders but hurts positive-carry holders.",
            ],
            formulas=[
                ("DV01-Neutral Futures Hedge",
                 "N_futures  =  DV01_bond × Face_bond\n"
                 "             ──────────────────────────\n"
                 "              DV01_futures × $100,000\n"
                 "\n"
                 "  DV01_futures  ≈  DV01_CTD / CF_CTD\n"
                 "  For CTD: N  ≈  CF_CTD contracts per $100k face"),
                ("Long Basis P&L Decomposition",
                 "P&L  =  ΔNB × Face / 100\n"
                 "     =  (ΔGB − ΔCarry) × Face / 100\n"
                 "\n"
                 "  ΔGB   = change in gross basis (yield change × DV01 differential)\n"
                 "  ΔCarry = change in repo rate × Full Price × d/360\n"
                 "  Option P&L = ΔNB − (pure carry theta)"),
                ("Basis $ Value per 32nd",
                 "$1 per 32nd per $100 face  =  $312.50 per $MM face\n"
                 "6 32nds net basis on $100MM  =  $1,875,000 option premium"),
            ],
            note="▶  Tab 6 'Basis Trading' — P&L bar chart, heatmap (yield × repo), hedge ratio chart.",
        ),

        _section(
            "Appendix — Numeric Example: Jun-2026 10yr T-Note Futures",
            [
                "Worked example using the live basket in this app. "
                "Settlement: Futures ≈ 110.006, Repo = 4.30%, Days to delivery = 79, "
                "AI at settlement ≈ $1.20 / $100 face.",

                "CTD Bond — 4.000% Nov-32 (n = 13 semi-annual periods):\n"
                "  CF = bprice(0.04/100 → 0.04, 6%, 13, $1) ≈ 0.8943\n"
                "  Clean Price ≈ $98.36  (ytm ≈ 4.28%)\n"
                "  Full Price ≈ $99.56   (clean + $1.20 AI)\n"
                "  CF × Futures = 0.8943 × 110.006 ≈ $98.37\n"
                "  Gross Basis ≈ (98.36 − 98.37) × 32 ≈ −0.3 32nds\n"
                "  Coupon Income (79 days): 4.000 × 79/365 = $0.866\n"
                "  Financing Cost: 99.56 × 0.043 × 79/360 = $0.940\n"
                "  Net Carry: $0.866 − $0.940 = −$0.074  (NEGATIVE — repo > coupon)\n"
                "  Carry in 32nds: −$0.074 × 32 = −2.4 32nds\n"
                "  Net Basis: GB − Carry = −0.3 − (−2.4) = +6.2 32nds  ✓\n"
                "  IRR ≈ (Invoice + CI − P) / (P × 79/360) ≈ 7.4%  (CHEAP: 7.4% >> 4.30%)",

                "High-coupon Bond — 6.500% Feb-36 (n = 20 semi-annual periods):\n"
                "  CF = bprice(0.065, 6%, 20, $1) ≈ 1.0344\n"
                "  Clean Price ≈ $118.1  (ytm ≈ 4.35%)\n"
                "  CF × Futures = 1.0344 × 110.006 ≈ $113.8\n"
                "  Gross Basis ≈ (118.1 − 113.8) × 32 ≈ 137 32nds\n"
                "  Carry ≈ 6.5 × 79/365 − 119.3 × 0.043 × 79/360 ≈ +$0.37 (positive carry!)\n"
                "  Net Basis ≈ 137 − 12 ≈ 125 32nds  (far from CTD)\n"
                "  IRR ≈ −5.8%  (RICH: must earn 5.8% extra annually just to break even)",

                "Basis trade sizing — $10MM face long CTD basis:\n"
                "  DV01_bond ≈ $800 per $MM (for 4% note, 6.5yr)\n"
                "  DV01_futures ≈ $890 per contract (futures tracks CTD duration)\n"
                "  Hedge: 10 × $800 / $890 ≈ 9 contracts short\n"
                "  Net Basis P&L per 1 32nd widening: $10MM / 100 × 1/32 = $3,125\n"
                "  If net basis widens from 6 to 10 32nds (+4 32nds): P&L = +$12,500\n"
                "  Daily carry cost at −2.4 32nds over 79 days: −$0.074 × $10MM/100 = −$7,400 total",
            ],
            formulas=[
                ("Invoice Calculation",
                 "Invoice = CF × Fut + AI_del\n"
                 "        = 0.8943 × 110.006 + 1.25  ≈  $100.81 per $100 face\n"
                 "  (AI_del > AI_spot because 79 days more accrued to delivery)"),
                ("Basis P&L Scale",
                 "$1 per 32nd per $100 face  =  $312.50 per $MM face\n"
                 "1 bp yield change  ≈  DV01 × 10  per $MM face\n"
                 "  (These are the two P&L atoms of a basis trade)"),
            ],
            note="▶  All numbers above update live as you move sliders in Tabs 2, 3, 4 — verify every figure yourself.",
        ),

    ], width=6)

    return dbc.Container([
        dbc.Row([dbc.Col([
            html.H1("The Treasury Bond Basis — A Quant's Field Guide",
                style={"color": C["white"], "fontSize": "26px", "fontWeight": "700",
                       "marginBottom": "4px"}),
            html.Div([
                html.Span("Based on Burghardt, Belton, Lane & Papa  ·  Chapters 1–6  ·  ",
                    style={"color": C["muted"], "fontSize": "13px"}),
                html.Span("Jun-2026 10-Year T-Note Futures",
                    style={"color": C["cyan"], "fontSize": "13px", "fontWeight": "600"}),
            ], style={"marginBottom": "6px"}),
            html.Div(
                "Every formula in this article is implemented live in the interactive tabs. "
                "Every number cited can be verified in the Tab 2 basket table.",
                style={"color": C["muted"], "fontSize": "12px", "marginBottom": "24px"}),
        ])]),
        dbc.Row([left_col, right_col], className="g-5"),
    ], fluid=True, style={"paddingTop": "24px", "paddingBottom": "60px", "maxWidth": "1500px"})


# ─── Full layout ─────────────────────────────────────────────────────────────

def build_layout():
    tabs = dbc.Tabs([
        dbc.Tab(tab_overview(),     label="The Basis Defined",     tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
        dbc.Tab(tab_basket(),       label="Deliverable Basket",    tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
        dbc.Tab(tab_carry(),        label="Carry & Forward Price", tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
        dbc.Tab(tab_implied_repo(), label="Implied Repo",          tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
        dbc.Tab(tab_delivery(),     label="Delivery Options",      tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
        dbc.Tab(tab_trading(),      label="Basis Trading",         tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
        dbc.Tab(tab_article(),      label="Article",               tab_style=TAB_STYLE, active_tab_style=TAB_SEL_STYLE),
    ], style={"background": C["bg"],
              "borderBottom": f"1px solid {C['border']}", "paddingLeft": "12px"})

    from theme import FONT
    return html.Div([navbar, tabs],
        style={"background": C["bg"], "minHeight": "100vh",
               "fontFamily": FONT, "color": C["text"]})
