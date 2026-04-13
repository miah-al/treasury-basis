"""
components.py — Reusable Dash UI building blocks for the Treasury Basis Explorer.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc
from theme import C, FONT, CONTROLS_STYLE


def card(children, style=None, **kw):
    base = {"background": C["card"], "border": f"1px solid {C['border']}",
            "borderRadius": "10px", "padding": "20px", "height": "100%"}
    if style:
        base.update(style)
    return dbc.Card(dbc.CardBody(children), style=base, **kw)


def slider(sid, min_, max_, step, value, label):
    """Labelled slider with live value display."""
    return html.Div([
        html.Div([
            html.Span(label, style={
                "color": C["muted"], "fontSize": "11px",
                "textTransform": "uppercase", "letterSpacing": "0.06em"}),
            html.Span(id=f"{sid}-val", style={
                "color": C["blue2"], "fontSize": "12px",
                "fontFamily": "monospace", "fontWeight": "700",
                "marginLeft": "8px"}),
        ], style={"marginBottom": "4px"}),
        dcc.Slider(id=sid, min=min_, max=max_, step=step, value=value,
                   marks=None, updatemode="drag",
                   allow_direct_input=False,
                   tooltip={"always_visible": False, "placement": "bottom"}),
    ], style={"marginBottom": "14px"})


def metric_pill(label, value_id, color=C["blue2"]):
    """Small metric display card."""
    return html.Div([
        html.Div(label, style={
            "color": C["muted"], "fontSize": "10px",
            "textTransform": "uppercase", "letterSpacing": "0.08em"}),
        html.Div(id=value_id, style={
            "color": color, "fontSize": "22px",
            "fontWeight": "700", "fontFamily": "monospace"}),
    ], style={"background": C["surface"], "border": f"1px solid {C['border']}",
              "borderRadius": "8px", "padding": "12px 16px", "minWidth": "120px"})


def section_header(title, subtitle=""):
    return html.Div([
        html.Div(title, style={
            "color": C["white"], "fontSize": "15px",
            "fontWeight": "600", "marginBottom": "3px"}),
        html.Div(subtitle, style={"color": C["muted"], "fontSize": "12px"}),
    ], style={"marginBottom": "14px", "paddingBottom": "10px",
              "borderBottom": f"1px solid {C['border']}"})


def article_card(title, body):
    """Concept explanation card (article-style)."""
    return dbc.Card(dbc.CardBody([
        html.Div(title, style={"color": C["blue2"], "fontWeight": "600",
                                "fontSize": "13.5px", "marginBottom": "7px"}),
        html.Div(body, style={"color": C["text"], "fontSize": "13px",
                               "lineHeight": "1.75"}),
    ]), style={"background": C["card"], "border": f"1px solid {C['border']}",
               "borderRadius": "10px", "height": "100%"})


def formula_block(label, text):
    """Formula display block."""
    return html.Div([
        html.Div(label, style={
            "color": C["muted"], "fontSize": "11px",
            "textTransform": "uppercase", "letterSpacing": "0.07em",
            "marginBottom": "4px"}),
        html.Pre(text, style={
            "color": C["amber"], "background": C["surface"],
            "border": f"1px solid {C['border2']}",
            "borderLeft": f"3px solid {C['amber']}",
            "borderRadius": "6px", "padding": "10px",
            "fontSize": "12px", "whiteSpace": "pre-wrap",
            "margin": "0", "fontFamily": "monospace"}),
    ])


def graph(fig_or_id, height=None):
    """Wrapper to produce a dcc.Graph from a figure or string ID."""
    cfg = {"displayModeBar": True,
           "modeBarButtonsToRemove": ["lasso2d", "select2d"],
           "displaylogo": False}
    style = {"margin": "0"}
    if isinstance(fig_or_id, str):
        return dcc.Graph(id=fig_or_id, config=cfg, style=style)
    if height:
        fig_or_id.update_layout(height=height)
    return dcc.Graph(figure=fig_or_id, config=cfg, style=style)


def controls_row(*sliders_and_metrics):
    """Wrap controls and metrics in the standard control panel container."""
    return html.Div(sliders_and_metrics, style=CONTROLS_STYLE)
