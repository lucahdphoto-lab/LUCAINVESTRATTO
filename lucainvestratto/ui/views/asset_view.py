"""
Asset allocation and holdings analysis view (Analisi per Asset) for LUCAINVESTRATTO.
Displays breakdown by asset class, geography, sector, currency,
PMC comparison, unrealized P&L, and dividend income yields.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime

from lucainvestratto.db import db
from lucainvestratto.models import Holding
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.ui.theme import render_metric_card
from lucainvestratto.export.excel_report import generate_dataframe_excel


def render_asset_view(selected_account_id: str = "all"):
    st.subheader("💼 Analisi di Portafoglio per Asset & Asset Class")
    st.markdown("Monitoraggio delle posizioni finanziarie, pesi percentuali, prezzo medio di carico (PMC) e plusvalenze latenti.")

    holdings = db.get_holdings(account_id=selected_account_id)
    if not holdings:
        st.info("Nessuna posizione finanziaria registrata per il conto selezionato. Aggiungi titoli nella sezione 'Import Dati'.")
        return

    summary = calculate_asset_summary(holdings)

    # 1. Top KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Valore Portafoglio", f"€ {summary['total_market_value']:,.2f}", f"{summary['count']} titoli attivi", "neutral")
    with col2:
        render_metric_card("Costo Storico (PMC)", f"€ {summary['total_invested']:,.2f}", "Capitale investito", "neutral")
    with col3:
        pl = summary["total_unrealized_pl"]
        pl_pct = summary["total_unrealized_pl_pct"]
        trend = "positive" if pl >= 0 else "negative"
        render_metric_card("P&L Latente (€)", f"€ {pl:+,.2f}", f"{pl_pct:+.2f}% sul capitale", trend)
    with col4:
        render_metric_card("Entrate Dividendi/Cedole", f"€ {summary['expected_annual_income']:,.2f}", "Flusso annuo stimato", "positive")
    with col5:
        render_metric_card("Yield Portafoglio", f"{summary['portfolio_dividend_yield']:.2f}%", "Rendimento cedolare medio", "neutral")

    st.divider()

    # 2. Charts Row: Allocation by Class and Geography
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        st.markdown("#### 🎯 Asset Allocation per Classe di Strumento")
        df_class = summary["df_by_class"]
        if not df_class.empty:
            fig_class = px.pie(
                df_class,
                names="asset_class",
                values="market_value",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_class.update_traces(textposition="inside", textinfo="percent+label")
            fig_class.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320, showlegend=False)
            st.plotly_chart(fig_class, use_container_width=True)

    with c_chart2:
        st.markdown("#### 🌍 Esposizione Geografica")
        df_geo = summary["df_by_geography"]
        if not df_geo.empty:
            fig_geo = px.pie(
                df_geo,
                names="geography",
                values="market_value",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_geo.update_traces(textposition="inside", textinfo="percent+label")
            fig_geo.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320, showlegend=False)
            st.plotly_chart(fig_geo, use_container_width=True)

    # 3. Charts Row: Performance by Asset (Top Gainers / Losers)
    st.markdown("#### 📊 Rendimento % per Singolo Strumento Finanziario (P&L Latente)")
    df_h = summary["df_holdings"].copy()
    if not df_h.empty:
        df_h.sort_values(by="unrealized_pl_pct", ascending=True, inplace=True)
        colors_list = ["#16A34A" if val >= 0 else "#DC2626" for val in df_h["unrealized_pl_pct"]]
        
        fig_perf = go.Figure(go.Bar(
            x=df_h["unrealized_pl_pct"],
            y=df_h["symbol"] + " (" + df_h["name"].str.slice(0, 18) + ")",
            orientation="h",
            marker_color=colors_list,
            text=df_h["unrealized_pl_pct"].apply(lambda v: f"{v:+.2f}%"),
            textposition="outside"
        ))
        fig_perf.update_layout(
            margin=dict(l=10, r=40, t=10, b=10),
            height=max(280, len(df_h) * 32),
            xaxis_title="Plus/Minusvalenza (%)",
            template="plotly_white"
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    st.divider()

    # 4. Detailed Holdings Table
    st.markdown("#### 📋 Tabella Dettagliata Posizioni in Portafoglio")
    
    display_cols = [
        "symbol", "name", "asset_class", "quantity", "average_buy_price",
        "current_price", "total_cost", "market_value", "unrealized_pl",
        "unrealized_pl_pct", "weight_pct", "annual_dividend_yield"
    ]
    df_table = df_h[display_cols].copy()
    df_table.columns = [
        "Simbolo", "Nome Titolo", "Classe", "Quantità", "PMC (€)",
        "Prezzo Attuale (€)", "Costo Totale (€)", "Controvalore (€)",
        "P&L (€)", "P&L (%)", "Peso (%)", "Yield (%)"
    ]

    # Ensure numeric columns are float
    numeric_cols = ["Quantità", "PMC (€)", "Prezzo Attuale (€)", "Costo Totale (€)", "Controvalore (€)", "P&L (€)", "P&L (%)", "Peso (%)", "Yield (%)"]
    for nc in numeric_cols:
        df_table[nc] = pd.to_numeric(df_table[nc], errors="coerce").fillna(0.0)

    c_tbl, c_dl = st.columns([3, 1])
    with c_dl:
        now_str = datetime.now().strftime('%Y%m%d_%H%M')
        # 1. Excel (.xlsx) export with native numbers, right-aligned, and totals
        xlsx_data = generate_dataframe_excel(
            df=df_table,
            title="LUCAINVESTRATTO - Portafoglio & Posizioni Dettagliate",
            sheet_name="Posizioni",
            currency_cols=["PMC (€)", "Prezzo Attuale (€)", "Costo Totale (€)", "Controvalore (€)", "P&L (€)"],
            pct_cols=["P&L (%)", "Peso (%)", "Yield (%)"],
            qty_cols=["Quantità"],
            center_cols=["Simbolo"],
            sum_cols=["Costo Totale (€)", "Controvalore (€)", "P&L (€)"]
        )
        st.download_button(
            label="📥 Esporta Excel (.xlsx)",
            data=xlsx_data,
            file_name=f"LUCAINVESTRATTO_Posizioni_{now_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
            help="File Excel nativo con numeri formattati come Valuta/Percentuale/Quantità e allineati rigorosamente a DESTRA."
        )

        # 2. Italian Excel CSV export (; separator, , decimal)
        csv_data = df_table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            label="📥 Esporta CSV (Excel IT)",
            data=csv_data,
            file_name=f"LUCAINVESTRATTO_Posizioni_{now_str}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Formato CSV con ';' e decimale virgola ',' per apertura diretta in Microsoft Excel con numeri riconosciuti e allineati a destra."
        )

    st.dataframe(
        df_table,
        column_config={
            "Quantità": st.column_config.NumberColumn(format="%.4f"),
            "PMC (€)": st.column_config.NumberColumn(format="€ %.2f"),
            "Prezzo Attuale (€)": st.column_config.NumberColumn(format="€ %.2f"),
            "Costo Totale (€)": st.column_config.NumberColumn(format="€ %.2f"),
            "Controvalore (€)": st.column_config.NumberColumn(format="€ %.2f"),
            "P&L (€)": st.column_config.NumberColumn(format="€ %.2f"),
            "P&L (%)": st.column_config.NumberColumn(format="%.2f %%"),
            "Peso (%)": st.column_config.NumberColumn(format="%.2f %%"),
            "Yield (%)": st.column_config.NumberColumn(format="%.2f %%"),
        },
        use_container_width=True,
        height=360
    )


    # 5. Quick Price Updater / Position Management
    with st.expander("✏️ Aggiorna Prezzo di Mercato o Gestisci Posizione"):
        h_sym_list = [h.symbol for h in holdings]
        selected_sym = st.selectbox("Seleziona Strumento da aggiornare:", h_sym_list)
        target_h = next((h for h in holdings if h.symbol == selected_sym), None)

        if target_h:
            ucol1, ucol2, ucol3 = st.columns(3)
            with ucol1:
                new_price = st.number_input("Nuovo Prezzo di Mercato (€)", value=float(target_h.current_price), step=1.0)
            with ucol2:
                new_qty = st.number_input("Quantità Posseduta", value=float(target_h.quantity), step=1.0)
            with ucol3:
                new_pmc = st.number_input("Prezzo Medio di Carico (PMC in €)", value=float(target_h.average_buy_price), step=1.0)

            c_act1, c_act2 = st.columns([1, 4])
            with c_act1:
                if st.button("💾 Salva Modifiche", type="primary"):
                    target_h.current_price = new_price
                    target_h.quantity = new_qty
                    target_h.average_buy_price = new_pmc
                    db.save_holding(target_h)
                    st.success(f"Posizione {target_h.symbol} aggiornata!")
                    st.rerun()
            with c_act2:
                if st.button("🗑️ Rimuovi Posizione", type="secondary"):
                    db.delete_holding(target_h.id)
                    st.toast(f"Posizione {target_h.symbol} eliminata.")
                    st.rerun()
