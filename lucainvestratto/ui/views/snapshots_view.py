"""
Snapshot and monthly reconciliation view for LUCAINVESTRATTO.
Provides:
1. Upload and archive of monthly bank statement images / photos (.png, .jpg) with asset breakdown.
2. Automated reconciliation (Quadratura) comparing reported snapshot totals with internal accounts & holdings.
3. Historical trajectory analysis across monthly snapshots (wealth progression & asset allocation drift).
4. Photographic archive gallery with inspection and export.
"""
import os
import io
import json
import base64
from datetime import date, datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

from lucainvestratto.db import db
from lucainvestratto.models import PortfolioSnapshot, Holding, BankAccount, Transaction
from lucainvestratto.analytics.snapshots import (
    reconcile_snapshot_with_actual,
    calculate_snapshot_trends,
    parse_raw_text_to_allocations
)


def render_snapshots_view():
    st.subheader("📸 Snapshot Mensili & Quadratura Estratto Conto")
    st.markdown("""
    Archiviazione della **fotografia mensile** del patrimonio (screenshot o foto dell'estratto conto/home banking),
    verifica automatizzata della **quadratura contabile** (riconciliazione con movimenti e dossier titoli)
    e analisi dell'**evoluzione dei totali e dell'asset allocation** nel tempo.
    """)

    accounts = db.get_accounts()
    all_snapshots = db.get_snapshots()

    tab_upload, tab_reconcile, tab_trends, tab_gallery = st.tabs([
        "📤 Carica Snapshot Mensile",
        "⚖️ Quadratura con Estratto Conto",
        "📈 Analisi Serie Storica Totali",
        f"🖼️ Archivio Fotografico ({len(all_snapshots)})"
    ])

    # ==========================================
    # TAB 1: UPLOAD SNAPSHOT
    # ==========================================
    with tab_upload:
        st.markdown("#### 📸 Registra Nuova Fotografia Patrimoniale")
        st.caption("Carica il riepilogo mensile da home banking (.png, .jpg) con i controvalori totali e le percentuali per asset.")

        col_img, col_form = st.columns([1, 1])

        uploaded_img = col_img.file_uploader(
            "Seleziona immagine riepilogo (.png, .jpg, .jpeg):",
            type=["png", "jpg", "jpeg"],
            help="Screenshot da app bancaria o scansione/foto dell'estratto conto mensile."
        )

        b64_image = ""
        img_filename = ""
        if uploaded_img is not None:
            img_bytes = uploaded_img.read()
            img_filename = uploaded_img.name
            mime_type = "image/png" if img_filename.lower().endswith(".png") else "image/jpeg"
            b64_image = f"data:{mime_type};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
            try:
                pil_img = Image.open(io.BytesIO(img_bytes))
                col_img.image(pil_img, caption=f"Anteprima: {img_filename}", use_container_width=True)
            except Exception as e:
                col_img.warning(f"Impossibile renderizzare l'anteprima: {e}")

        with col_form:
            snap_date = st.date_input("Data della Fotografia / Estratto Conto", value=date.today())
            acc_choices = {"all": "🌐 Tutti i Conti (Patrimonio Globale Consolidato)"}
            for a in accounts:
                acc_choices[a.id] = f"{a.name} ({a.bank_name or a.currency})"
            selected_acc = st.selectbox(
                "Perimetro di riferimento:",
                options=list(acc_choices.keys()),
                format_func=lambda k: acc_choices[k]
            )

            col_w1, col_w2, col_w3 = st.columns(3)
            with col_w1:
                total_w = st.number_input("Patrimonio Totale (€)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
            with col_w2:
                liquid_c = st.number_input("Di cui Liquidità (€)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
            with col_w3:
                invest_a = st.number_input("Di cui Investito (€)", min_value=0.0, value=0.0, step=100.0, format="%.2f")

            # Auto-infer invested if 0
            if invest_a == 0.0 and total_w > liquid_c:
                invest_a = round(total_w - liquid_c, 2)

            notes = st.text_input("Note di chiusura mese", placeholder="es. Fine mese Marzo 2026 - Quadratura Fineco + Degiro")

        st.markdown("---")
        st.markdown("#### 🧩 Ripartizione per Asset e Percentuali a quella Data")
        st.caption("Inserisci i totali per classe di attivo e le percentuali indicate nell'immagine.")

        # Parsing assistant helper expander
        with st.expander("✨ Assistente di Compilazione Rapida / Incolla Testo", expanded=False):
            st.markdown("Se hai copiato il testo dall'estratto conto o da un report OCR, incollalo qui:")
            pasted_text = st.text_area(
                "Testo riassuntivo asset:",
                placeholder="Azionario Globale: 95.000 € (41%)\nObbligazioni: 45.000 € (20%)\nLiquidità: 55.000 € (24%)\nAzioni Tech: 35.000 € (15%)",
                height=100
            )
            if st.button("🪄 Riconosci Asset da Testo Incollato"):
                parsed_allocs = parse_raw_text_to_allocations(pasted_text)
                if parsed_allocs:
                    st.session_state["temp_alloc_editor"] = parsed_allocs
                    st.success(f"Riconosciute {len(parsed_allocs)} classi di attivo!")
                else:
                    st.warning("Nessuna classe di attivo riconosciuta. Verifica il formato del testo.")

        # Initialize session state for interactive table
        if "temp_alloc_editor" not in st.session_state:
            st.session_state["temp_alloc_editor"] = [
                {"asset_class": "Azionario Globale (ETF)", "amount": 0.0, "weight_pct": 0.0},
                {"asset_class": "Obbligazionario Governativo", "amount": 0.0, "weight_pct": 0.0},
                {"asset_class": "Liquidità & Depositi", "amount": 0.0, "weight_pct": 0.0},
                {"asset_class": "Azioni Singole", "amount": 0.0, "weight_pct": 0.0}
            ]

        df_editor_input = pd.DataFrame(st.session_state["temp_alloc_editor"])
        edited_df = st.data_editor(
            df_editor_input,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "asset_class": st.column_config.TextColumn("Classe di Attivo / Macro Asset", required=True),
                "amount": st.column_config.NumberColumn("Importo (€)", format="€ %.2f", min_value=0.0),
                "weight_pct": st.column_config.NumberColumn("Peso Percentuale (%)", format="%.2f %%", min_value=0.0, max_value=100.0)
            }
        )

        sum_alloc_amt = edited_df["amount"].sum()
        sum_alloc_pct = edited_df["weight_pct"].sum()

        col_chk1, col_chk2 = st.columns(2)
        with col_chk1:
            if abs(sum_alloc_pct - 100.0) < 0.1:
                st.success(f"Somma Pesi: **{sum_alloc_pct:.2f}%** (100% Completo)")
            else:
                st.warning(f"Somma Pesi: **{sum_alloc_pct:.2f}%** (Diverso da 100%)")
        with col_chk2:
            st.info(f"Somma Controvalori Asset: **€ {sum_alloc_amt:,.2f}**")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Salva Fotografia Snapshot nel Database", type="primary", use_container_width=True):
            if total_w <= 0.0 and sum_alloc_amt > 0:
                total_w = sum_alloc_amt
            if total_w <= 0.0:
                st.error("Inserire un importo per il patrimonio totale o compilare la ripartizione asset.")
            else:
                # Prepare allocation json
                alloc_records = edited_df.to_dict(orient="records")
                new_snap = PortfolioSnapshot(
                    account_id=selected_acc,
                    snapshot_date=snap_date.isoformat(),
                    total_wealth=float(total_w),
                    liquid_cash=float(liquid_c),
                    invested_amount=float(invest_a),
                    allocations_json=json.dumps(alloc_records, ensure_ascii=False),
                    image_filename=img_filename,
                    image_base64=b64_image,
                    notes=notes
                )
                db.save_snapshot(new_snap)
                st.success(f"Snapshot registrato con successo per la data {snap_date.isoformat()}!")
                st.rerun()

    # ==========================================
    # TAB 2: RECONCILIATION / QUADRATURA
    # ==========================================
    with tab_reconcile:
        st.markdown("#### ⚖️ Riconciliazione & Quadratura con Estratto Conto")
        st.caption("Verifica automatica: confronta il totale riportato dalla fotografia bancaria con il calcolo contabile interno.")

        if not all_snapshots:
            st.info("Nessuno snapshot disponibile per la quadratura. Carica una fotografia patrimoniale nel Tab precedente o carica i dati demo.")
        else:
            snap_options = {s.id: f"Data: {s.snapshot_date} | Totale Foto: € {s.total_wealth:,.2f} | {s.notes[:30] if s.notes else ''}" for s in sorted(all_snapshots, key=lambda x: x.snapshot_date, reverse=True)}
            selected_snap_id = st.selectbox(
                "Seleziona Snapshot da Riconciliare:",
                options=list(snap_options.keys()),
                format_func=lambda k: snap_options[k]
            )

            chosen_snap = db.get_snapshot_by_id(selected_snap_id)
            if chosen_snap:
                holdings = db.get_holdings()
                transactions = db.get_transactions()
                recon = reconcile_snapshot_with_actual(chosen_snap, holdings, accounts, transactions)

                # Status Banner
                st.markdown(f"""
                <div style="background-color: {recon['status_color']}20; border-left: 6px solid {recon['status_color']}; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: {recon['status_color']};">{recon['status_label']}</h3>
                    <p style="margin: 6px 0 0 0; color: #334155; font-size: 1.05em;">{recon['status_desc']}</p>
                </div>
                """, unsafe_allow_html=True)

                # Metrics Row
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                with kpi1:
                    st.metric("Patrimonio da Snapshot (Foto)", f"€ {recon['reported_total']:,.2f}")
                with kpi2:
                    st.metric("Patrimonio Contabile (Sistema)", f"€ {recon['internal_total']:,.2f}")
                with kpi3:
                    delta_color = "normal" if recon['delta_total'] == 0 else ("inverse" if recon['delta_total'] < 0 else "off")
                    st.metric(
                        "Delta Quadratura (€)",
                        f"€ {recon['delta_total']:,.2f}",
                        delta=f"{recon['delta_pct']:+.2f}%",
                        delta_color=delta_color
                    )
                with kpi4:
                    st.metric("Data Rilevazione", recon['snapshot_date'])

                st.markdown("---")
                st.markdown("##### 🔍 Dettaglio per Componenti di Riconciliazione")

                comp_data = [
                    {
                        "Componente": "Liquidità Disponibile & Depositi",
                        "Valore Snapshot (€)": float(recon['reported_cash']),
                        "Valore Contabile Sistema (€)": float(recon['internal_cash']),
                        "Scostamento (€)": float(recon['delta_cash']),
                        "Stato": "✅" if abs(recon['delta_cash']) < 5.0 else "⚠️"
                    },
                    {
                        "Componente": "Portafoglio Titoli Investito",
                        "Valore Snapshot (€)": float(recon['reported_invested']),
                        "Valore Contabile Sistema (€)": float(recon['internal_invested']),
                        "Scostamento (€)": float(recon['delta_invested']),
                        "Stato": "✅" if abs(recon['delta_invested']) < 10.0 else "⚠️"
                    },
                    {
                        "Componente": "TOTALE PATRIMONIO",
                        "Valore Snapshot (€)": float(recon['reported_total']),
                        "Valore Contabile Sistema (€)": float(recon['internal_total']),
                        "Scostamento (€)": float(recon['delta_total']),
                        "Stato": "✅" if abs(recon['delta_total']) < 1.0 else ("⚠️" if abs(recon['delta_total']) < 50.0 else "❌")
                    }
                ]
                st.dataframe(
                    pd.DataFrame(comp_data),
                    column_config={
                        "Valore Snapshot (€)": st.column_config.NumberColumn(format="€ %.2f"),
                        "Valore Contabile Sistema (€)": st.column_config.NumberColumn(format="€ %.2f"),
                        "Scostamento (€)": st.column_config.NumberColumn(format="€ %.2f"),
                    },
                    use_container_width=True
                )


                # Asset Level Breakdown if present
                df_alloc_comp = recon.get("df_alloc_comparison")
                if df_alloc_comp is not None and not df_alloc_comp.empty:
                    st.markdown("##### 📊 Quadratura Dettagliata per Classe di Attivo")
                    st.dataframe(df_alloc_comp, use_container_width=True)

                # Explanatory reconciliation guide
                with st.expander("ℹ️ Guida alla risoluzione dei delta di quadratura", expanded=False):
                    st.markdown("""
                    **Perché potrebbe verificarsi uno scostamento tra fotografia e sistema?**
                    - **Ratei di cedole e dividendi**: la banca potrebbe mostrare il controvalore inclusivo del rateo maturato (*corso tel-quel*), mentre il sistema valorizza il *corso secco*.
                    - **Orari di chiusura di mercato**: i prezzi di chiusura dell'estratto conto potrebbero differire dai prezzi istantanei o dall'ultimo scambio registrato.
                    - **Oneri bancari e imposte di bollo**: canoni mensili o bollo titoli dello 0.20% addebitati all'ultimo giorno lavorativo del mese.
                    - **Ordini in fase di regolamento (T+2)**: vendite o acquisti eseguiti a fine mese con data valuta nei primi giorni del mese successivo.
                    """)

    # ==========================================
    # TAB 3: HISTORICAL TRENDS & ASSET DRIFT
    # ==========================================
    with tab_trends:
        st.markdown("#### 📈 Analisi Serie Storica & Deriva dei Totali")
        st.caption("Evoluzione multi-periodale del patrimonio consolidato e delle allocazioni percentuali mese per mese.")

        trends = calculate_snapshot_trends(all_snapshots)
        if not trends["has_data"] or trends["count"] == 0:
            st.info("Nessun dato storico disponibile. Registra almeno 2 snapshot per visualizzare i grafici di trend.")
        else:
            # Summary Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Patrimonio Attuale (Ultimo)", f"€ {trends['latest_wealth']:,.2f}")
            with m2:
                st.metric("Patrimonio Iniziale", f"€ {trends['earliest_wealth']:,.2f}")
            with m3:
                st.metric(
                    "Guadagno Complessivo",
                    f"€ {trends['total_gain']:,.2f}",
                    delta=f"{trends['total_gain_pct']:+.2f}%"
                )
            with m4:
                st.metric("CAGR Annualizzato", f"{trends['cagr']:.2f}%")

            st.markdown("---")

            # Chart 1: Wealth Evolution Curve
            df_snaps = trends["df_snapshots"]
            fig_wealth = go.Figure()

            fig_wealth.add_trace(go.Scatter(
                x=df_snaps["Data Snapshot"],
                y=df_snaps["Patrimonio Totale (€)"],
                mode='lines+markers',
                name='Patrimonio Totale',
                line=dict(color='#2563EB', width=3),
                marker=dict(size=8, color='#1E40AF')
            ))

            fig_wealth.add_trace(go.Scatter(
                x=df_snaps["Data Snapshot"],
                y=df_snaps["Investito (€)"],
                mode='lines+markers',
                name='Portafoglio Investito',
                line=dict(color='#10B981', width=2, dash='dot'),
                marker=dict(size=6)
            ))

            fig_wealth.add_trace(go.Scatter(
                x=df_snaps["Data Snapshot"],
                y=df_snaps["Liquidità (€)"],
                mode='lines+markers',
                name='Liquidità & Riserva',
                line=dict(color='#F59E0B', width=2, dash='dot'),
                marker=dict(size=6)
            ))

            fig_wealth.update_layout(
                title="Evoluzione Patrimonio Totale, Investito e Liquidità (€)",
                xaxis_title="Data Fotografia",
                yaxis_title="Controvalore (€)",
                template="plotly_white",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_wealth, use_container_width=True)

            # Chart 2: Asset Allocation Evolution (Stacked Area / Drift)
            df_alloc_hist = trends.get("df_allocations_history")
            if df_alloc_hist is not None and not df_alloc_hist.empty:
                st.markdown("##### 🧬 Evoluzione e Deriva dell'Asset Allocation (%)")
                fig_alloc = px.area(
                    df_alloc_hist,
                    x="Data",
                    y="Percentuale (%)",
                    color="Classe Attivo",
                    title="Deriva dei Pesi Percentuali delle Classi di Attivo nel Tempo",
                    template="plotly_white"
                )
                fig_alloc.update_yaxes(range=[0, 100])
                st.plotly_chart(fig_alloc, use_container_width=True)

            # Table of Historical Snapshots
            st.dataframe(
                df_snaps,
                column_config={
                    "Patrimonio Totale (€)": st.column_config.NumberColumn(format="€ %.2f"),
                    "Liquidità (€)": st.column_config.NumberColumn(format="€ %.2f"),
                    "Investito (€)": st.column_config.NumberColumn(format="€ %.2f"),
                    "Variazione Mensile (€)": st.column_config.NumberColumn(format="€ %.2f"),
                    "Variazione Mensile (%)": st.column_config.NumberColumn(format="%.2f %%"),
                },
                use_container_width=True
            )

    # ==========================================
    # TAB 4: PHOTOGRAPHIC ARCHIVE GALLERY
    # ==========================================
    with tab_gallery:
        st.markdown("#### 🖼️ Galleria & Archivio Immagini Estratti")
        st.caption("Visualizza le immagini originali caricate per ciascuna fotografia mensile.")

        if not all_snapshots:
            st.info("Nessuna immagine archiviata al momento.")
        else:
            sorted_by_date = sorted(all_snapshots, key=lambda x: x.snapshot_date, reverse=True)
            for snap in sorted_by_date:
                with st.expander(f"📷 Snapshot del **{snap.snapshot_date}** — Totale: **€ {snap.total_wealth:,.2f}** | Note: {snap.notes or 'N/D'}", expanded=False):
                    g_col1, g_col2 = st.columns([1, 2])
                    with g_col1:
                        if snap.image_base64:
                            st.image(snap.image_base64, caption=f"File: {snap.image_filename or 'screenshot.png'}", use_container_width=True)
                        else:
                            st.info("Nessun file immagine allegato a questo snapshot.")
                    with g_col2:
                        st.markdown(f"**Data Snapshot:** `{snap.snapshot_date}`")
                        st.markdown(f"**Patrimonio Totale:** `€ {snap.total_wealth:,.2f}`")
                        st.markdown(f"**Liquidità:** `€ {snap.liquid_cash:,.2f}`")
                        st.markdown(f"**Portafoglio Investito:** `€ {snap.invested_amount:,.2f}`")
                        st.markdown(f"**Note:** {snap.notes or 'Nessuna nota registrata'}")

                        # Show allocations
                        allocs = snap.get_allocations()
                        if allocs:
                            st.markdown("**Composizione Asset:**")
                            st.dataframe(pd.DataFrame(allocs), use_container_width=True)

                        # Delete button
                        if st.button(f"🗑️ Elimina Snapshot ({snap.snapshot_date})", key=f"del_snap_{snap.id}"):
                            db.delete_snapshot(snap.id)
                            st.success("Snapshot eliminato con successo!")
                            st.rerun()
