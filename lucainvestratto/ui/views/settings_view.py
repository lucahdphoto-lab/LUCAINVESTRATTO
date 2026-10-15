"""
Settings and configuration view for LUCAINVESTRATTO.
Includes:
1. Color theme selection, custom color pickers, degrading gradients (buttons and windows),
   external background image customization, and glassmorphism transparency controls.
2. Custom threshold alerts and active notification center.
3. Selective reset functions (transactions, holdings, date-filtered, accounts).
4. Data recalculation, integrity diagnostics, and running balance alignment.
"""
import base64
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from lucainvestratto.db import db
from lucainvestratto.settings import (
    load_settings, save_settings, THEME_PRESETS, PRESET_BACKGROUND_IMAGES, hex_to_rgba
)
from lucainvestratto.analytics.notifications import evaluate_alerts
from lucainvestratto.analytics.recalc import run_data_audit, execute_recalculation_and_alignment


def render_settings_view():
    st.subheader("⚙️ Impostazioni: Colori, Sfumature, Sfondo, Trasparenze & Alert")
    st.markdown("""
    Personalizza l'aspetto visivo con **sfumature degradanti**, **immagini di sfondo esterne**,
    **regolazione delle trasparenze (effetto vetro satinato)**, imposta regole di alert e gestisci l'integrità del database.
    """)

    settings = load_settings()
    accounts = db.get_accounts()
    holdings = db.get_holdings()
    transactions = db.get_transactions()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎨 Colori, Sfumature & Sfondo",
        "🔔 Notifiche & Alert Personalizzati",
        "🧹 Azzeramento Selettivo Dati",
        "🔄 Ricalcolo & Allineamento Dati"
    ])

    # ================= TAB 1: MODIFICA E SCELTA COLORI, SFUMATURE, SFONDO, TRASPARENZE =================
    with tab1:
        st.markdown("#### 🎨 Palette & Temi Finanziari Predefiniti")
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
        <div style="display: flex; gap: 10px; margin: 10px 0 16px 0; align-items: center; flex-wrap: wrap;">
            <div style="background: {preset_colors['primary_color']}; color: #FFF; padding: 5px 12px; border-radius: 6px; font-weight: 600; font-size: 11.5px;">
                Primario: {preset_colors['primary_color']}
            </div>
            <div style="background: {preset_colors['header_bg_start']}; color: #FFF; padding: 5px 12px; border-radius: 6px; font-weight: 600; font-size: 11.5px; border: 1px solid #475569;">
                Header: {preset_colors['header_bg_start']}
            </div>
            <div style="background: {preset_colors['accent_color']}; color: #000; padding: 5px 12px; border-radius: 6px; font-weight: 600; font-size: 11.5px;">
                Accento: {preset_colors['accent_color']}
            </div>
            <div style="background: {preset_colors['positive_color']}; color: #FFF; padding: 5px 12px; border-radius: 6px; font-weight: 600; font-size: 11.5px;">
                Guadagni: {preset_colors['positive_color']}
            </div>
            <div style="background: {preset_colors['negative_color']}; color: #FFF; padding: 5px 12px; border-radius: 6px; font-weight: 600; font-size: 11.5px;">
                Perdite: {preset_colors['negative_color']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        # 1. SFUMATURE DEGRADANTI
        st.markdown("#### 🌈 1. Sfumature Degradanti per Finestre e Pulsanti")
        st.caption("Configura sfumature cromatiche dinamiche a due o più tonalità per bottoni e riquadri informativi.")

        c_grad1, c_grad2 = st.columns(2)
        with c_grad1:
            st.markdown("##### 🔘 Sfumatura Degradante Pulsanti")
            grad_btn_en = st.toggle("Abilita Gradiente sui Pulsanti", value=settings.gradient_buttons_enabled)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                btn_start = st.color_picker("Colore Iniziale Gradiente Pulsante", value=settings.gradient_btn_start)
            with col_b2:
                btn_end = st.color_picker("Colore Finale Gradiente Pulsante", value=settings.gradient_btn_end)

            # Live preview of button
            st.markdown(f"""
            <div style="margin-top: 8px;">
                <button style="background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%); color: #FFF; border: none; border-radius: 8px; padding: 8px 18px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: pointer;">
                    Anteprima Pulsante con Sfumatura ✨
                </button>
            </div>
            """, unsafe_allow_html=True)

        with c_grad2:
            st.markdown("##### 🪟 Sfumatura Degradante Finestre e Card")
            grad_card_en = st.toggle("Abilita Gradiente sulle Card", value=settings.gradient_cards_enabled)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                card_start = st.color_picker("Colore Iniziale Card", value=settings.gradient_card_start)
            with col_c2:
                card_end = st.color_picker("Colore Finale Card", value=settings.gradient_card_end)

        st.markdown("---")
        # 2. SFONDO CON IMMAGINI ESTERNE
        st.markdown("#### 🖼️ 2. Modifica Sfondo con Immagini Esterne")
        st.caption("Imposta una grafica di sfondo ad alta definizione (trading floor, architettura o URL personalizzato).")

        bg_mode_options = [
            "Colore Piatto / Gradiente Standard",
            "Wallpaper Finanziari ad Alta Definizione (Preset)",
            "URL Immagine Esterna Web",
            "Carica File Immagine dal Tuo Computer (.jpg, .png)"
        ]
        
        # Determine initial selection index
        init_bg_idx = 0
        if settings.background_type == "image_preset":
            init_bg_idx = 1
        elif settings.background_type == "image_url":
            init_bg_idx = 2
        elif settings.background_type == "image_upload":
            init_bg_idx = 3

        selected_bg_mode = st.radio(
            "Modalità Sfondo Applicazione:",
            options=bg_mode_options,
            index=init_bg_idx
        )

        bg_type_selected = "default"
        bg_preset_selected = settings.background_preset_key
        bg_url_selected = settings.background_image_url
        bg_base64_selected = settings.background_image_base64

        if selected_bg_mode == "Wallpaper Finanziari ad Alta Definizione (Preset)":
            bg_type_selected = "image_preset"
            preset_img_keys = list(PRESET_BACKGROUND_IMAGES.keys())
            curr_p_idx = preset_img_keys.index(settings.background_preset_key) if settings.background_preset_key in preset_img_keys else 1
            bg_preset_selected = st.selectbox("Scegli Wallpaper Istituzionale:", preset_img_keys, index=curr_p_idx)
            
            chosen_url = PRESET_BACKGROUND_IMAGES[bg_preset_selected]
            if chosen_url:
                st.image(chosen_url, caption=f"Anteprima: {bg_preset_selected}", use_container_width=True)

        elif selected_bg_mode == "URL Immagine Esterna Web":
            bg_type_selected = "image_url"
            bg_url_selected = st.text_input(
                "Inserisci URL pubblico dell'immagine (.jpg, .png):",
                value=settings.background_image_url,
                placeholder="https://images.unsplash.com/photo-..."
            )
            if bg_url_selected.strip():
                try:
                    st.image(bg_url_selected.strip(), caption="Anteprima Immagine da URL", use_container_width=True)
                except Exception:
                    st.caption("Inserisci un link diretto valido a un'immagine web.")

        elif selected_bg_mode == "Carica File Immagine dal Tuo Computer (.jpg, .png)":
            bg_type_selected = "image_upload"
            uploaded_bg = st.file_uploader("Seleziona file immagine da impostare come sfondo:", type=["png", "jpg", "jpeg", "webp"])
            if uploaded_bg is not None:
                img_bytes = uploaded_bg.read()
                mime = uploaded_bg.type or "image/jpeg"
                bg_base64_selected = f"data:{mime};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
                st.image(img_bytes, caption="Immagine caricata per lo sfondo", use_container_width=True)
            elif settings.background_image_base64:
                st.caption("Immagine caricata in precedenza già memorizzata.")
        else:
            bg_type_selected = "default"

        overlay_op = st.slider(
            "Opacità Velo di Copertura Sfondo (% scurezza per massima leggibilità testi):",
            min_value=10, max_value=98, value=int(settings.background_overlay_opacity * 100), step=2
        )

        st.markdown("---")
        # 3. REGOLAZIONE TRASPARENZE E EFFETTO GLASSMORPHISM
        st.markdown("#### 🪟 3. Regolazione Trasparenze & Effetto Vetro Satinato (Glassmorphism)")
        st.caption("Modifica l'opacità e la sfocatura delle finestre e delle card per far trasparire lo sfondo.")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            card_op = st.slider("Opacità Finestre e Card (%)", min_value=20, max_value=100, value=int(settings.card_opacity_pct), step=5)
        with col_t2:
            blur_px = st.slider("Intensità Sfocatura Vetro (Blur in px)", min_value=0, max_value=30, value=int(settings.card_blur_px), step=2)
        with col_t3:
            side_op = st.slider("Opacità Barra Laterale Sidebar (%)", min_value=40, max_value=100, value=int(settings.sidebar_opacity_pct), step=5)

        # Live Interactive Glass Preview
        st.markdown("##### 🔍 Anteprima Effetto Trasparenza in Tempo Reale")
        glass_preview_rgba = hex_to_rgba(card_start, opacity=card_op / 100.0)
        st.markdown(f"""
        <div style="background: {glass_preview_rgba}; backdrop-filter: blur({blur_px}px); -webkit-backdrop-filter: blur({blur_px}px); border: 1px solid rgba(255,255,255,0.3); border-radius: 12px; padding: 18px; margin: 10px 0; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.18);">
            <div style="font-weight: 700; font-size: 16px; margin-bottom: 6px;">✨ Finestra Glassmorphism con Trasparenza al {card_op}% e Blur {blur_px}px</div>
            <div style="font-size: 13px; opacity: 0.9;">I dati, i grafici e le tabelle di LUCAINVESTRATTO saranno visualizzati con questo stile di trasparenza e sfumatura degradante.</div>
            <div style="margin-top: 12px;">
                <button style="background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%); color: #FFF; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 600; font-size: 12px;">Pulsante Degradante Attivo</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        use_custom = st.checkbox("Abilita colori primari e accento personalizzati", value=settings.use_custom_colors)
        c_cp1, c_cp2 = st.columns(2)
        with c_cp1:
            custom_p = st.color_picker("Colore Primario Base", value=settings.custom_primary_color)
        with c_cp2:
            custom_a = st.color_picker("Colore Accento Base", value=settings.custom_accent_color)

        if st.button("💾 Salva e Applica Configurazione Completa", type="primary"):
            settings.theme_preset = chosen_preset
            settings.use_custom_colors = use_custom
            settings.custom_primary_color = custom_p
            settings.custom_accent_color = custom_a
            
            # Gradients
            settings.gradient_buttons_enabled = grad_btn_en
            settings.gradient_btn_start = btn_start
            settings.gradient_btn_end = btn_end
            settings.gradient_cards_enabled = grad_card_en
            settings.gradient_card_start = card_start
            settings.gradient_card_end = card_end

            # Background
            settings.background_type = bg_type_selected
            settings.background_preset_key = bg_preset_selected
            settings.background_image_url = bg_url_selected
            settings.background_image_base64 = bg_base64_selected
            settings.background_overlay_opacity = overlay_op / 100.0

            # Transparency
            settings.card_opacity_pct = float(card_op)
            settings.card_blur_px = int(blur_px)
            settings.sidebar_opacity_pct = float(side_op)

            save_settings(settings)
            st.success("Tutte le impostazioni di colore, sfumature, sfondo e trasparenza sono state salvate con successo!")
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
