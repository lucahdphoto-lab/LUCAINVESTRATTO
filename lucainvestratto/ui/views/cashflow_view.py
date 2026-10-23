"""
Bank statement analysis view by date (Estratto Conto per Data) for LUCAINVESTRATTO.
Includes date range filtering, KPI cards, running balance evolution, monthly inflows/outflows,
and categorized expenditure breakdown.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta, datetime

from lucainvestratto.db import db
from lucainvestratto.models import Transaction, BankAccount
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.ui.theme import render_metric_card
from lucainvestratto.export.excel_report import generate_dataframe_excel


def render_cashflow_view(selected_account_id: str = "all"):
    st.subheader("📅 Analisi Estratto Conto & Flussi di Cassa per Data")
    st.markdown("Monitoraggio dinamico dei movimenti bancari, curve di saldo temporale, entrate e uscite categorizzate.")

    accounts = db.get_accounts()
    if not accounts:
        st.warning("Nessun conto bancario configurato. Carica prima i dati nella sezione 'Gestione Conti'.")
        return

    # Date range selector filters
    col_preset, col_dates = st.columns([2, 3])
    with col_preset:
        preset = st.selectbox(
            "Filtro Temporale Rapido:",
            ["Tutto lo Storico", "Ultimo Mese (30gg)", "Ultimi 3 Mesi (90gg)", "Ultimi 6 Mesi (180gg)", "YTD (Anno Corrente)", "Ultimo Anno (365gg)", "Personalizzato"],
            index=0
        )

    today = date.today()
    if preset == "Ultimo Mese (30gg)":
        start_d = today - timedelta(days=30)
        end_d = today
    elif preset == "Ultimi 3 Mesi (90gg)":
        start_d = today - timedelta(days=90)
        end_d = today
    elif preset == "Ultimi 6 Mesi (180gg)":
        start_d = today - timedelta(days=180)
        end_d = today
    elif preset == "YTD (Anno Corrente)":
        start_d = date(today.year, 1, 1)
        end_d = today
    elif preset == "Ultimo Anno (365gg)":
        start_d = today - timedelta(days=365)
        end_d = today
    elif preset == "Personalizzato":
        with col_dates:
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                start_d = st.date_input("Data Inizio", value=today - timedelta(days=180))
            with c_d2:
                end_d = st.date_input("Data Fine", value=today)
    else:
        start_d = None
        end_d = None

    # Fetch transactions with date and account filters
    start_str = start_d.isoformat() if start_d else None
    end_str = end_d.isoformat() if end_d else None
    transactions = db.get_transactions(account_id=selected_account_id, start_date=start_str, end_date=end_str)

    # Calculate Cashflow Summary
    summary = calculate_cashflow_summary(transactions, accounts, selected_account_id=selected_account_id)

    # 1. Top KPI Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_metric_card("Saldo Iniziale", f"€ {summary['initial_balance']:,.2f}", "Inizio periodo", "neutral")
    with k2:
        render_metric_card("Totale Entrate", f"€ {summary['total_inflows']:,.2f}", "Accrediti lordi", "positive")
    with k3:
        render_metric_card("Totale Uscite", f"€ {summary['total_outflows']:,.2f}", "Addebiti e spese", "negative")
    with k4:
        net_flow = summary["net_cashflow"]
        trend = "positive" if net_flow >= 0 else "negative"
        render_metric_card("Flusso Netto", f"€ {net_flow:+,.2f}", "Entrate - Uscite", trend)
    with k5:
        render_metric_card("Saldo Finale", f"€ {summary['final_balance']:,.2f}", "Liquidità effettiva", "neutral")
    with k6:
        sav_rate = summary["savings_rate_pct"]
        s_trend = "positive" if sav_rate >= 20 else ("neutral" if sav_rate >= 0 else "negative")
        render_metric_card("Tasso Risparmio", f"{sav_rate:.1f}%", "% entrate risparmiata", s_trend)

    st.divider()

    if not transactions:
        st.info("Nessuna transazione trovata per il periodo selezionato.")
        return

    # 2. Charts Row 1: Running Balance Evolution & Monthly In/Out
    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("#### 📈 Evoluzione Storica del Saldo di Liquidità")
        df_daily = summary["df_daily"]
        if not df_daily.empty:
            fig_bal = go.Figure()
            fig_bal.add_trace(go.Scatter(
                x=df_daily["date"],
                y=df_daily["balance"],
                mode="lines+markers",
                name="Saldo Totale (€)",
                line=dict(color="#2563EB", width=2.5),
                fill="tozeroy",
                fillcolor="rgba(37, 99, 235, 0.12)"
            ))
            fig_bal.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=350,
                hovermode="x unified",
                xaxis_title="",
                yaxis_title="Saldo (€)",
                template="plotly_white"
            )
            st.plotly_chart(fig_bal, use_container_width=True)

    with col_chart2:
        st.markdown("#### 📊 Flussi Mensili (Entrate vs Uscite)")
        df_monthly = summary["df_monthly"]
        if not df_monthly.empty:
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(
                x=df_monthly["Mese"],
                y=df_monthly["Entrate"],
                name="Entrate",
                marker_color="#16A34A"
            ))
            fig_m.add_trace(go.Bar(
                x=df_monthly["Mese"],
                y=-df_monthly["Uscite"],
                name="Uscite",
                marker_color="#DC2626"
            ))
            fig_m.add_trace(go.Scatter(
                x=df_monthly["Mese"],
                y=df_monthly["Netto"],
                mode="lines+markers",
                name="Flusso Netto",
                line=dict(color="#0F172A", width=2)
            ))
            fig_m.update_layout(
                barmode="relative",
                margin=dict(l=20, r=20, t=20, b=20),
                height=350,
                hovermode="x unified",
                xaxis_title="",
                yaxis_title="Importo (€)",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_m, use_container_width=True)

    # 3. Charts Row 2: Category Breakdown
    col_cat1, col_cat2 = st.columns(2)

    with col_cat1:
        st.markdown("#### 🥧 Scomposizione Spese per Categoria")
        df_out = summary["category_outflows"]
        if not df_out.empty:
            fig_cat = px.pie(
                df_out,
                names="Categoria",
                values="Totale (€)",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Sunset
            )
            fig_cat.update_traces(textposition="inside", textinfo="percent+label")
            fig_cat.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=320,
                showlegend=False
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nessuna uscita registrata nel periodo.")

    with col_cat2:
        st.markdown("#### 💰 Fonti di Entrata / Reddito")
        df_in = summary["category_inflows"]
        if not df_in.empty:
            fig_in = px.bar(
                df_in,
                x="Totale (€)",
                y="Categoria",
                orientation="h",
                color="Totale (€)",
                color_continuous_scale="Greens"
            )
            fig_in.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=320,
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_in, use_container_width=True)
        else:
            st.info("Nessuna entrata registrata nel periodo.")

    st.divider()

    # 4. Filterable Transactions Table
    st.markdown(f"#### 📜 Registro Movimenti Estratto Conto ({len(transactions)} transazioni)")
    
    # Text search
    search_q = st.text_input("🔍 Filtra transazioni per descrizione o causale:", placeholder="es. Stipendio, Replay, BTP, Carta...")
    
    table_rows = []
    for tx in transactions:
        if search_q and search_q.lower() not in tx.description.lower() and search_q.lower() not in tx.category.lower():
            continue
        table_rows.append({
            "Data": tx.date,
            "Conto": next((a.name for a in accounts if a.id == tx.account_id), tx.account_id),
            "Tipo": tx.type,
            "Categoria": tx.category,
            "Importo (€)": tx.amount,
            "Descrizione / Causale": tx.description,
            "Titolo": tx.asset_symbol or "-"
        })

    if table_rows:
        df_display = pd.DataFrame(table_rows)
        # Ensure Importo is float
        df_display["Importo (€)"] = df_display["Importo (€)"].astype(float)
        
        c_tbl, c_dl = st.columns([3, 1])
        with c_dl:
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            # 1. Excel (.xlsx) with strictly numeric floats, currency format, and right alignment
            xlsx_data = generate_dataframe_excel(
                df=df_display,
                title="LUCAINVESTRATTO - Estratto Conto & Flussi di Cassa",
                sheet_name="Movimenti",
                currency_cols=["Importo (€)"],
                center_cols=["Data", "Titolo"],
                sum_cols=["Importo (€)"]
            )
            st.download_button(
                label="📥 Esporta Excel (.xlsx)",
                data=xlsx_data,
                file_name=f"LUCAINVESTRATTO_Movimenti_{now_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
                help="File Excel nativo con numeri formattati come Valuta (€) e allineati rigorosamente a DESTRA."
            )

            # 2. Italian Excel CSV (; separator, , decimal)
            csv_data = df_display.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
            st.download_button(
                label="📥 Esporta CSV (Excel IT)",
                data=csv_data,
                file_name=f"LUCAINVESTRATTO_Movimenti_{now_str}.csv",
                mime="text/csv",
                use_container_width=True,
                help="Formato CSV con ';' e decimale virgola ',' per apertura diretta in Microsoft Excel con numeri riconosciuti e allineati a destra."
            )

        st.dataframe(
            df_display,
            column_config={
                "Importo (€)": st.column_config.NumberColumn(
                    "Importo (€)",
                    format="€ %.2f",
                    help="Importo dell'operazione contabile"
                )
            },
            use_container_width=True,
            height=380
        )
    else:
        st.info("Nessun movimento corrisponde al filtro di ricerca.")
