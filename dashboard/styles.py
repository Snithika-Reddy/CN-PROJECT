"""NetIntel Custom UI Design System and Theme Styles.

Strictly incorporates the 4 user-provided palette colors:
- Color 1 (Mint Ice):        #DFFCF9
- Color 2 (Ice Periwinkle):  #CBDFFC
- Color 3 (Lavender Mist):   #C4BFF0
- Color 4 (Pastel Orchid):   #CDAAEA

With high-contrast obsidian-indigo typography (#15112B, #3B3356) to ensure
100% crystal-clear readability across all cards, buttons, charts, and metrics.
"""

import plotly.graph_objects as go


def get_custom_css() -> str:
    """Return injectible CSS stylesheet for Streamlit."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        /* Exact 4 Palette Colors */
        --palette-mint:     #DFFCF9;
        --palette-blue:     #CBDFFC;
        --palette-lavender: #C4BFF0;
        --palette-orchid:   #CDAAEA;

        /* Derived Surfaces & Borders */
        --app-bg:           linear-gradient(135deg, #DFFCF9 0%, #EBF4FE 45%, #CBDFFC 100%);
        --sidebar-bg:       linear-gradient(180deg, #CBDFFC 0%, #D8DCFD 40%, #C4BFF0 100%);
        --card-bg:          #FFFFFF;
        --card-glass:       rgba(255, 255, 255, 0.94);
        --card-border:      #C4BFF0;
        --card-hover:       #CDAAEA;

        /* High-Contrast Accessible Typography */
        --text-primary:     #15112B;
        --text-secondary:   #3B3356;
        --text-muted:       #5E547E;
        --text-accent:      #6A2D94;

        /* Accents & Glows */
        --glow-orchid:      rgba(205, 170, 234, 0.35);
        --glow-mint:        rgba(223, 252, 249, 0.35);
        --glow-lavender:    rgba(196, 191, 240, 0.35);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-primary);
    }

    /* Main App Background */
    .stApp {
        background: var(--app-bg) !important;
        background-attachment: fixed !important;
        color: var(--text-primary) !important;
    }

    /* Streamlit Native Header */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: none !important;
    }

    /* Streamlit Main Container Spacing */
    .main .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 2.5rem !important;
    }

    /* Sidebar Background & Borders */
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 2px solid var(--card-border) !important;
        box-shadow: 2px 0 16px rgba(196, 191, 240, 0.3) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* Sidebar Navigation Category Labels */
    .nav-category {
        font-size: 11px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        color: #2D1D4F !important;
        background: rgba(255, 255, 255, 0.75) !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        margin-top: 14px !important;
        margin-bottom: 8px !important;
        display: inline-block !important;
        border-left: 3px solid #CDAAEA !important;
        box-shadow: 0 1px 4px rgba(196, 191, 240, 0.25) !important;
    }

    /* Navigation & General Buttons */
    .stButton > button {
        border-radius: 9px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 14px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1.5px solid #C4BFF0 !important;
        background: #FFFFFF !important;
        color: #241A45 !important;
        text-align: left !important;
        box-shadow: 0 2px 6px rgba(196, 191, 240, 0.25) !important;
    }

    .stButton > button p,
    .stButton > button span,
    .stButton > button div {
        color: #241A45 !important;
        font-weight: 700 !important;
    }

    .stButton > button:hover {
        border-color: #CDAAEA !important;
        background: #DFFCF9 !important; /* Mint Ice */
        color: #15112B !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(205, 170, 234, 0.4) !important;
    }

    .stButton > button:hover p,
    .stButton > button:hover span {
        color: #15112B !important;
    }

    /* Active / Primary Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #CDAAEA 0%, #C4BFF0 50%, #CBDFFC 100%) !important;
        border: 1.5px solid #CDAAEA !important;
        color: #150F2E !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 16px rgba(205, 170, 234, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: #150F2E !important;
        font-weight: 800 !important;
    }

    /* Top Navigation Header Banner */
    .netintel-header {
        background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FE 50%, #CBDFFC 100%) !important;
        border: 2px solid #C4BFF0 !important;
        border-radius: 14px !important;
        padding: 20px 26px !important;
        margin-bottom: 22px !important;
        box-shadow: 0 8px 30px rgba(196, 191, 240, 0.35) !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .netintel-header::after {
        content: '' !important;
        position: absolute !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 4px !important;
        background: linear-gradient(90deg, #DFFCF9 0%, #CBDFFC 33%, #C4BFF0 66%, #CDAAEA 100%) !important;
    }

    .netintel-title {
        font-size: 26px !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #1C1236 0%, #3D2566 50%, #162E5C 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin: 0 !important;
        letter-spacing: -0.5px !important;
    }

    .netintel-subtitle {
        font-size: 13px !important;
        color: #4C3C6E !important;
        margin-top: 5px !important;
        font-weight: 600 !important;
    }

    /* Metric KPI Cards */
    .kpi-card {
        background: #FFFFFF !important;
        border: 1.5px solid #C4BFF0 !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        box-shadow: 0 4px 20px rgba(196, 191, 240, 0.28) !important;
        transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease !important;
        margin-bottom: 14px !important;
        position: relative !important;
    }

    .kpi-card:hover {
        transform: translateY(-2px) !important;
        border-color: #CDAAEA !important;
        box-shadow: 0 8px 28px rgba(205, 170, 234, 0.4) !important;
    }

    .kpi-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        color: #4C3C6E !important;
        margin-bottom: 6px !important;
    }

    .kpi-value {
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #15112B !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: -0.5px !important;
    }

    .kpi-subtext {
        font-size: 12px !important;
        color: #554A78 !important;
        margin-top: 5px !important;
        font-weight: 500 !important;
    }

    /* Info & Alert Callout Banners */
    .palette-banner {
        background: #FFFFFF !important;
        border: 1.5px solid #C4BFF0 !important;
        border-left: 4px solid #CDAAEA !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 2px 10px rgba(196, 191, 240, 0.2) !important;
        color: #15112B !important;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block !important;
        padding: 5px 12px !important;
        border-radius: 20px !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        letter-spacing: 0.6px !important;
        text-transform: uppercase !important;
    }

    .badge-live {
        background: #DFFCF9 !important;
        color: #064E46 !important;
        border: 1.5px solid #63D0C2 !important;
        box-shadow: 0 0 10px rgba(99, 208, 194, 0.3) !important;
    }

    .badge-warning {
        background: #FFF4E5 !important;
        color: #8A4802 !important;
        border: 1.5px solid #F3A638 !important;
        box-shadow: 0 0 10px rgba(243, 166, 56, 0.25) !important;
    }

    .badge-critical {
        background: #FDE8EC !important;
        color: #9A1C2E !important;
        border: 1.5px solid #F56C6C !important;
    }

    .badge-simulation {
        background: #CBDFFC !important;
        color: #143566 !important;
        border: 1.5px dashed #7EAFF2 !important;
    }

    /* Section Headers */
    .section-title {
        color: #1F153B !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        margin-top: 18px !important;
        margin-bottom: 12px !important;
        border-bottom: 1.5px solid #C4BFF0 !important;
        padding-bottom: 8px !important;
        letter-spacing: 0.3px !important;
        position: relative !important;
    }

    .section-title::after {
        content: '' !important;
        position: absolute !important;
        bottom: -1.5px !important;
        left: 0 !important;
        width: 60px !important;
        height: 3px !important;
        background: linear-gradient(90deg, #CDAAEA, #CBDFFC) !important;
    }

    /* Timeline Component */
    .timeline-item {
        border-left: 2px solid #CDAAEA !important;
        padding-left: 16px !important;
        margin-left: 8px !important;
        margin-bottom: 16px !important;
        position: relative !important;
    }

    .timeline-item::before {
        content: '' !important;
        position: absolute !important;
        left: -6px !important;
        top: 4px !important;
        width: 10px !important;
        height: 10px !important;
        border-radius: 50% !important;
        background: #CDAAEA !important;
        box-shadow: 0 0 8px #CDAAEA !important;
    }

    /* Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        border-bottom: 2px solid #C4BFF0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid #CBDFFC !important;
        border-radius: 8px 8px 0 0 !important;
        color: #2D2350 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #150F2E !important;
        background: #DFFCF9 !important;
        border-color: #CDAAEA !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #CDAAEA 0%, #FFFFFF 100%) !important;
        border-color: #CDAAEA !important;
        color: #150F2E !important;
        border-bottom: 3px solid #CDAAEA !important;
        font-weight: 800 !important;
    }

    /* Plotly Chart Container Customization */
    .stPlotlyChart {
        background: #FFFFFF !important;
        border: 1.5px solid #C4BFF0 !important;
        border-radius: 14px !important;
        padding: 10px !important;
        box-shadow: 0 4px 20px rgba(196, 191, 240, 0.25) !important;
    }

    /* Streamlit Native Metrics */
    [data-testid="stMetricValue"] {
        color: #15112B !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #4C3C6E !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        font-size: 11px !important;
        letter-spacing: 0.8px !important;
    }

    [data-testid="stMetricDelta"] {
        color: #763B9E !important;
    }

    /* Streamlit Dataframe & Table */
    .stDataFrame, div[data-testid="stTable"] {
        background: #FFFFFF !important;
        border: 1.5px solid #C4BFF0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 12px rgba(196, 191, 240, 0.2) !important;
    }

    /* Checkboxes, Radios, Sliders */
    .stCheckbox label, .stSlider label {
        color: #15112B !important;
        font-weight: 600 !important;
    }
    </style>
    """


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """Format Plotly figure to harmonize with the 4-color palette and ensure high-contrast text."""
    fig.update_layout(
        paper_bgcolor="rgba(255, 255, 255, 0.95)",
        plot_bgcolor="rgba(223, 252, 249, 0.12)",
        font=dict(family="Inter, sans-serif", color="#15112B", size=12),
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(
            gridcolor="rgba(196, 191, 240, 0.35)",
            tickfont=dict(color="#3B3356", size=11),
            title_font=dict(color="#15112B", size=12),
        ),
        yaxis=dict(
            gridcolor="rgba(196, 191, 240, 0.35)",
            tickfont=dict(color="#3B3356", size=11),
            title_font=dict(color="#15112B", size=12),
        ),
        legend=dict(
            font=dict(color="#15112B", size=11),
            bgcolor="rgba(255, 255, 255, 0.75)",
            bordercolor="#C4BFF0",
            borderwidth=1,
        ),
    )
    return fig
