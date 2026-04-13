"""
theme.py — Design system: colours, shared layout helpers, plot defaults
"""

FONT = "'Inter', 'Segoe UI', sans-serif"

C = dict(
    bg      = "#080c14",
    surface = "#0f1623",
    card    = "#141e2e",
    border  = "#1e2d44",
    border2 = "#253550",
    text    = "#dce8f5",
    muted   = "#637997",
    blue    = "#3b82f6",
    blue2   = "#60a5fa",
    green   = "#10b981",
    red     = "#ef4444",
    amber   = "#f59e0b",
    purple  = "#8b5cf6",
    cyan    = "#06b6d4",
    indigo  = "#6366f1",
    white   = "#f0f7ff",
)

CARD_STYLE = {
    "background": C["card"],
    "border":     f"1px solid {C['border']}",
    "borderRadius": "10px",
    "padding":    "20px",
}

CONTROLS_STYLE = {
    "background":   C["surface"],
    "border":       f"1px solid {C['border']}",
    "borderRadius": "10px",
    "padding":      "18px 20px",
    "marginBottom": "18px",
}

PLOT_LAYOUT = dict(
    paper_bgcolor = C["surface"],
    plot_bgcolor  = C["card"],
    font          = dict(family=FONT, color=C["text"], size=12),
    margin        = dict(l=50, r=20, t=45, b=45),
    legend        = dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                         font=dict(color=C["text"])),
    xaxis         = dict(gridcolor=C["border"], linecolor=C["border"],
                         zerolinecolor=C["border2"]),
    yaxis         = dict(gridcolor=C["border"], linecolor=C["border"],
                         zerolinecolor=C["border2"]),
    hoverlabel    = dict(bgcolor=C["surface"], font=dict(color=C["white"],
                         family=FONT)),
)

TABLE_STYLES = dict(
    style_table  = {"overflowX": "auto"},
    style_header = {
        "backgroundColor": C["surface"], "color": C["muted"],
        "fontWeight": "600", "fontSize": "11px",
        "textTransform": "uppercase", "border": f"1px solid {C['border']}",
    },
    style_cell   = {
        "backgroundColor": C["card"], "color": C["text"],
        "border": f"1px solid {C['border']}", "fontSize": "12px",
        "fontFamily": "monospace", "padding": "8px 10px",
    },
)

TAB_STYLE = dict(
    background    = C["surface"],
    color         = C["muted"],
    border        = "none",
    borderBottom  = "2px solid transparent",
    padding       = "10px 20px",
    fontSize      = "13px",
    fontWeight    = "500",
)
TAB_SEL_STYLE = {**TAB_STYLE,
    "color":       C["white"],
    "borderBottom": f"2px solid {C['blue']}",
    "background":  C["bg"],
}
