"""NetIntel Custom UI Design System and Theme Styles.

Applies the specified curated palette:
- Lightest Cyan: #E3FDFD
- Soft Aqua:     #CBF1F5
- Light Teal:    #A6E3E9
- Deep Teal:     #71C9CE
Combined with modern glassmorphism, responsive KPI cards, and status badges.
"""

def get_custom_css() -> str:
    """Return injectible CSS stylesheet for Streamlit."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --ice-cyan: #E3FDFD;
        --soft-aqua: #CBF1F5;
        --light-teal: #A6E3E9;
        --deep-teal: #71C9CE;
        --dark-bg: #091118;
        --card-bg: rgba(17, 32, 45, 0.85);
        --card-border: rgba(113, 201, 206, 0.22);
        --text-primary: #E3FDFD;
        --text-secondary: #A6E3E9;
        --text-muted: #6C8E99;
        --success-glow: rgba(113, 201, 206, 0.35);
        --warning-color: #F9C74F;
        --danger-color: #F94144;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: var(--dark-bg);
        color: var(--text-primary);
    }

    /* Top Navigation Banner */
    .netintel-header {
        background: linear-gradient(135deg, rgba(17, 32, 45, 0.95) 0%, rgba(9, 17, 24, 0.95) 100%);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .netintel-title {
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(90deg, #E3FDFD, #71C9CE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .netintel-subtitle {
        font-size: 13px;
        color: var(--text-secondary);
        margin: 0;
    }

    /* Metric KPI Cards */
    .kpi-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 12px;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: var(--deep-teal);
        box-shadow: 0 6px 24px var(--success-glow);
    }

    .kpi-label {
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--text-muted);
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: var(--ice-cyan);
        font-family: 'JetBrains Mono', monospace;
    }

    .kpi-subtext {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
    }

    /* Badges */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .badge-live {
        background: rgba(113, 201, 206, 0.2);
        color: var(--deep-teal);
        border: 1px solid var(--deep-teal);
    }

    .badge-warning {
        background: rgba(249, 199, 79, 0.18);
        color: #F9C74F;
        border: 1px solid #F9C74F;
    }

    .badge-critical {
        background: rgba(249, 65, 68, 0.2);
        color: #F94144;
        border: 1px solid #F94144;
    }

    .badge-simulation {
        background: rgba(166, 227, 233, 0.15);
        color: #A6E3E9;
        border: 1px dashed #A6E3E9;
    }

    /* Section Headers */
    .section-title {
        color: var(--ice-cyan);
        font-size: 18px;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 12px;
        border-bottom: 1px solid var(--card-border);
        padding-bottom: 6px;
    }

    /* Timeline styling */
    .timeline-item {
        border-left: 2px solid var(--deep-teal);
        padding-left: 14px;
        margin-left: 8px;
        margin-bottom: 14px;
        position: relative;
    }

    .timeline-item::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--deep-teal);
    }

    /* Plotly Chart Container Customization */
    .stPlotlyChart {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 8px;
    }
    </style>
    """
