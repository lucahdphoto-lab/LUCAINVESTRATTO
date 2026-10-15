"""
Financial Terminal styling and UI theme components for LUCAINVESTRATTO.
Inspired by FactSet Workstation, Bloomberg Terminal, and modern private wealth dashboards.
"""
import streamlit as st


def apply_theme():
    st.markdown("""
    <style>
        /* Modern Financial Dashboard Styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Top Header Brand */
        .brand-header {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }
        .brand-title {
            color: #F8FAFC;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brand-badge {
            background: #2563EB;
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .brand-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-top: 6px;
            margin-bottom: 0;
        }

        /* KPI Metric Card */
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .kpi-label {
            color: #64748B;
            font-size: 11.5px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .kpi-value {
            color: #0F172A;
            font-size: 22px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 4px;
        }
        .kpi-sub {
            font-size: 11.5px;
            font-weight: 500;
        }
        .kpi-positive {
            color: #16A34A;
        }
        .kpi-negative {
            color: #DC2626;
        }
        .kpi-neutral {
            color: #475569;
        }

        /* Dark mode compatibility for KPI cards */
        @media (prefers-color-scheme: dark) {
            .kpi-card {
                background: #1E293B;
                border-color: #334155;
            }
            .kpi-label {
                color: #94A3B8;
            }
            .kpi-value {
                color: #F8FAFC;
            }
            .kpi-neutral {
                color: #CBD5E1;
            }
        }

        /* FactSet Badge */
        .factset-tag {
            background: #E0E7FF;
            color: #3730A3;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #C7D2FE;
        }
    </style>
    """, unsafe_allow_html=True)


def render_brand_header(active_account_name: str = "Tutti i conti (Consolidato)"):
    st.markdown(f"""
    <div class="brand-header">
        <div class="brand-title">
            <span>🏛️ LUCAINVESTRATTO</span>
            <span class="brand-badge">PRO FACTSET & INVESTING ED.</span>
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
