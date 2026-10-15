"""
Export view for LUCAINVESTRATTO.
Provides one-click generation and download for .PDF, .XLSX, and .TXT reports.
"""
import streamlit as st
from datetime import datetime

from lucainvestratto.db import db
from lucainvestratto.config import BENCHMARKS
from lucainvestratto.export.pdf_report import generate_pdf_report
from lucainvestratto.export.excel_report import generate_excel_report
from lucainvestratto.export.txt_report import generate_txt_report


def render_export_view(selected_account_id: str = "all", selected_account_name: str = "Tutti i conti (Consolidato)"):
    st.subheader("📑 Esportazione Report & Output Finanziari")
    st.markdown("""
    Genera report istituzionali completi esportabili nei formati professionali:
    **PDF (.pdf)**, **Excel Multi-Foglio (.xlsx)** e **Testo ASCII Terminale (.txt)**.
    """)

    accounts = db.get_accounts()
    holdings = db.get_holdings(account_id=selected_account_id)
    transactions = db.get_transactions(account_id=selected_account_id)

    # Benchmark selection for export
    col_bmk, col_date = st.columns([3, 2])
    with col_bmk:
        bmk_keys = list(BENCHMARKS.keys())
        selected_bmk = st.selectbox("Benchmark di confronto per i report:", bmk_keys, index=0)
    with col_date:
        st.info(f"📅 Data generazione: **{datetime.now().strftime('%d/%m/%Y %H:%M')}**")

    # Scope Summary card
    with st.container():
        st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px;">
            <b>Perimetro Report:</b> {selected_account_name} &nbsp;|&nbsp;
            <b>Posizioni Finanziarie:</b> {len(holdings)} titoli &nbsp;|&nbsp;
            <b>Movimenti Estratto Conto:</b> {len(transactions)} transazioni &nbsp;|&nbsp;
            <b>Benchmark:</b> {selected_bmk}
        </div>
        """, unsafe_allow_html=True)

    c_pdf, c_xlsx, c_txt = st.columns(3)

    # 1. PDF Report Card
    with c_pdf:
        st.markdown("### 📄 Report PDF Istituzionale")
        st.markdown("""
        Documento formattato stile **Private Banking / FactSet**:
        - Sintesi patrimoniale & KPI
        - Tabelle Asset Allocation
        - Dettaglio Top Holdings
        - Estratto conto flussi cassa
        """)
        try:
            pdf_bytes = generate_pdf_report(
                accounts=accounts,
                holdings=holdings,
                transactions=transactions,
                account_filter_name=selected_account_name,
                benchmark_code=selected_bmk
            )
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            st.download_button(
                label="📥 Scarica Report .PDF",
                data=pdf_bytes,
                file_name=f"LUCAINVESTRATTO_Report_{now_str}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore generazione PDF: {e}")

    # 2. Excel Report Card
    with c_xlsx:
        st.markdown("### 📊 Cartella Excel (.xlsx)")
        st.markdown("""
        File multi-foglio professionale con stili e formule:
        - Foglio 1: Sintesi & Metriche Rischio
        - Foglio 2: Asset Allocation
        - Foglio 3: Posizioni Portafoglio
        - Foglio 4: Estratto Conto Completo
        """)
        try:
            xlsx_bytes = generate_excel_report(
                accounts=accounts,
                holdings=holdings,
                transactions=transactions,
                account_filter_name=selected_account_name,
                benchmark_code=selected_bmk
            )
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            st.download_button(
                label="📥 Scarica Report .XLSX",
                data=xlsx_bytes,
                file_name=f"LUCAINVESTRATTO_Dati_{now_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore generazione Excel: {e}")

    # 3. TXT Report Card
    with c_txt:
        st.markdown("### 📑 Report Terminale (.txt)")
        st.markdown("""
        Riepilogo monospaziato stile **Bloomberg Terminal**:
        - Formattazione ASCII pulita a griglia
        - Tabelle allineate con metriche di rischio
        - Ideale per archiviazione, log e prompt AI
        """)
        try:
            txt_content = generate_txt_report(
                accounts=accounts,
                holdings=holdings,
                transactions=transactions,
                account_filter_name=selected_account_name,
                benchmark_code=selected_bmk
            )
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            st.download_button(
                label="📥 Scarica Report .TXT",
                data=txt_content,
                file_name=f"LUCAINVESTRATTO_Brief_{now_str}.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore generazione TXT: {e}")

    # Text preview expandable
    with st.expander("👁️ Visualizza anteprima del Report Testuale (.txt)", expanded=False):
        try:
            preview_txt = generate_txt_report(
                accounts=accounts,
                holdings=holdings,
                transactions=transactions,
                account_filter_name=selected_account_name,
                benchmark_code=selected_bmk
            )
            st.code(preview_txt, language="text")
        except Exception as e:
            st.error(f"Errore anteprima: {e}")
