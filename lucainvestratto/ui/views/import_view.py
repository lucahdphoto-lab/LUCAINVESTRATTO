"""
Import view for LUCAINVESTRATTO.
Handles uploading and importing files in .xlsx, .csv, .txt, .png, and .jpg formats,
plus manual entry forms for transactions and portfolio holdings.
"""
import streamlit as st
import pandas as pd
from typing import List

from lucainvestratto.db import db
from lucainvestratto.models import Transaction, Holding
from lucainvestratto.parsers import parse_statement_file
from lucainvestratto.config import TRANSACTION_TYPES, TRANSACTION_CATEGORIES, ASSET_CLASSES


def render_import_view():
    st.subheader("📥 Importazione Dati & Documenti")
    st.markdown("""
    Carica file di estratto conto bancario o screenshot di portafoglio.
    Formati supportati: **.XLSX**, **.CSV**, **.TXT**, **.PNG**, **.JPG**.
    """)

    accounts = db.get_accounts()
    if not accounts:
        st.warning("Devi prima creare o selezionare almeno un conto bancario nella sezione 'Gestione Conti'.")
        return

    account_map = {f"{a.name} ({a.bank_name or a.currency})": a.id for a in accounts}
    selected_acc_label = st.selectbox("Seleziona il conto bancario di destinazione:", list(account_map.keys()))
    selected_account_id = account_map[selected_acc_label]

    tab1, tab2, tab3 = st.tabs(["📁 Carica File (.xlsx, .csv, .txt, .png, .jpg)", "➕ Inserimento Manuale Transazione", "➕ Inserimento Manuale Posizione"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Scegli un file da importare:",
            type=["xlsx", "xls", "csv", "txt", "png", "jpg", "jpeg"],
            help="Carica un foglio Excel, file CSV, testo estratto conto o screenshot."
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name

            st.info(f"File selezionato: **{filename}** ({len(file_bytes) / 1024:.1f} KB)")

            # Parse file
            with st.spinner("Analisi e decodifica del file in corso..."):
                parse_result = parse_statement_file(file_bytes, filename, selected_account_id)

            if not parse_result.success:
                st.error(f"❌ {parse_result.message}")
            else:
                st.success(f"✅ {parse_result.message}")

                # Preview Raw DF if available
                if parse_result.raw_df_preview is not None:
                    with st.expander("🔍 Anteprima righe file grezzo", expanded=False):
                        st.dataframe(parse_result.raw_df_preview, use_container_width=True)

                # Show extracted transactions
                if parse_result.transactions:
                    st.markdown(f"#### 📄 Movimenti Estratti ({len(parse_result.transactions)} righe)")
                    preview_data = [
                        {
                            "Data": tx.date,
                            "Tipo": tx.type,
                            "Categoria": tx.category,
                            "Importo (€)": f"€ {tx.amount:,.2f}",
                            "Descrizione": tx.description
                        }
                        for tx in parse_result.transactions[:25]
                    ]
                    st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

                    if st.button("🚀 Conferma ed Importa Transazioni nel Database", type="primary"):
                        saved = db.save_transactions(parse_result.transactions)
                        st.success(f"Importate con successo {saved} transazioni nel conto selezionato!")
                        st.rerun()

                # Show extracted holdings
                if parse_result.holdings:
                    st.markdown(f"#### 💼 Posizioni di Portafoglio Estratte ({len(parse_result.holdings)} titoli)")
                    preview_holdings = [
                        {
                            "Simbolo": h.symbol,
                            "Nome": h.name,
                            "Asset Class": h.asset_class,
                            "Quantità": h.quantity,
                            "PMC (€)": f"€ {h.average_buy_price:,.2f}",
                            "Prezzo (€)": f"€ {h.current_price:,.2f}",
                            "Controvalore (€)": f"€ {h.market_value:,.2f}"
                        }
                        for h in parse_result.holdings
                    ]
                    st.dataframe(pd.DataFrame(preview_holdings), use_container_width=True)

                    if st.button("🚀 Conferma ed Importa Posizioni nel Portafoglio", type="primary"):
                        saved = db.save_holdings(parse_result.holdings)
                        st.success(f"Importate con successo {saved} posizioni nel portafoglio!")
                        st.rerun()

    with tab2:
        st.markdown("#### Registrazione Singola Transazione / Movimento")
        with st.form("manual_tx_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tx_date = st.date_input("Data Operazione")
                tx_type = st.selectbox("Tipologia Movimento", TRANSACTION_TYPES)
                tx_cat = st.selectbox("Categoria", TRANSACTION_CATEGORIES)
                tx_amt = st.number_input("Importo (€) [usa il segno meno per le uscite]", value=0.0, step=10.0)
            with col2:
                tx_desc = st.text_input("Descrizione / Causale", placeholder="es. Stipendio, Spesa supermercato, Acquisto titolo")
                tx_sym = st.text_input("Simbolo Asset (opzionale)", placeholder="es. SWDA.MI, AAPL")
                tx_fee = st.number_input("Commissioni / Spese (€)", value=0.0, min_value=0.0, step=1.0)
                tx_note = st.text_input("Note aggiuntive", placeholder="Note personali")

            submitted_tx = st.form_submit_button("Aggiungi Transazione", type="primary")
            if submitted_tx:
                if tx_amt == 0.0:
                    st.error("L'importo non può essere zero.")
                else:
                    new_tx = Transaction(
                        account_id=selected_account_id,
                        date=tx_date.isoformat(),
                        type=tx_type,
                        category=tx_cat,
                        amount=tx_amt,
                        description=tx_desc.strip() or "Movimento manuale",
                        asset_symbol=tx_sym.strip() or None,
                        fees=tx_fee,
                        notes=tx_note.strip()
                    )
                    db.save_transaction(new_tx)
                    st.success("Transazione registrata con successo!")
                    st.rerun()

    with tab3:
        st.markdown("#### Registrazione Singolo Titolo / Posizione in Portafoglio")
        with st.form("manual_holding_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                h_sym = st.text_input("Ticker o ISIN *", placeholder="es. SWDA.MI o IT0005240830")
                h_name = st.text_input("Nome Strumento *", placeholder="es. iShares Core MSCI World")
                h_class = st.selectbox("Asset Class", ASSET_CLASSES)
                h_sector = st.text_input("Settore", placeholder="es. Tecnologia, Finanziari, Sovrani")
                h_geo = st.text_input("Area Geografica", placeholder="es. Globale, USA, Europa, Italia")
            with c2:
                h_qty = st.number_input("Quantità / Quote possedute *", min_value=0.0001, value=10.0, step=1.0)
                h_pmc = st.number_input("Prezzo Medio di Carico (PMC in €) *", min_value=0.01, value=100.0, step=1.0)
                h_price = st.number_input("Prezzo Attuale di Mercato (€) *", min_value=0.01, value=105.0, step=1.0)
                h_yield = st.number_input("Dividend / Coupon Yield Annuale (%)", min_value=0.0, value=1.5, step=0.1)
                h_dur = st.number_input("Duration (per obbligazioni)", min_value=0.0, value=0.0, step=0.5)

            h_notes = st.text_area("Note", placeholder="Strategia, orizzonte temporale, stop loss")
            submitted_holding = st.form_submit_button("Aggiungi Titolo al Portafoglio", type="primary")

            if submitted_holding:
                if not h_sym.strip() or not h_name.strip():
                    st.error("Simbolo e Nome dello strumento sono obbligatori.")
                else:
                    new_h = Holding(
                        account_id=selected_account_id,
                        symbol=h_sym.strip(),
                        name=h_name.strip(),
                        asset_class=h_class,
                        sector=h_sector.strip() or "Generale",
                        geography=h_geo.strip() or "Globale",
                        quantity=h_qty,
                        average_buy_price=h_pmc,
                        current_price=h_price,
                        annual_dividend_yield=h_yield,
                        duration=h_dur,
                        notes=h_notes.strip()
                    )
                    db.save_holding(new_h)
                    st.success(f"Posizione '{new_h.symbol}' aggiunta al portafoglio!")
                    st.rerun()
