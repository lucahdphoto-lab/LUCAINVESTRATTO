"""
Institutional PDF report generator for LUCAINVESTRATTO.
Generates an executive-grade wealth management and statement report using ReportLab.
"""
import io
from typing import List, Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

from lucainvestratto.models import BankAccount, Holding, Transaction
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics


def generate_pdf_report(
    accounts: List[BankAccount],
    holdings: List[Holding],
    transactions: List[Transaction],
    account_filter_name: str = "Tutti i conti (Consolidato)",
    benchmark_code: str = "MSCI_WORLD"
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    brand_blue = colors.HexColor("#0F172A")    # Deep Navy
    accent_blue = colors.HexColor("#2563EB")   # Royal Blue
    light_bg = colors.HexColor("#F8FAFC")      # Slate light
    alt_row = colors.HexColor("#F1F5F9")
    text_dark = colors.HexColor("#1E293B")
    green_p = colors.HexColor("#16A34A")
    red_loss = colors.HexColor("#DC2626")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=brand_blue
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B")
    )
    section_style = ParagraphStyle(
        "DocSection",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=brand_blue,
        spaceBefore=12,
        spaceAfter=6
    )
    cell_style = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=text_dark
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=text_dark
    )
    cell_header = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("LUCAINVESTRATTO", title_style))
    story.append(Paragraph("REPORT INTEGRATO DI GESTIONE PATRIMONIALE & ESTRATTO CONTO MULTI-CONTO", subtitle_style))
    story.append(Paragraph(
        f"Data generazione: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Perimetro: <b>{account_filter_name}</b> | Benchmark: <b>{benchmark_code}</b>",
        subtitle_style
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=accent_blue, spaceAfter=14))

    # Calculate analytics
    cash_sum = calculate_cashflow_summary(transactions, accounts)
    asset_sum = calculate_asset_summary(holdings)
    risk_sum = calculate_risk_metrics(holdings, benchmark_code=benchmark_code)

    tot_liquidita = cash_sum["final_balance"]
    tot_investito = asset_sum["total_market_value"]
    patrimonio_totale = tot_liquidita + tot_investito

    # 2. Key Performance Indicators Table
    story.append(Paragraph("1. Sintesi Esecutiva & Indicatori Chiave (KPI)", section_style))

    pl_color = green_p if asset_sum["total_unrealized_pl"] >= 0 else red_loss
    kpi_data = [
        [
            Paragraph("<b>Patrimonio Totale Netto</b>", cell_bold),
            Paragraph(f"<b>€ {patrimonio_totale:,.2f}</b>", cell_bold),
            Paragraph("<b>Indice di Sharpe (Ann.)</b>", cell_bold),
            Paragraph(f"<b>{risk_sum['sharpe_ratio']:.2f}</b>", cell_bold)
        ],
        [
            Paragraph("Liquidità Totale Conti", cell_style),
            Paragraph(f"€ {tot_liquidita:,.2f}", cell_style),
            Paragraph("Indice di Sortino", cell_style),
            Paragraph(f"{risk_sum['sortino_ratio']:.2f}", cell_style)
        ],
        [
            Paragraph("Controvalore Investito", cell_style),
            Paragraph(f"€ {tot_investito:,.2f}", cell_style),
            Paragraph("Volatilità Annualizzata", cell_style),
            Paragraph(f"{risk_sum['volatility_annualized']:.2f}%", cell_style)
        ],
        [
            Paragraph("Costo Storico (PMC)", cell_style),
            Paragraph(f"€ {asset_sum['total_invested']:,.2f}", cell_style),
            Paragraph("Massimo Drawdown (MDD)", cell_style),
            Paragraph(f"{risk_sum['max_drawdown']:.2f}%", cell_style)
        ],
        [
            Paragraph("Plus/Minusvalenza Latente", cell_style),
            Paragraph(f"€ {asset_sum['total_unrealized_pl']:,.2f} ({asset_sum['total_unrealized_pl_pct']:+.2f}%)", cell_style),
            Paragraph("Value at Risk (VaR 95% Ann.)", cell_style),
            Paragraph(f"{risk_sum['var_95_annual']:.2f}% (€ {risk_sum['var_95_amount_eur']:,.2f})", cell_style)
        ],
        [
            Paragraph("Rendimento Annualizzato (CAGR)", cell_style),
            Paragraph(f"<b>{risk_sum['cagr']:+.2f}%</b>", cell_bold),
            Paragraph("Beta vs Benchmark", cell_style),
            Paragraph(f"{risk_sum['beta']:.2f}", cell_style)
        ],
        [
            Paragraph("Flusso Netto Cassa Periodo", cell_style),
            Paragraph(f"€ {cash_sum['net_cashflow']:+,.2f}", cell_style),
            Paragraph("Alfa di Jensen", cell_style),
            Paragraph(f"{risk_sum['alpha_jensen']:+.2f}%", cell_style)
        ]
    ]

    t_kpi = Table(kpi_data, colWidths=[4.2 * cm, 4.8 * cm, 4.2 * cm, 4.8 * cm])
    t_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # 3. Asset Allocation Table
    story.append(Paragraph("2. Ripartizione per Asset Class", section_style))
    df_class = asset_sum["df_by_class"]

    alloc_rows = [[
        Paragraph("Asset Class", cell_header),
        Paragraph("Controvalore (€)", cell_header),
        Paragraph("Peso (%)", cell_header),
        Paragraph("P&L Non Realizzato", cell_header),
        Paragraph("Rendimento (%)", cell_header)
    ]]

    if not df_class.empty:
        for _, r in df_class.iterrows():
            alloc_rows.append([
                Paragraph(str(r["asset_class"]), cell_style),
                Paragraph(f"€ {float(r['market_value']):,.2f}", cell_style),
                Paragraph(f"{float(r['weight_pct']):.1f}%", cell_style),
                Paragraph(f"€ {float(r['unrealized_pl']):+,.2f}", cell_style),
                Paragraph(f"{float(r['pl_pct']):+.2f}%", cell_style)
            ])
    else:
        alloc_rows.append([Paragraph("Nessuna posizione registrata", cell_style)] * 5)

    t_alloc = Table(alloc_rows, colWidths=[6.0 * cm, 3.2 * cm, 2.4 * cm, 3.4 * cm, 3.0 * cm])
    t_alloc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, alt_row]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(t_alloc)
    story.append(Spacer(1, 10))

    # 4. Top Holdings Table
    story.append(Paragraph("3. Dettaglio Principali Strumenti Finanziari in Portafoglio", section_style))
    df_holdings = asset_sum["df_holdings"]

    holdings_rows = [[
        Paragraph("Simbolo", cell_header),
        Paragraph("Denominazione Strumento", cell_header),
        Paragraph("Q.tà", cell_header),
        Paragraph("PMC", cell_header),
        Paragraph("Prezzo", cell_header),
        Paragraph("Controvalore", cell_header),
        Paragraph("P&L (€)", cell_header),
        Paragraph("Peso %", cell_header)
    ]]

    if not df_holdings.empty:
        top_h = df_holdings.head(10)
        for _, h in top_h.iterrows():
            holdings_rows.append([
                Paragraph(str(h["symbol"]), cell_bold),
                Paragraph(str(h["name"])[:28], cell_style),
                Paragraph(f"{float(h['quantity']):,.2f}", cell_style),
                Paragraph(f"€ {float(h['average_buy_price']):,.2f}", cell_style),
                Paragraph(f"€ {float(h['current_price']):,.2f}", cell_style),
                Paragraph(f"€ {float(h['market_value']):,.2f}", cell_style),
                Paragraph(f"€ {float(h['unrealized_pl']):+,.2f}", cell_style),
                Paragraph(f"{float(h['weight_pct']):.1f}%", cell_style)
            ])
    else:
        holdings_rows.append([Paragraph("Nessun titolo presente", cell_style)] * 8)

    t_holdings = Table(holdings_rows, colWidths=[2.2 * cm, 4.4 * cm, 1.8 * cm, 2.0 * cm, 2.0 * cm, 2.6 * cm, 2.0 * cm, 1.0 * cm])
    t_holdings.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, alt_row]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(t_holdings)
    story.append(Spacer(1, 10))

    # 5. Cashflow Statement Summary
    story.append(Paragraph("4. Sintesi Estratto Conto e Flussi di Liquidità", section_style))
    cf_data = [
        [
            Paragraph("<b>Saldo Iniziale Periodo</b>", cell_style),
            Paragraph(f"€ {cash_sum['initial_balance']:,.2f}", cell_style),
            Paragraph("<b>Saldo Finale Effettivo</b>", cell_bold),
            Paragraph(f"<b>€ {cash_sum['final_balance']:,.2f}</b>", cell_bold)
        ],
        [
            Paragraph("Totale Entrate / Accrediti", cell_style),
            Paragraph(f"€ {cash_sum['total_inflows']:,.2f}", cell_style),
            Paragraph("Flusso Netto di Cassa", cell_style),
            Paragraph(f"€ {cash_sum['net_cashflow']:+,.2f}", cell_style)
        ],
        [
            Paragraph("Totale Uscite / Addebiti", cell_style),
            Paragraph(f"€ {cash_sum['total_outflows']:,.2f}", cell_style),
            Paragraph("Tasso di Risparmio", cell_style),
            Paragraph(f"{cash_sum['savings_rate_pct']:.1f}%", cell_style)
        ]
    ]
    t_cf = Table(cf_data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
    t_cf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(t_cf)
    story.append(Spacer(1, 14))

    # Disclaimer footer
    disclaimer_style = ParagraphStyle(
        "DocDisclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=6.5,
        leading=9,
        textColor=colors.HexColor("#94A3B8")
    )
    story.append(Paragraph(
        "Avvertenze: Documento generato ad uso informativo da LUCAINVESTRATTO. I dati storici, i rendimenti passati e le metriche di rischio "
        "(Sharpe, Sortino, VaR, Max Drawdown) non costituiscono promessa o garanzia di rendimenti futuri. "
        "Non costituisce sollecitazione al pubblico risparmio o consulenza finanziaria personalizzata.",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
