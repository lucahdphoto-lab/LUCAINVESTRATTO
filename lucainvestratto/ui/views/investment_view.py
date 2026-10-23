"""
Professional investment & risk analytics view for LUCAINVESTRATTO.
Implements institutional parameters from FactSet, Bloomberg, and Investing.com:
- Sharpe Ratio, Sortino Ratio, Calmar Ratio, Treynor Ratio
- Maximum Drawdown (MDD) & Underwater Chart
- Value at Risk (VaR 95%, 99% Historical & Parametric) & Expected Shortfall (CVaR)
- Beta, Jensen's Alpha, R², Tracking Error, Information Ratio
- Benchmark Comparison vs MSCI World, S&P 500, FTSE MIB, Euro Aggregate Bonds
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from lucainvestratto.db import db
from lucainvestratto.models import Holding
from lucainvestratto.config import BENCHMARKS, DEFAULT_RISK_FREE_RATE
from lucainvestratto.analytics.risk import calculate_risk_metrics
from lucainvestratto.ui.theme import render_metric_card


def render_investment_view(selected_account_id: str = "all"):
    st.subheader("📈 Analisi Investimento Avanzata — Standard FactSet & Investing.com")
    st.markdown("""
    Metriche di rendimento corretto per il rischio (*risk-adjusted performance*),
    analisi di drawdown istituzionale, Value at Risk (VaR) e confronto con benchmark di mercato.
    """)

    holdings = db.get_holdings(account_id=selected_account_id)
    if not holdings:
        st.info("Nessuna posizione finanziaria per il conto selezionato. Aggiungi titoli per eseguire l'analisi quantitativa.")
        return

    # Configuration bar
    c_bmk, c_rf = st.columns([3, 2])
    with c_bmk:
        bmk_options = {k: f"{v.name} ({v.asset_type})" for k, v in BENCHMARKS.items()}
        selected_bmk_key = st.selectbox(
            "Benchmark di Riferimento Istituzionale:",
            options=list(bmk_options.keys()),
            format_func=lambda k: bmk_options[k],
            index=0
        )
    with c_rf:
        rf_rate_pct = st.number_input(
            "Tasso Risk-Free Annuo (Rf %)",
            min_value=0.0,
            max_value=15.0,
            value=DEFAULT_RISK_FREE_RATE * 100.0,
            step=0.25,
            help="Tasso privo di rischio di riferimento (es. €STR / BCE Depo Rate pari al 3.0%)"
        )

    # Compute Risk Metrics
    risk_data = calculate_risk_metrics(
        holdings,
        risk_free_rate=rf_rate_pct / 100.0,
        benchmark_code=selected_bmk_key
    )

    # 1. Top KPI Row - FactSet Standard Ratios
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        sharpe = risk_data["sharpe_ratio"]
        s_trend = "positive" if sharpe >= 1.0 else ("neutral" if sharpe >= 0.5 else "negative")
        render_metric_card("Indice di Sharpe", f"{sharpe:.2f}", "Rendimento / Volatilità", s_trend)
    with k2:
        sortino = risk_data["sortino_ratio"]
        so_trend = "positive" if sortino >= 1.2 else ("neutral" if sortino >= 0.6 else "negative")
        render_metric_card("Indice di Sortino", f"{sortino:.2f}", "Focus su volatilità negativa", so_trend)
    with k3:
        calmar = risk_data["calmar_ratio"]
        c_trend = "positive" if calmar >= 0.8 else "neutral"
        render_metric_card("Indice di Calmar", f"{calmar:.2f}", "CAGR / Max Drawdown", c_trend)
    with k4:
        vol = risk_data["volatility_annualized"]
        render_metric_card("Volatilità Annualizzata", f"{vol:.2f}%", f"Benchmark: {risk_data['bmk_volatility_annualized']:.1f}%", "neutral")

    # 2. Second KPI Row - Extreme Risk & Benchmark Sensitivity
    k5, k6, k7, k8 = st.columns(4)
    with k5:
        mdd = risk_data["max_drawdown"]
        render_metric_card("Massimo Drawdown (MDD)", f"{mdd:.2f}%", f"Attuale: {risk_data['current_drawdown']:.2f}%", "negative")
    with k6:
        var_ann = risk_data["var_95_annual"]
        var_amt = risk_data["var_95_amount_eur"]
        render_metric_card("VaR 95% Annuo", f"{var_ann:.2f}%", f"Perdita max: € {var_amt:,.0f}", "negative")
    with k7:
        beta = risk_data["beta"]
        b_sub = "Più volatile del mercato" if beta > 1.05 else ("Meno volatile del mercato" if beta < 0.95 else "In linea col mercato")
        render_metric_card("Beta vs Benchmark", f"{beta:.2f}", b_sub, "neutral")
    with k8:
        alpha = risk_data["alpha_jensen"]
        a_trend = "positive" if alpha > 0 else "negative"
        render_metric_card("Alfa di Jensen", f"{alpha:+.2f}%", "Extra-rendimento CAPM", a_trend)

    st.divider()

    df_series = risk_data["df_series"]

    # 3. Chart: Portfolio vs Benchmark Normalized Trajectory
    st.markdown(f"#### 📊 Performance Cumulativa: Portafoglio vs {risk_data['benchmark_name']} (Base 100)")
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(
        x=df_series["Date"],
        y=df_series["Portfolio_Index"],
        mode="lines",
        name="Portafoglio Reale",
        line=dict(color="#2563EB", width=2.5)
    ))
    fig_comp.add_trace(go.Scatter(
        x=df_series["Date"],
        y=df_series["Benchmark_Index"],
        mode="lines",
        name=f"Benchmark ({selected_bmk_key})",
        line=dict(color="#94A3B8", width=1.8, dash="dot")
    ))
    fig_comp.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=380,
        hovermode="x unified",
        xaxis_title="",
        yaxis_title="Valore Indicizzato (Base 100)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # 4. Chart: Underwater Drawdown (FactSet Standard)
    col_dd, col_vol = st.columns([3, 2])

    with col_dd:
        st.markdown("#### 🌊 Curva Underwater (Drawdown dal Massimo Storico)")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=df_series["Date"],
            y=df_series["Drawdown"],
            mode="lines",
            name="Drawdown Portafoglio",
            line=dict(color="#DC2626", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(220, 38, 38, 0.15)"
        ))
        fig_dd.add_trace(go.Scatter(
            x=df_series["Date"],
            y=df_series["Benchmark_Drawdown"],
            mode="lines",
            name="Drawdown Benchmark",
            line=dict(color="#64748B", width=1, dash="dash")
        ))
        fig_dd.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            hovermode="x unified",
            xaxis_title="",
            yaxis_title="Drawdown (%)",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    with col_vol:
        st.markdown("#### 📉 Volatilità Rolling a 30 Giorni (Ann. %)")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(
            x=df_series["Date"],
            y=df_series["Rolling_Vol"],
            mode="lines",
            name="Rolling 30D Vol",
            line=dict(color="#F59E0B", width=2)
        ))
        fig_vol.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            hovermode="x unified",
            xaxis_title="",
            yaxis_title="Volatilità (%)",
            template="plotly_white"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    st.divider()

    # 5. Full FactSet Statistical Matrix Table
    st.markdown("#### 📋 Matrice Statistica Completa (FactSet / Bloomberg Standard Table)")

    stat_data = [
        {"Parametro Analitico": "Rendimento Cumulativo (1 Anno)", "Portafoglio": f"{risk_data['cumulative_return']:+.2f}%", "Benchmark": f"{risk_data['bmk_cumulative_return']:+.2f}%", "Descrizione": "Rendimento complessivo nel periodo"},
        {"Parametro Analitico": "Rendimento Annualizzato (CAGR)", "Portafoglio": f"{risk_data['cagr']:+.2f}%", "Benchmark": f"{risk_data['bmk_cagr']:+.2f}%", "Descrizione": "Tasso di crescita annuale composto"},
        {"Parametro Analitico": "Volatilità Annualizzata (Dev. Standard)", "Portafoglio": f"{risk_data['volatility_annualized']:.2f}%", "Benchmark": f"{risk_data['bmk_volatility_annualized']:.2f}%", "Descrizione": "Dispersione dei rendimenti attorno alla media"},
        {"Parametro Analitico": "Downside Deviation (Deviazione Ribassista)", "Portafoglio": f"{risk_data['downside_deviation']:.2f}%", "Benchmark": "-", "Descrizione": "Volatilità calcolata solo sui rendimenti negativi"},
        {"Parametro Analitico": "Indice di Sharpe", "Portafoglio": f"{risk_data['sharpe_ratio']:.2f}", "Benchmark": "-", "Descrizione": "Extra-rendimento per unità di rischio totale"},
        {"Parametro Analitico": "Indice di Sortino", "Portafoglio": f"{risk_data['sortino_ratio']:.2f}", "Benchmark": "-", "Descrizione": "Extra-rendimento per unità di rischio di ribasso"},
        {"Parametro Analitico": "Indice di Calmar", "Portafoglio": f"{risk_data['calmar_ratio']:.2f}", "Benchmark": "-", "Descrizione": "Rapporto tra CAGR e Massimo Drawdown"},
        {"Parametro Analitico": "Indice di Treynor", "Portafoglio": f"{risk_data['treynor_ratio']:.2f}", "Benchmark": "-", "Descrizione": "Extra-rendimento per unità di rischio sistematico (Beta)"},
        {"Parametro Analitico": "Massimo Drawdown (MDD)", "Portafoglio": f"{risk_data['max_drawdown']:.2f}%", "Benchmark": "-", "Descrizione": "Massima perdita da picco a valle registrata"},
        {"Parametro Analitico": "Value at Risk (VaR 95% 1-Giorno)", "Portafoglio": f"{risk_data['var_95_daily']:.2f}%", "Benchmark": "-", "Descrizione": "Massima perdita attesa giornaliera con confidenza 95%"},
        {"Parametro Analitico": "Value at Risk (VaR 95% Annuale)", "Portafoglio": f"{risk_data['var_95_annual']:.2f}%", "Benchmark": "-", "Descrizione": "Massima perdita annua con intervallo di confidenza 95%"},
        {"Parametro Analitico": "Conditional VaR / Expected Shortfall 95%", "Portafoglio": f"{risk_data['cvar_95_annual']:.2f}%", "Benchmark": "-", "Descrizione": "Perdita media attesa nello scenario peggiore del 5%"},
        {"Parametro Analitico": "Beta vs Benchmark", "Portafoglio": f"{risk_data['beta']:.2f}", "Benchmark": "1.00", "Descrizione": "Sensibilità del portafoglio alle oscillazioni del mercato"},
        {"Parametro Analitico": "Alfa di Jensen (CAPM Alpha)", "Portafoglio": f"{risk_data['alpha_jensen']:+.2f}%", "Benchmark": "0.00%", "Descrizione": "Extra-rendimento generato oltre il modello CAPM"},
        {"Parametro Analitico": "Coefficiente di Correlazione (r)", "Portafoglio": f"{risk_data['correlation']:.2f}", "Benchmark": "1.00", "Descrizione": "Grado di correlazione lineare con il benchmark"},
        {"Parametro Analitico": "Coefficiente di Determinazione (R²)", "Portafoglio": f"{risk_data['r_squared']:.2f}", "Benchmark": "1.00", "Descrizione": "% della varianza del portafoglio spiegata dal benchmark"},
        {"Parametro Analitico": "Tracking Error", "Portafoglio": f"{risk_data['tracking_error']:.2f}%", "Benchmark": "-", "Descrizione": "Volatilità dello scostamento rispetto al benchmark"},
        {"Parametro Analitico": "Information Ratio", "Portafoglio": f"{risk_data['information_ratio']:.2f}", "Benchmark": "-", "Descrizione": "Efficienza dell'extra-rendimento rispetto al tracking error"},
        {"Parametro Analitico": "Percentuale Giorni Positivi (Win Rate)", "Portafoglio": f"{risk_data['win_rate']:.1f}%", "Benchmark": "-", "Descrizione": "Frequenza di sessioni di mercato con rendimento > 0"}
    ]

    df_stat = pd.DataFrame(stat_data)
    st.dataframe(
        df_stat.style.set_properties(subset=["Portafoglio", "Benchmark"], **{'text-align': 'right'}),
        use_container_width=True,
        height=420
    )
