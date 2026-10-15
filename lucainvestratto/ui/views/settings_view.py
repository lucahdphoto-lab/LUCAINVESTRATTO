"""
Settings and configuration view for LUCAINVESTRATTO.
Includes:
1. Color theme selection, custom color pickers, degrading gradients (buttons and windows),
   external background image customization, and glassmorphism transparency controls,
   featuring an interactive STICKY LATERAL POP-UP PREVIEW that updates in real time.
2. Custom threshold alerts and active notification center.
3. Selective reset functions (transactions, holdings, date-filtered, accounts).
4. Data recalculation, integrity diagnostics, and running balance alignment.
"""
import base64
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
    Personalizza l'interfaccia grafica con **sfumature degradanti**, **immagini di sfondo**,
    e **trasparenze con effetto vetro**, osservando i cambiamenti in tempo reale nel **pop-up laterale di anteprima**.
    """)

    settings = load_settings()
    accounts = db.get_accounts()
    holdings = db.get_holdings()
    transactions = db.get_transactions()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎨 Colori, Sfumature & Sfondo (con Pop-Up Anteprima)",
        "🔔 Notifiche & Alert Personalizzati",
        "🧹 Azzeramento Selettivo Dati",
        "🔄 Ricalcolo & Allineamento Dati"
    ])

    # ================= TAB 1: MODIFICA COLORI CON POP-UP LATERALE =================
    with tab1:
        col_ctrl, col_popup = st.columns([1.5, 1.3], gap="large")

        # ---------------- CONTROLS COLUMN (LEFT) ----------------
        with col_ctrl:
            st.markdown("#### 🎨 Palette & Temi Finanziari Predefiniti")
            preset_options = list(THEME_PRESETS.keys())
            preset_labels = {k: v["name"] for k, v in THEME_PRESETS.items()}

            current_idx = preset_options.index(settings.theme_preset) if settings.theme_preset in preset_options else 0
            chosen_preset = st.selectbox(
                "Seleziona Tema Predefinito:",
                options=preset_options,
                format_func=lambda k: preset_labels[k],
                index=current_idx,
                key="theme_preset_select"
            )

            preset_colors = THEME_PRESETS[chosen_preset]

            st.markdown("---")
            # 1. SFUMATURE DEGRADANTI
            st.markdown("#### 🌈 1. Sfumature Degradanti per Finestre e Pulsanti")
            
            c_grad1, c_grad2 = st.columns(2)
            with c_grad1:
                st.markdown("##### 🔘 Sfumatura Pulsanti")
                grad_btn_en = st.toggle("Abilita Gradiente sui Pulsanti", value=settings.gradient_buttons_enabled, key="toggle_grad_btn")
                btn_start = st.color_picker(
                    "Colore Iniziale Pulsante",
                    value=settings.gradient_btn_start if settings.gradient_buttons_enabled else preset_colors["primary_color"],
                    key="cp_btn_start"
                )
                btn_end = st.color_picker(
                    "Colore Finale Pulsante",
                    value=settings.gradient_btn_end if settings.gradient_buttons_enabled else preset_colors.get("btn_gradient_end", "#1E40AF"),
                    key="cp_btn_end"
                )

            with c_grad2:
                st.markdown("##### 🪟 Sfumatura Finestre / Card")
                grad_card_en = st.toggle("Abilita Gradiente sulle Card", value=settings.gradient_cards_enabled, key="toggle_grad_card")
                card_start = st.color_picker(
                    "Colore Iniziale Card",
                    value=settings.gradient_card_start if settings.gradient_cards_enabled else preset_colors.get("card_gradient_start", "#FFFFFF"),
                    key="cp_card_start"
                )
                card_end = st.color_picker(
                    "Colore Finale Card",
                    value=settings.gradient_card_end if settings.gradient_cards_enabled else preset_colors.get("card_gradient_end", "#F8FAFC"),
                    key="cp_card_end"
                )

            st.markdown("---")
            # 2. SFONDO CON IMMAGINI ESTERNE
            st.markdown("#### 🖼️ 2. Modifica Sfondo con Immagini Esterne")
            bg_mode_options = [
                "Colore Piatto / Gradiente Standard",
                "Wallpaper Finanziari ad Alta Definizione (Preset)",
                "URL Immagine Esterna Web",
                "Carica File Immagine dal Tuo Computer (.jpg, .png)"
            ]
            
            init_bg_idx = 0
            if settings.background_type == "image_preset":
                init_bg_idx = 1
            elif settings.background_type == "image_url":
                init_bg_idx = 2
            elif settings.background_type == "image_upload":
                init_bg_idx = 3

            selected_bg_mode = st.radio("Modalità Sfondo Applicazione:", options=bg_mode_options, index=init_bg_idx, key="radio_bg_mode")

            bg_type_selected = "default"
            bg_preset_selected = settings.background_preset_key
            bg_url_selected = settings.background_image_url
            bg_base64_selected = settings.background_image_base64
            effective_bg_for_preview = ""

            if selected_bg_mode == "Wallpaper Finanziari ad Alta Definizione (Preset)":
                bg_type_selected = "image_preset"
                preset_img_keys = list(PRESET_BACKGROUND_IMAGES.keys())
                curr_p_idx = preset_img_keys.index(settings.background_preset_key) if settings.background_preset_key in preset_img_keys else 1
                bg_preset_selected = st.selectbox("Scegli Wallpaper Istituzionale:", preset_img_keys, index=curr_p_idx, key="sb_bg_preset")
                effective_bg_for_preview = PRESET_BACKGROUND_IMAGES.get(bg_preset_selected, "")

            elif selected_bg_mode == "URL Immagine Esterna Web":
                bg_type_selected = "image_url"
                bg_url_selected = st.text_input(
                    "Inserisci URL pubblico dell'immagine (.jpg, .png):",
                    value=settings.background_image_url,
                    placeholder="https://images.unsplash.com/photo-...",
                    key="txt_bg_url"
                )
                effective_bg_for_preview = bg_url_selected.strip()

            elif selected_bg_mode == "Carica File Immagine dal Tuo Computer (.jpg, .png)":
                bg_type_selected = "image_upload"
                uploaded_bg = st.file_uploader("Seleziona file immagine:", type=["png", "jpg", "jpeg", "webp"], key="upload_bg_file")
                if uploaded_bg is not None:
                    img_bytes = uploaded_bg.read()
                    mime = uploaded_bg.type or "image/jpeg"
                    bg_base64_selected = f"data:{mime};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
                    effective_bg_for_preview = bg_base64_selected
                elif settings.background_image_base64:
                    effective_bg_for_preview = settings.background_image_base64
                    st.caption("Immagine caricata in precedenza già memorizzata.")
            else:
                bg_type_selected = "default"
                effective_bg_for_preview = ""

            overlay_op = st.slider(
                "Opacità Velo di Copertura Sfondo (% oscuramento per leggibilità):",
                min_value=10, max_value=98, value=int(settings.background_overlay_opacity * 100), step=2, key="sl_overlay_op"
            )

            st.markdown("---")
            # 3. REGOLAZIONE TRASPARENZE E EFFETTO GLASSMORPHISM
            st.markdown("#### 🪟 3. Regolazione Trasparenze & Vetro Satinato (Glassmorphism)")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                card_op = st.slider("Opacità Finestre e Card (%)", min_value=20, max_value=100, value=int(settings.card_opacity_pct), step=5, key="sl_card_op")
                side_op = st.slider("Opacità Barra Laterale Sidebar (%)", min_value=40, max_value=100, value=int(settings.sidebar_opacity_pct), step=5, key="sl_side_op")
            with col_t2:
                blur_px = st.slider("Intensità Sfocatura Vetro (Blur in px)", min_value=0, max_value=30, value=int(settings.card_blur_px), step=2, key="sl_blur_px")

            st.markdown("---")
            use_custom = st.checkbox("Abilita colori primari e accento personalizzati", value=settings.use_custom_colors, key="chk_use_custom")
            c_cp1, c_cp2 = st.columns(2)
            with c_cp1:
                custom_p = st.color_picker("Colore Primario Base", value=settings.custom_primary_color, key="cp_custom_p")
            with c_cp2:
                custom_a = st.color_picker("Colore Accento Base", value=settings.custom_accent_color, key="cp_custom_a")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Salva e Applica Configurazione Completa", type="primary", use_container_width=True, key="btn_save_all_settings"):
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
                st.toast("✅ Configurazione salvata con successo!")
                st.rerun()

        # ---------------- LIVE STICKY POP-UP PREVIEW COLUMN (RIGHT) ----------------
        with col_popup:
            # Sticky CSS container
            st.markdown("""
            <style>
                .preview-sticky-box {
                    position: -webkit-sticky;
                    position: sticky;
                    top: 24px;
                    z-index: 1000;
                    margin-bottom: 24px;
                }
            </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="preview-sticky-box">', unsafe_allow_html=True)
            
            # Pop-up Card Header with Live Indicator
            c_head1, c_head2 = st.columns([3, 2])
            with c_head1:
                st.markdown("### 📱 Pop-Up Anteprima Live")
            with c_head2:
                st.markdown("""
                <div style="text-align: right; padding-top: 6px;">
                    <span style="background: #16A34A; color: #FFF; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 12px; display: inline-flex; align-items: center; gap: 4px;">
                        <span style="width: 6px; height: 6px; border-radius: 50%; background: #FFF; display: inline-block;"></span>
                        LIVE UPDATE
                    </span>
                </div>
                """, unsafe_allow_html=True)

            st.caption("Questo riquadro riflette istantaneamente le tue modifiche a colori, trasparenze, sfumature e sfondo.")

            # Compute preview styles
            card_start_rgba = hex_to_rgba(card_start, opacity=card_op / 100.0)
            card_end_rgba = hex_to_rgba(card_end, opacity=card_op / 100.0)
            overlay_val = overlay_op / 100.0

            # Background CSS for the live simulator box
            if effective_bg_for_preview:
                preview_bg_css = f"background: linear-gradient(rgba(15, 23, 42, {overlay_val:.2f}), rgba(15, 23, 42, {overlay_val:.2f})), url('{effective_bg_for_preview}'); background-size: cover; background-position: center;"
            else:
                preview_bg_css = f"background: linear-gradient(135deg, {preset_colors['header_bg_start']} 0%, {preset_colors['header_bg_end']} 100%);"

            # Render Simulator Sandbox Box
            st.markdown(f"""
            <div style="{preview_bg_css} border: 2px solid rgba(255, 255, 255, 0.2); border-radius: 16px; padding: 18px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35); margin-bottom: 12px;">
                <!-- Mini Brand Header -->
                <div style="background: linear-gradient(135deg, {preset_colors['header_bg_start']} 0%, {preset_colors['header_bg_end']} 100%); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 12px 16px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="color: #F8FAFC; font-weight: 700; font-size: 15px; display: flex; align-items: center; gap: 6px;">
                        <span>🏛️ LUCAINVESTRATTO</span>
                        <span style="background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%); color: #FFF; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 700;">PRO</span>
                    </div>
                    <span style="background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); color: #FFF; font-size: 9px; font-weight: 700; padding: 2px 7px; border-radius: 10px;">⚠️ ALERT</span>
                </div>

                <!-- Glassmorphism KPI Metric Card with Gradients & Transparency -->
                <div style="background: linear-gradient(135deg, {card_start_rgba} 0%, {card_end_rgba} 100%); backdrop-filter: blur({blur_px}px); -webkit-backdrop-filter: blur({blur_px}px); border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 12px; padding: 14px; margin-bottom: 14px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);">
                    <div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Patrimonio Netto Totale (Simulato)</div>
                    <div style="font-size: 22px; font-weight: 800; color: #0F172A; font-family: monospace; margin: 4px 0;">€ 201.415,89</div>
                    <div style="font-size: 11px; font-weight: 600; color: #16A34A;">▲ +25,99% (+€ 41.520,00) • Sharpe: 1.45</div>
                </div>

                <!-- Action Button with Degrading Gradient -->
                <div style="display: flex; gap: 10px; margin-bottom: 14px;">
                    <button style="background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%); color: #FFFFFF; border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; padding: 8px 16px; font-weight: 600; font-size: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.25); width: 100%; cursor: pointer;">
                        🚀 Pulsante Azione con Sfumatura
                    </button>
                    <button style="background: rgba(255,255,255,0.12); backdrop-filter: blur({blur_px}px); color: #FFF; border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; padding: 8px 14px; font-weight: 600; font-size: 12px; cursor: pointer;">
                        Filtro
                    </button>
                </div>

                <!-- Glassmorphism Mini Chart Card -->
                <div style="background: linear-gradient(135deg, {card_start_rgba} 0%, {card_end_rgba} 100%); backdrop-filter: blur({blur_px}px); -webkit-backdrop-filter: blur({blur_px}px); border: 1px solid rgba(255, 255, 255, 0.22); border-radius: 12px; padding: 12px;">
                    <div style="font-size: 10.5px; font-weight: 700; color: #64748B; margin-bottom: 4px;">📈 ANDAMENTO PORTAFOGLIO VS BENCHMARK</div>
                    <div style="height: 140px;" id="mini_chart_container">
            """, unsafe_allow_html=True)

            # Mini live chart themed with the selected colors
            fig_mini = go.Figure()
            fig_mini.add_trace(go.Scatter(
                x=["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott"],
                y=[100, 102.5, 101.8, 106.2, 105.0, 111.4, 114.2, 112.8, 119.5, 125.9],
                mode="lines",
                name="Portafoglio",
                line=dict(color=btn_start, width=2.5),
                fill="tozeroy",
                fillcolor=hex_to_rgba(btn_start, opacity=0.18)
            ))
            fig_mini.add_trace(go.Scatter(
                x=["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott"],
                y=[100, 101.2, 102.0, 104.5, 103.8, 107.1, 108.5, 107.9, 111.2, 114.0],
                mode="lines",
                name="Benchmark",
                line=dict(color="#94A3B8", width=1.5, dash="dot")
            ))
            fig_mini.update_layout(
                margin=dict(l=5, r=5, t=5, b=5),
                height=135,
                hovermode=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, showticklabels=True, color="#94A3B8", tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)", showticklabels=False),
                showlegend=False
            )
            st.plotly_chart(fig_mini, use_container_width=True, config={"displayModeBar": False})

            st.markdown("""
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Popover for modal view
            with st.popover("🔎 Apri Pop-Up Ingrandito a Finestra Modale"):
                st.markdown("#### 🖼️ Vista Pop-Up a Schermo Intero")
                st.caption("Rappresentazione ingrandita della dashboard con le impostazioni correnti:")
                st.markdown(f"""
                <div style="{preview_bg_css} border-radius: 14px; padding: 24px; color: #FFF;">
                    <div style="background: linear-gradient(135deg, {card_start_rgba} 0%, {card_end_rgba} 100%); backdrop-filter: blur({blur_px}px); border-radius: 12px; padding: 20px; color: #0F172A;">
                        <h3 style="margin-top:0;">Dettaglio Rendimento con Trasparenza al {card_op}%</h3>
                        <p>Questo effetto di trasparenza garantisce che lo sfondo risalti mantenendo la massima leggibilità.</p>
                        <button style="background: linear-gradient(135deg, {btn_start} 0%, {btn_end} 100%); color: #FFF; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold;">Pulsante Degradante</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

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
