"""
Financial Terminal styling and UI theme components for LUCAINVESTRATTO.
Inspired by FactSet Workstation, Bloomberg Terminal, and modern private wealth dashboards.
Supports dynamic theme presets, custom color palettes, and alert notification badges.
"""
from typing import Optional, Dict, List
import streamlit as st


def apply_theme(colors: Optional[Dict[str, str]] = None):
    if not colors:
        colors = {
            "primary_color": "#2563EB",
            "header_bg_start": "#0F172A",
            "header_bg_end": "#1E293B",
            "card_border": "#CBD5E1",
            "accent_color": "#38BDF8",
            "positive_color": "#16A34A",
            "negative_color": "#DC2626"
        }

    p_color = colors.get("primary_color", "#2563EB")
    h_start = colors.get("header_bg_start", "#0F172A")
    h_end = colors.get("header_bg_end", "#1E293B")
    accent = colors.get("accent_color", "#38BDF8")
    c_border = colors.get("card_border", "#CBD5E1")

    st.markdown(f"""
    <style>
        /* Modern Financial Dashboard Styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* Dynamic Header Brand */
        .brand-header {{
            background: linear-gradient(135deg, {h_start} 0%, {h_end} 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.18);
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
            background: {p_color};
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .alert-pill {{
            background: #DC2626;
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
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

        /* KPI Metric Card */
        .kpi-card {{
            background: #FFFFFF;
            border: 1px solid {c_border};
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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
                background: #1E293B;
                border-color: #334155;
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
        }}
        .notif-danger {{
            background: #FEF2F2;
            border: 1px solid #FCA5A5;
            color: #991B1B;
        }}
        .notif-warning {{
            background: #FFFBEB;
            border: 1px solid #FCD34D;
            color: #92400E;
        }}
        .notif-info {{
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            color: #1E40AF;
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
