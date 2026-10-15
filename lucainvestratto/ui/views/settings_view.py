"""
Settings and configuration view for LUCAINVESTRATTO.
Includes:
1. Color theme selection and custom color pickers.
2. Custom threshold alerts and active notification center.
3. Selective reset functions (transactions, holdings, date-filtered, accounts).
4. Data recalculation, integrity diagnostics, and running balance alignment.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from lucainvestratto.db import db
from lucainvestratto.settings import load_settings, save_settings, THEME_PRESETS
from lucainvestratto.analytics.notifications import evaluate_alerts
from lucainvestratto.analytics.recalc import run_data_audit, execute_recalculation_and_alignment


def render_settings_view():
    st.subheader("⚙️ Impostazioni, Colori, Alert & Allineamento Dati")
    st.markdown("""
    Personalizza l'interfaccia grafica, imposta soglie di allerta automatiche,
    esegui azzeramenti selettivi del database e ricalcola l'integrità dei dati finanziari.
    """)

    settings = load_settings()
    accounts = db.get_accounts()
    holdings = db.get_holdings()
    transactions = db.get_transactions()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎨 Scelta & Modifica Colori",
        "🔔 Notifiche & Alert Personalizzati",
        "🧹 Azzeramento Selettivo Dati",
        "🔄 Ricalcolo & Allineamento Dati"
    ])

    # ================= TAB 1: MODIFICA E SCELTA COLORI =================
    with tab1:
        st.markdown("#### 🎨 Palette Colori & Personalizzazione Tema Visivo")
        st.markdown("Scegli tra i preset istituzionali o personalizza i colori primari e di accento dell'applicazione.")

        preset_options = list(THEME_PRESETS.keys())
        preset_labels = {k: v["name"] for k, v in THEME_PRESETS.items()}

        current_idx = preset_options.index(settings.theme_preset) if settings.theme_preset in preset_options else 0
        chosen_preset = st.selectbox(
            "Seleziona Tema Predefinito:",
            options=preset_options,
            format_func=lambda k: preset_labels[k],
            index=current_idx
        )

        preset_colors = THEME_PRESETS[chosen_preset]
        
        # Color Preview Badges
        st.markdown(f"""
        <div style="display: flex; gap: 12px; margin: 14px 0 20px 0; align-items: center; flex-wrap: wrap;">
            <div style="background: {preset_colors['primary_color']}; color: #FFF; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 12px;">
                Primario: {preset_colors['primary_color']}
            </div>
            <div style="background: {preset_colors['header_bg_start']}; color: #FFF; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 12px; border: 1px solid #475569;">
                Header: {preset_colors['header_bg_start']}
            </div>
            <div style="background: {preset_colors['accent_color']}; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 12px;">
                Accento: {preset_colors['accent_color']}
            </div>
            <div style="background: {preset_colors['positive_color']}; color: #FFF; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 12px;">
                Guadagni: {preset_colors['positive_color']}
            </div>
            <div style="background: {preset_colors['negative_color']}; color: #FFF; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 12px;">
                Perdite: {preset_colors['negative_color']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 🖌️ Personalizzazione Manuale Colori")
        use_custom = st.checkbox("Abilita colori personalizzati (sovrascrive il preset selezionato)", value=settings.use_custom_colors)

        c_col1, c_col2 = st.columns(2)
        with c_col1:
            custom_p = st.color_picker("Colore Primario (Pulsanti, Indicatori, Badge)", value=settings.custom_primary_color)
        with c_col2:
            custom_a = st.color_picker("Colore Accento (Linee grafici, Evidenziazioni)", value=settings.custom_accent_color)

        if st.button("💾 Salva e Applica Configurazione Colori", type="primary"):
            settings.theme_preset = chosen_preset
            settings.use_custom_colors = use_custom
            settings.custom_primary_color = custom_p
            settings.custom_accent_color = custom_a
            save_settings(settings)
            st.success("Configurazione colori salvata con successo! Ricarica per visualizzare le modifiche.")
            st.rerun()

    # ================= TAB 2: NOTIFICHE E ALERT PERSONALIZZATI =================
    with tab2:
        st.markdown("#### 🔔 Funzione Notifiche & Soglie di Allerta Personalizzate")
        st.markdown("Configura le regole di allerta automatica. Il sistema valuterà in tempo reale i saldi di cassa e il rischio di portafoglio.")

        with st.form("form_notifications"):
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                st.markdown("##### 📉 Soglia Massimo Drawdown Portafoglio")
                en_dd = st.toggle("Abilita Alert Drawdown", value=settings.alert_max_drawdown_enabled)
                val_dd = st.slider("Avvisa se il Drawdown supera il (%):", min_value=1.0, max_value=25.0, value=float(settings.alert_max_drawdown_pct), step=0.5)

                st.markdown("##### 💶 Soglia Giacenza Liquidità Minima")
                en_cash = st.toggle("Abilita Alert Liquidità Minima", value=settings.alert_min_cash_enabled)
                val_cash = st.number_input("Avvisa se la cassa complessiva scende sotto (€):", min_value=500.0, max_value=50000.0, value=float(settings.alert_min_cash_amount), step=500.0)

            with col_a2:
                st.markdown("##### ⚖️ Soglia Concentrazione Singolo Titolo")
                en_weight = st.toggle("Abilita Alert Sovra-Allocazione Titolo", value=settings.alert_max_weight_enabled)
                val_weight = st.slider("Avvisa se un singolo asset supera il (% del portafoglio):", min_value=5.0, max_value=50.0, value=float(settings.alert_max_weight_pct), step=1.0)

                st.markdown("##### 💳 Soglia Uscita / Spesa Rilevante")
                en_exp = st.toggle("Abilita Alert Spese Elevate", value=settings.alert_high_expense_enabled)
                val_exp = st.number_input("Avvisa per singoli addebiti superiori a (€):", min_value=100.0, max_value=10000.0, value=float(settings.alert_high_expense_amount), step=100.0)

            submit_notif = st.form_submit_button("💾 Salva Preferenze Notifiche", type="primary")
            if submit_notif:
                settings.alert_max_drawdown_enabled = en_dd
                settings.alert_max_drawdown_pct = val_dd
                settings.alert_min_cash_enabled = en_cash
                settings.alert_min_cash_amount = val_cash
                settings.alert_max_weight_enabled = en_weight
                settings.alert_max_weight_pct = val_weight
                settings.alert_high_expense_enabled = en_exp
                settings.alert_high_expense_amount = val_exp
                save_settings(settings)
                st.success("Soglie di notifica aggiornate!")
                st.rerun()

        st.divider()
        st.markdown("#### 🚨 Centro Notifiche Attive in Tempo Reale")
        active_alerts = evaluate_alerts(settings, accounts, holdings, transactions)
        
        if not active_alerts:
            st.success("✅ Nessun alert attivo. Tutti i parametri di liquidità, drawdown e concentrazione rientrano nelle soglie di sicurezza.")
        else:
            for alert in active_alerts:
                box_class = f"notif-{alert.level}"
                st.markdown(f"""
                <div class="notif-box {box_class}">
                    <span style="font-size: 24px;">{alert.icon}</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 700; font-size: 14px;">{alert.title}</div>
                        <div style="font-size: 13px; margin-top: 3px;">{alert.message}</div>
                        <div style="font-size: 11.5px; margin-top: 5px; opacity: 0.85;">
                            Valore Rilevato: <b>{alert.current_value}</b> &nbsp;|&nbsp; Soglia Limite: <b>{alert.threshold_value}</b>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ================= TAB 3: AZZERAMENTO SELETTIVO =================
    with tab3:
        st.markdown("#### 🧹 Funzioni di Azzeramento Selettivo del Database")
        st.markdown("Puoi ripulire in modo mirato solo determinati dati (es. solo le transazioni o solo i titoli), senza perdere l'intera configurazione.")

        acc_choices = {"all": "Tutti i conti"}
        for a in accounts:
            acc_choices[a.id] = f"{a.name} ({a.bank_name or a.currency})"

        c_reset1, c_reset2 = st.columns(2)

        # 1. Reset Transactions Only
        with c_reset1:
            with st.container(border=True):
                st.markdown("##### 📄 Azzeramento Estratto Conto (Transazioni)")
                st.caption("Elimina i movimenti bancari mantenendo intatti i conti creati e le posizioni di portafoglio.")
                sel_acc_tx = st.selectbox("Perimetro conto da azzerare:", options=list(acc_choices.keys()), format_func=lambda k: acc_choices[k], key="reset_tx_acc")
                
                en_date_filter = st.checkbox("Filtra per data di operazione", key="en_date_del")
                del_before = None
                if en_date_filter:
                    del_before = st.date_input("Elimina solo transazioni fino al (compreso):", value=date.today() - timedelta(days=90))

                if st.button("🗑️ Elimina Transazioni Selezionate", type="secondary", key="btn_del_tx"):
                    if del_before:
                        count = db.clear_transactions_by_date(before_date=del_before.isoformat(), account_id=sel_acc_tx)
                        st.success(f"Eliminate {count} transazioni anteriori al {del_before}.")
                    else:
                        db.clear_transactions(account_id=sel_acc_tx)
                        st.success("Transazioni eliminate con successo.")
                    st.rerun()

        # 2. Reset Holdings Only
        with c_reset2:
            with st.container(border=True):
                st.markdown("##### 💼 Azzeramento Portafoglio (Titoli ed Asset)")
                st.caption("Elimina le posizioni finanziarie mantenendo intatti i conti bancari e l'estratto conto dei movimenti.")
                sel_acc_h = st.selectbox("Perimetro titoli da azzerare:", options=list(acc_choices.keys()), format_func=lambda k: acc_choices[k], key="reset_h_acc")
                
                if st.button("🗑️ Elimina Posizioni Selezionate", type="secondary", key="btn_del_h"):
                    db.clear_holdings(account_id=sel_acc_h)
                    st.success("Titoli di portafoglio eliminati con successo.")
                    st.rerun()

        # 3. Factory Reset with Safeguard
        st.markdown("---")
        with st.container(border=True):
            st.markdown("##### ⚠️ Ripristino Totale di Fabbrica (Factory Reset)")
            st.markdown("Questa operazione eliminerà **tutti i conti, tutti i movimenti e tutti i titoli** presenti nel database.")
            
            chk_confirm = st.checkbox("Sono consapevole che questa operazione cancellerà permanentemente tutti i dati.", key="chk_factory")
            txt_confirm = st.text_input("Digita 'CONFERMA' in maiuscolo per abilitare l'azzeramento totale:", key="txt_factory")

            if st.button("🚨 Esegui Reset Totale di Fabbrica", type="primary", disabled=(not chk_confirm or txt_confirm.strip() != "CONFERMA")):
                db.factory_reset()
                st.success("Database completamente azzerato!")
                st.rerun()

    # ================= TAB 4: RICALCOLO E ALLINEAMENTO DATI =================
    with tab4:
        st.markdown("#### 🔄 Funzioni di Ricalcolo per Allineamento Dati")
        st.markdown("""
        Controlla la coerenza del database, verifica la corrispondenza dei saldi progressivi,
        identifica duplicati o record orfani e ricalcola i pesi e i valori di portafoglio.
        """)

        audit = run_data_audit()

        # Top Diagnostic Metric Badges
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Conti Attivi", audit.total_accounts)
        with d2:
            st.metric("Movimenti Rilevati", audit.total_transactions, delta=f"{audit.duplicate_transactions_count} duplicati", delta_color="inverse" if audit.duplicate_transactions_count > 0 else "off")
        with d3:
            st.metric("Titoli Registrati", audit.total_holdings, delta=f"{audit.orphaned_holdings_count} orfani", delta_color="inverse" if audit.orphaned_holdings_count > 0 else "off")
        with d4:
            st.metric("Stato Integrità", audit.status)

        if audit.issues_found:
            st.warning("⚠️ Rilevate anomalie nell'allineamento dei dati:")
            for issue in audit.issues_found:
                st.markdown(f"- {issue}")
        else:
            st.success("✅ Integrità dei dati verificata: nessun record orfano, duplicato o sbilanciamento rilevato.")

        st.markdown("##### 📊 Tabella di Riconciliazione Saldi per Conto")
        if audit.account_balances:
            df_reconcile = pd.DataFrame(audit.account_balances)
            st.dataframe(
                df_reconcile.style.format({
                    "Saldo Iniziale": "€ {:,.2f}",
                    "Flusso Transazioni": "€ {:+,.2f}",
                    "Liquidità Effettiva": "€ {:,.2f}",
                    "Portafoglio Investito": "€ {:,.2f}",
                    "Patrimonio Totale": "€ {:,.2f}"
                }),
                use_container_width=True
            )

        st.divider()
        st.markdown("##### 🚀 Esegui Azione di Allineamento e Ripulitura Automatica")
        st.caption("Rimuove automaticamente eventuali record duplicati o orfani e ricalcola le quote del portafoglio.")
        
        if st.button("⚡ Avvia Ricalcolo & Allineamento Automatico", type="primary"):
            result = execute_recalculation_and_alignment()
            st.success(f"✅ {result['message']}")
            st.rerun()
