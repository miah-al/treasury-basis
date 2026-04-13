"""
app.py — Treasury Basis Explorer entry point.

Run:
    python app.py

Opens at http://localhost:8050
"""
import dash
import dash_bootstrap_components as dbc

# Build app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Treasury Basis Explorer",
    suppress_callback_exceptions=True,
)

# Set layout (imports layout module which pre-computes static figures)
from layout import build_layout
app.layout = build_layout()

# Register callbacks (must happen after layout so all component IDs exist)
from callbacks import register_callbacks
register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, port=8052, host="0.0.0.0")
