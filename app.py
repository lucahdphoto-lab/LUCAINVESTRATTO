"""
Main application entry point for LUCAINVESTRATTO.
Multi-bank account management, multi-format statement import (.xlsx, .csv, .txt, .png, .jpg),
date-based cash flow analysis, asset allocation, institutional investment analytics (FactSet/Investing standards),
automated multi-format report exports (.pdf, .xlsx, .txt), and comprehensive settings with custom colors,
notifications, selective resets, and data alignment.
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from lucainvestratto.db import db
from lucainvestratto.settings import load_settings
from lucainvestratto.ui.theme import apply_theme, render_brand_header, render_metric_card
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics
from lucainvestratto.analytics.notifications import evaluate_alerts
from lucainvestratto.ui.views import (
    render_accounts_view,
    render_import_view,
    render_cashflow_view,
    render_asset_view,
    render_investment_view,
    render_export_view,
    render_settings_view
)

# Page Configuration
st.set_page_config(
    page_title="LUCAINVESTRATTO - Wealth & Statement Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load settings and apply dynamic visual theme
app_settings = load_settings()
active_colors = app_settings.get_active_colors()
apply_theme(app_settings)

# Ensure sample demo data is loaded if database is empty on first boot
db.load_demo_data(reset=False)

# Fetch accounts from DB
accounts = db.get_accounts()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🏛️ **LUCAINVESTRATTO**")
    st.caption("v1.0.0 • Institutional Financial Suite")
    st.divider()

    # Account Scope Selector
    st.markdown("### 🏦 **Perimetro Conto**")
    account_options = {"all": "🌐 Tutti i conti (Consolidato)"}
    for acc in accounts:
        account_options[acc.id] = f"{acc.name} ({acc.bank_name or acc.currency})"

    selected_account_id = st.selectbox(
        "Seleziona Conto di Analisi:",
        options=list(account_options.keys()),
        format_func=lambda k: account_options[k],
        index=0
    )
    selected_account_name = account_options[selected_account_id]

    # Quick Wealth Summary in Sidebar
    active_txs = db.get_transactions(account_id=selected_account_id)
    active_holdings = db.get_holdings(account_id=selected_account_id)
    cash_sum = calculate_cashflow_summary(active_txs, accounts, selected_account_id=selected_account_id)
    asset_sum = calculate_asset_summary(active_holdings)

    tot_cash = cash_sum["final_balance"]
    tot_invest = asset_sum["total_market_value"]
    net_worth = tot_cash + tot_invest

    st.markdown("---")
    st.markdown(f"**Liquidità Disponibile:**<br>`€ {tot_cash:,.2f}`", unsafe_allow_html=True)
    st.markdown(f"**Portafoglio Investito:**<br>`€ {tot_invest:,.2f}`", unsafe_allow_html=True)
    st.markdown(f"**Patrimonio Netto:**<br><span style='color: {active_colors['primary_color']}; font-size: 1.15em; font-weight: bold;'>€ {net_worth:,.2f}</span>", unsafe_allow_html=True)
    st.markdown("---")

    # Evaluate Active Notifications
    active_alerts = evaluate_alerts(app_settings, accounts, active_holdings, active_txs)
    if active_alerts:
        st.warning(f"⚠️ **{len(active_alerts)} Alert Rilevati**")

    # Main Navigation
    st.markdown("### 🧭 **Menu Navigazione**")
    nav_choice = st.radio(
        "Seleziona Maschera:",
        [
            "📊 Dashboard Consolidata",
            "📅 Estratto Conto per Data",
            "💼 Analisi per Asset",
            "📈 Analisi Investimento (FactSet)",
            "📥 Import Dati (.xlsx, .csv, .txt, .img)",
            "🏦 Gestione Conti Bancari",
            "📑 Esportazione Report (.pdf, .xlsx, .txt)",
            "⚙️ Impostazioni & Alert"
        ],
        index=0
    )

    st.divider()
    st.caption("© 2026 LUCAINVESTRATTO Financial Analytics")


# ================= MAIN VIEW ROUTING =================
render_brand_header(active_account_name=selected_account_name, active_alerts_count=len(active_alerts))

# If there are active alerts and on Dashboard, render a quick notification banner
if active_alerts and nav_choice == "📊 Dashboard Consolidata":
    with st.expander(f"⚠️ **Attenzione: {len(active_alerts)} soglie di allerta superate** (Clicca per visualizzare i dettagli)", expanded=True):
        for alert in active_alerts:
            box_class = f"notif-{alert.level}"
            st.markdown(f"""
            <div class="notif-box {box_class}">
                <span style="font-size: 20px;">{alert.icon}</span>
                <div>
                    <b>{alert.title}</b>: {alert.message}
                    <br><small>Rilevato: <b>{alert.current_value}</b> (Soglia limite: {alert.threshold_value})</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

if nav_choice == "📊 Dashboard Consolidata":
    # Executive Overview Dashboard
    st.subheader("📊 Sintesi Patrimoniale & Panoramica Consolidata")
    st.markdown(f"Visualizzazione aggregata per: **{selected_account_name}**")

    # Top KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Patrimonio Totale Netto", f"€ {net_worth:,.2f}", "Liquidità + Investimenti", "neutral")
    with c2:
        render_metric_card("Liquidità Conti", f"€ {tot_cash:,.2f}", f"Saldi disponibili", "neutral")
    with c3:
        render_metric_card("Valore Investito", f"€ {tot_invest:,.2f}", f"{len(active_holdings)} posizioni attive", "neutral")
    with c4:
        pl = asset_sum["total_unrealized_pl"]
        pl_pct = asset_sum["total_unrealized_pl_pct"]
        trend = "positive" if pl >= 0 else "negative"
        render_metric_card("P&L Latente Portafoglio", f"€ {pl:+,.2f}", f"{pl_pct:+.2f}% sul costo PMC", trend)
    with c5:
        cf_net = cash_sum["net_cashflow"]
        cf_trend = "positive" if cf_net >= 0 else "negative"
        render_metric_card("Flusso Netto Cassa", f"€ {cf_net:+,.2f}", f"Tasso risp: {cash_sum['savings_rate_pct']:.1f}%", cf_trend)

    st.divider()

    # Visualizations Row 1
    col_chart_l, col_chart_r = st.columns([1, 1])

    with col_chart_l:
        st.markdown("#### 🎯 Ripartizione Patrimonio & Asset Allocation")
        alloc_items = []
        if tot_cash > 0:
            alloc_items.append({"Classe": "Liquidità & Conti Correnti", "Valore": tot_cash})
        for _, r in asset_sum["df_by_class"].iterrows():
            alloc_items.append({"Classe": str(r["asset_class"]), "Valore": float(r["market_value"])})
        
        df_overall = pd.DataFrame(alloc_items)
        if not df_overall.empty:
            fig_alloc = px.pie(
                df_overall,
                names="Classe",
                values="Valore",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_alloc.update_traces(textposition="inside", textinfo="percent+label")
            fig_alloc.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=340, showlegend=False)
            st.plotly_chart(fig_alloc, use_container_width=True)
        else:
            st.info("Nessun dato di allocazione disponibile.")

    with col_chart_r:
        st.markdown("#### 📈 Evoluzione Flusso di Cassa & Saldi")
        df_daily = cash_sum["df_daily"]
        if not df_daily.empty:
            fig_dash_bal = go.Figure()
            fig_dash_bal.add_trace(go.Scatter(
                x=df_daily["date"],
                y=df_daily["balance"],
                mode="lines",
                name="Saldo Cassa",
                line=dict(color=active_colors["primary_color"], width=2.5),
                fill="tozeroy",
                fillcolor=f"rgba(37, 99, 235, 0.10)"
            ))
            fig_dash_bal.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=340,
                hovermode="x unified",
                xaxis_title="",
                yaxis_title="Saldo (€)",
                template="plotly_white"
            )
            st.plotly_chart(fig_dash_bal, use_container_width=True)
        else:
            st.info("Nessun movimento cassa registrato.")

    st.divider()

    # FactSet Quick Metrics Preview
    st.markdown("#### ⚡ Anteprima Rapida Metriche FactSet & Investing")
    if active_holdings:
        risk_quick = calculate_risk_metrics(active_holdings)
        q1, q2, q3, q4, q5 = st.columns(5)
        with q1:
            render_metric_card("Sharpe Ratio", f"{risk_quick['sharpe_ratio']:.2f}", "Rendimento/Rischio", "positive")
        with q2:
            render_metric_card("Sortino Ratio", f"{risk_quick['sortino_ratio']:.2f}", "Downside risk", "positive")
        with q3:
            render_metric_card("Max Drawdown", f"{risk_quick['max_drawdown']:.2f}%", "Picco-Valle", "negative")
        with q4:
            render_metric_card("VaR 95% Annuo", f"{risk_quick['var_95_annual']:.2f}%", f"€ {risk_quick['var_95_amount_eur']:,.0f}", "negative")
        with q5:
            render_metric_card("Alfa di Jensen", f"{risk_quick['alpha_jensen']:+.2f}%", "Extra-rendimento", "positive")
    else:
        st.info("Aggiungi o importa posizioni per calcolare le metriche di rischio istituzionali.")

elif nav_choice == "📅 Estratto Conto per Data":
    render_cashflow_view(selected_account_id=selected_account_id)

elif nav_choice == "💼 Analisi per Asset":
    render_asset_view(selected_account_id=selected_account_id)

elif nav_choice == "📈 Analisi Investimento (FactSet)":
    render_investment_view(selected_account_id=selected_account_id)

elif nav_choice == "📥 Import Dati (.xlsx, .csv, .txt, .img)":
    render_import_view()

elif nav_choice == "🏦 Gestione Conti Bancari":
    render_accounts_view()

elif nav_choice == "📑 Esportazione Report (.pdf, .xlsx, .txt)":
    render_export_view(selected_account_id=selected_account_id, selected_account_name=selected_account_name)

elif nav_choice == "⚙️ Impostazioni & Alert":
    render_settings_view()
