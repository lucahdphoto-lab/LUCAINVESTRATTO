"""
Multi-bank account management view for LUCAINVESTRATTO.
Allows adding, modifying, inspecting, and deleting bank accounts.
"""
import streamlit as st
import pandas as pd
from typing import List

from lucainvestratto.models import BankAccount
from lucainvestratto.db import db
from lucainvestratto.config import ACCOUNT_TYPES, SUPPORTED_CURRENCIES
from lucainvestratto.ui.theme import render_metric_card


def render_accounts_view():
    st.subheader("🏦 Gestione Multi-Conto Bancario")
    st.markdown("Gestisci tutti i tuoi conti correnti, dossier titoli, conti deposito e broker in un'unica interfaccia centralizzata.")

    accounts = db.get_accounts()
    all_transactions = db.get_transactions()
    all_holdings = db.get_holdings()

    # Top summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Conti Registrati", str(len(accounts)), "Istituti bancari e broker", "neutral")
    with col2:
        tot_liquidita_init = sum(a.initial_balance for a in accounts)
        render_metric_card("Liquidità Iniziale", f"€ {tot_liquidita_init:,.2f}", "Saldi base aggregati", "neutral")
    with col3:
        tot_holdings_val = sum(h.market_value for h in all_holdings)
        render_metric_card("Valore Investimenti", f"€ {tot_holdings_val:,.2f}", f"{len(all_holdings)} strumenti attivi", "positive")
    with col4:
        tot_tx_count = len(all_transactions)
        render_metric_card("Totale Movimenti", f"{tot_tx_count:,}", "Registrati nel database", "neutral")

    st.divider()

    # List of accounts
    st.markdown("#### 📋 Elenco Conti Collegati")
    if not accounts:
        st.info("Nessun conto bancario presente. Aggiungi il tuo primo conto oppure carica i dati demo di esempio.")
    else:
        for acc in accounts:
            acc_txs = [t for t in all_transactions if t.account_id == acc.id]
            acc_holdings = [h for h in all_holdings if h.account_id == acc.id]
            
            # Compute current cash balance
            net_flow = sum(t.amount for t in acc_txs)
            current_cash = acc.initial_balance + net_flow
            inv_value = sum(h.market_value for h in acc_holdings)
            total_account_wealth = current_cash + inv_value

            with st.expander(f"🏦 **{acc.name}** ({acc.bank_name or 'Istituto Bancario'}) — Patrimonio: € {total_account_wealth:,.2f}", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Liquidità Corrente", f"€ {current_cash:,.2f}", delta=f"Flusso: € {net_flow:+,.2f}")
                c2.metric("Portafoglio Titoli", f"€ {inv_value:,.2f}", delta=f"{len(acc_holdings)} posizioni")
                c3.metric("Tipologia Conto", acc.account_type)
                c4.metric("Valuta Base", acc.currency)

                if acc.iban:
                    st.caption(f"**IBAN / Identificativo:** `{acc.iban}`")
                if acc.notes:
                    st.caption(f"**Note:** {acc.notes}")

                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    if st.button("🗑️ Elimina Conto", key=f"del_acc_{acc.id}", type="secondary"):
                        db.delete_account(acc.id)
                        st.toast(f"Conto '{acc.name}' eliminato con successo.")
                        st.rerun()

    st.divider()

    # Add new account form
    st.markdown("#### ➕ Aggiungi un Nuovo Conto Bancario")
    with st.form("form_add_account", clear_on_submit=True):
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            name = st.text_input("Nome Conto / Riferimento *", placeholder="es. Fineco Trading & Titoli")
            bank_name = st.text_input("Banca o Broker", placeholder="es. FinecoBank S.p.A.")
            account_type = st.selectbox("Tipologia Conto", ACCOUNT_TYPES, index=0)
        with fcol2:
            currency = st.selectbox("Valuta", SUPPORTED_CURRENCIES, index=0)
            initial_balance = st.number_input("Saldo Iniziale / Di Partenza (€)", min_value=0.0, value=0.0, step=100.0)
            iban = st.text_input("IBAN o Codice Dossier", placeholder="IT00X0000000000000000000000")

        notes = st.text_area("Note o Dettagli Aggiuntivi", placeholder="Inserisci note sulla gestione, commissioni o referente bancario.")
        submit = st.form_submit_button("Salva Conto Bancario", type="primary")

        if submit:
            if not name.strip():
                st.error("Il nome del conto è obbligatorio.")
            else:
                new_acc = BankAccount(
                    name=name.strip(),
                    bank_name=bank_name.strip(),
                    account_type=account_type,
                    currency=currency,
                    iban=iban.strip(),
                    initial_balance=initial_balance,
                    notes=notes.strip()
                )
                db.save_account(new_acc)
                st.success(f"Conto '{new_acc.name}' creato con successo!")
                st.rerun()

    # Demo dataset section
    st.divider()
    st.markdown("#### 🎲 Dati di Esempio / Demo Dataset")
    st.caption("Vuoi testare immediatamente tutte le funzionalità con conti realistici, transazioni ed investimenti?")
    c_demo1, c_demo2 = st.columns([2, 3])
    with c_demo1:
        if st.button("🔄 Ricarica Dataset Demo Completo", type="secondary"):
            db.load_demo_data(reset=True)
            st.success("Dataset demo ricaricato con successo!")
            st.rerun()
