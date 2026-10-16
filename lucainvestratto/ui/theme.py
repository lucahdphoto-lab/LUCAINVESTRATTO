"""
Financial Terminal styling and UI theme components for LUCAINVESTRATTO.
Inspired by FactSet Workstation, Bloomberg Terminal, and modern private wealth dashboards.
Supports dynamic theme presets, custom color palettes, gradient buttons & cards,
external background images, and adjustable glassmorphism transparency.
"""
from typing import Optional, Dict, List
import streamlit as st
from lucainvestratto.settings import AppSettings, hex_to_rgba


def apply_theme(settings: Optional[AppSettings] = None):
    if not settings:
        settings = AppSettings()

    colors = settings.get_active_colors()
    p_color = colors.get("primary_color", "#2563EB")
    h_start = colors.get("header_bg_start", "#0F172A")
    h_end = colors.get("header_bg_end", "#1E293B")
    accent = colors.get("accent_color", "#38BDF8")
    c_border = colors.get("card_border", "#CBD5E1")

    # Button Gradients
    if settings.gradient_buttons_enabled:
        btn_start = settings.gradient_btn_start if settings.use_custom_colors else colors.get("btn_gradient_start", p_color)
        btn_end = settings.gradient_btn_end if settings.use_custom_colors else colors.get("btn_gradient_end", "#1E40AF")
    else:
        btn_start = p_color
        btn_end = p_color

    # Card Transparency & Gradients
    card_opacity = settings.card_opacity_pct / 100.0
    card_blur = settings.card_blur_px

    if settings.gradient_cards_enabled:
        c_raw_start = settings.gradient_card_start if settings.use_custom_colors else colors.get("card_gradient_start", "#FFFFFF")
        c_raw_end = settings.gradient_card_end if settings.use_custom_colors else colors.get("card_gradient_end", "#F8FAFC")
    else:
        c_raw_start = "#FFFFFF"
        c_raw_end = "#FFFFFF"

    card_start_rgba = hex_to_rgba(c_raw_start, opacity=card_opacity)
    card_end_rgba = hex_to_rgba(c_raw_end, opacity=card_opacity)

    # Background Image CSS
    bg_image = settings.get_effective_background_image()
    overlay_opacity = max(0.1, min(0.98, settings.background_overlay_opacity))
    sidebar_opacity = max(0.4, min(1.0, settings.sidebar_opacity_pct / 100.0))

    bg_css = ""
    if bg_image:
        bg_css = f"""
        .stApp {{
            background-image: linear-gradient(rgba(15, 23, 42, {overlay_opacity:.2f}), rgba(15, 23, 42, {overlay_opacity:.2f})), url('{bg_image}') !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
        }}
        """

    st.markdown(f"""
    <style>
        /* Modern Financial Dashboard Styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        {bg_css}

        /* Sidebar Glassmorphism & Fixed Responsive Width */
        section[data-testid="stSidebar"] {{
            background: rgba(15, 23, 42, {sidebar_opacity:.2f}) !important;
            backdrop-filter: blur({card_blur}px) !important;
            -webkit-backdrop-filter: blur({card_blur}px) !important;
            width: 290px !important;
            min-width: 260px !important;
            max-width: 300px !important;
        }}

        /* On mobile, guarantee the sidebar leaves space and never covers 100% of the screen */
        @media (max-width: 768px) {{
            section[data-testid="stSidebar"] {{
                width: 82vw !important;
                max-width: 310px !important;
                box-shadow: 12px 0 35px rgba(0, 0, 0, 0.75) !important;
            }}
            /* Make sidebar collapse toggle clearly visible and touch-friendly */
            button[data-testid="stSidebarCollapseButton"] {{
                background: rgba(37, 99, 235, 0.3) !important;
                border: 1px solid rgba(56, 189, 248, 0.5) !important;
                border-radius: 8px !important;
                color: #38BDF8 !important;
                padding: 6px !important;
            }}
        }}

        /* Dynamic Header Brand */
        .brand-header {{
            background: linear-gradient(135deg, {h_start} 0%, {h_end} 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
            backdrop-filter: blur({card_blur}px);
            -webkit-backdrop-filter: blur({card_blur}px);
        }}
        .brand-title {{
            color: #F8FAFC;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .brand-badge {{
            background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%);
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .alert-pill {{
            background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 2px 10px rgba(220, 38, 38, 0.4);
            animation: pulse-alert 2s infinite;
        }}
        @keyframes pulse-alert {{
            0% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }}
            70% {{ transform: scale(1.03); box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }}
            100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }}
        }}
        .brand-subtitle {{
            color: #94A3B8;
            font-size: 13px;
            margin-top: 6px;
            margin-bottom: 0;
        }}

        /* Buttons with Degrading Gradients (Sfumature degradanti) */
        .stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {{
            background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.45rem 1.1rem !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18) !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        .stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28) !important;
            filter: brightness(1.1) !important;
        }}
        .stButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%) !important;
            backdrop-filter: blur({card_blur}px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }}
        .stButton > button[kind="secondary"]:hover {{
            transform: translateY(-1px) !important;
            border-color: {p_color} !important;
        }}

        /* KPI Metric Card with Gradients & Transparency */
        .kpi-card {{
            background: linear-gradient(135deg, {card_start_rgba} 0%, {card_end_rgba} 100%) !important;
            backdrop-filter: blur({card_blur}px) !important;
            -webkit-backdrop-filter: blur({card_blur}px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
        }}
        .kpi-label {{
            color: #64748B;
            font-size: 11.5px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .kpi-value {{
            color: #0F172A;
            font-size: 22px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 4px;
        }}
        .kpi-sub {{
            font-size: 11.5px;
            font-weight: 500;
        }}
        .kpi-positive {{
            color: #16A34A;
        }}
        .kpi-negative {{
            color: #DC2626;
        }}
        .kpi-neutral {{
            color: #475569;
        }}

        @media (prefers-color-scheme: dark) {{
            .kpi-card {{
                border-color: rgba(255, 255, 255, 0.12) !important;
            }}
            .kpi-label {{
                color: #94A3B8;
            }}
            .kpi-value {{
                color: #F8FAFC;
            }}
            .kpi-neutral {{
                color: #CBD5E1;
            }}
        }}

        /* Stylized Notification Boxes */
        .notif-box {{
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            backdrop-filter: blur({card_blur}px);
        }}
        .notif-danger {{
            background: rgba(254, 242, 242, 0.9);
            border: 1px solid #FCA5A5;
            color: #991B1B;
        }}
        .notif-warning {{
            background: rgba(255, 251, 235, 0.9);
            border: 1px solid #FCD34D;
            color: #92400E;
        }}
        .notif-info {{
            background: rgba(239, 246, 255, 0.9);
            border: 1px solid #BFDBFE;
            color: #1E40AF;
        }}

        /* Sidebar Navigation & Section Categorization */
        .sidebar-section-title {{
            font-size: 11px !important;
            font-weight: 700 !important;
            color: #94A3B8 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.9px !important;
            margin-top: 18px !important;
            margin-bottom: 6px !important;
            padding-left: 4px !important;
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
        }}

        /* Sidebar Button Alignment & Styling */
        section[data-testid="stSidebar"] div.stButton > button {{
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
            padding: 0.45rem 0.85rem !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            letter-spacing: -0.15px !important;
            border-radius: 8px !important;
            margin-bottom: 2px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }}

        section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
            font-weight: 600 !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
        }}

        /* Compact Wealth Card for Sidebar */
        .sidebar-wealth-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 10px 12px;
            margin-top: 8px;
            margin-bottom: 14px;
            backdrop-filter: blur(8px);
        }}
        .sidebar-wealth-row {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #94A3B8;
            margin-bottom: 3px;
        }}
        .sidebar-wealth-row b {{
            color: #F8FAFC;
            font-family: 'JetBrains Mono', monospace;
        }}
        .sidebar-wealth-total {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 700;
            color: #F8FAFC;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 6px;
            margin-top: 5px;
        }}
        .sidebar-wealth-total b {{
            color: #38BDF8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13.5px;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_brand_header(active_account_name: str = "Tutti i conti (Consolidato)", active_alerts_count: int = 0):
    alert_badge = f'<span class="alert-pill">⚠️ {active_alerts_count} ALERT ATTIVI</span>' if active_alerts_count > 0 else ''
    st.markdown(f"""
    <div class="brand-header">
        <div class="brand-title">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span>🏛️ LUCAINVESTRATTO</span>
                <span class="brand-badge">PRO SUITE</span>
            </div>
            {alert_badge}
        </div>
        <p class="brand-subtitle">
            Piattaforma di Gestione Multi-Conto Bancario • Import Estratto Conto & Snapshot • Analisi Rischio/Rendimento Istituzionale
            <br>
            <b>Conto attivo:</b> <span style="color: #60A5FA;">{active_account_name}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, sub: str = "", trend: str = "neutral"):
    css_class = f"kpi-{trend}" if trend in ["positive", "negative", "neutral"] else "kpi-neutral"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-sub {css_class}">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)
