"""
Institutional PDF report generator for LUCAINVESTRATTO.
Generates an executive-grade wealth management and statement report using ReportLab.
Ensures ALL numeric data is formatted and strictly RIGHT-ALIGNED in tables.
"""
import io
from typing import List, Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
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
    
    # Custom colors
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

    # Paragraph Styles with explicit alignment
    cell_style = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=text_dark
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=text_dark
    )
    cell_style_right = ParagraphStyle(
        "CellNormalRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=text_dark
    )
    cell_bold_right = ParagraphStyle(
        "CellBoldRight",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=text_dark
    )
    cell_center = ParagraphStyle(
        "CellCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=text_dark
    )
    cell_header = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.white
    )
    cell_header_right = ParagraphStyle(
        "CellHeaderRight",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=colors.white
    )
    cell_header_center = ParagraphStyle(
        "CellHeaderCenter",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
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

    kpi_data = [
        [
            Paragraph("<b>Patrimonio Totale Netto</b>", cell_bold),
            Paragraph(f"<b>€ {patrimonio_totale:,.2f}</b>", cell_bold_right),
            Paragraph("<b>Indice di Sharpe (Ann.)</b>", cell_bold),
            Paragraph(f"<b>{risk_sum['sharpe_ratio']:.2f}</b>", cell_bold_right)
        ],
        [
            Paragraph("Liquidità Totale Conti", cell_style),
            Paragraph(f"€ {tot_liquidita:,.2f}", cell_style_right),
            Paragraph("Indice di Sortino", cell_style),
            Paragraph(f"{risk_sum['sortino_ratio']:.2f}", cell_style_right)
        ],
        [
            Paragraph("Controvalore Investito", cell_style),
            Paragraph(f"€ {tot_investito:,.2f}", cell_style_right),
            Paragraph("Volatilità Annualizzata", cell_style),
            Paragraph(f"{risk_sum['volatility_annualized']:.2f}%", cell_style_right)
        ],
        [
            Paragraph("Costo Storico (PMC)", cell_style),
            Paragraph(f"€ {asset_sum['total_invested']:,.2f}", cell_style_right),
            Paragraph("Massimo Drawdown (MDD)", cell_style),
            Paragraph(f"{risk_sum['max_drawdown']:.2f}%", cell_style_right)
        ],
        [
            Paragraph("Plus/Minusvalenza Latente", cell_style),
            Paragraph(f"€ {asset_sum['total_unrealized_pl']:,.2f} ({asset_sum['total_unrealized_pl_pct']:+.2f}%)", cell_style_right),
            Paragraph("Value at Risk (VaR 95% Ann.)", cell_style),
            Paragraph(f"{risk_sum['var_95_annual']:.2f}% (€ {risk_sum['var_95_amount_eur']:,.2f})", cell_style_right)
        ],
        [
            Paragraph("Rendimento Annualizzato (CAGR)", cell_style),
            Paragraph(f"<b>{risk_sum['cagr']:+.2f}%</b>", cell_bold_right),
            Paragraph("Beta vs Benchmark", cell_style),
            Paragraph(f"{risk_sum['beta']:.2f}", cell_style_right)
        ],
        [
            Paragraph("Flusso Netto Cassa Periodo", cell_style),
            Paragraph(f"€ {cash_sum['net_cashflow']:+,.2f}", cell_style_right),
            Paragraph("Alfa di Jensen", cell_style),
            Paragraph(f"{risk_sum['alpha_jensen']:+.2f}%", cell_style_right)
        ]
    ]

    t_kpi = Table(kpi_data, colWidths=[4.2 * cm, 4.8 * cm, 4.2 * cm, 4.8 * cm])
    t_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # 3. Asset Allocation Table
    story.append(Paragraph("2. Ripartizione per Asset Class", section_style))
    df_class = asset_sum["df_by_class"]

    alloc_rows = [[
        Paragraph("Asset Class", cell_header),
        Paragraph("Controvalore (€)", cell_header_right),
        Paragraph("Peso (%)", cell_header_right),
        Paragraph("P&L Non Realizzato", cell_header_right),
        Paragraph("Rendimento (%)", cell_header_right)
    ]]

    if not df_class.empty:
        for _, r in df_class.iterrows():
            alloc_rows.append([
                Paragraph(str(r["asset_class"]), cell_style),
                Paragraph(f"€ {float(r['market_value']):,.2f}", cell_style_right),
                Paragraph(f"{float(r['weight_pct']):.1f}%", cell_style_right),
                Paragraph(f"€ {float(r['unrealized_pl']):+,.2f}", cell_style_right),
                Paragraph(f"{float(r['pl_pct']):+.2f}%", cell_style_right)
            ])
    else:
        alloc_rows.append([Paragraph("Nessuna posizione registrata", cell_style)] * 5)

    t_alloc = Table(alloc_rows, colWidths=[6.0 * cm, 3.2 * cm, 2.4 * cm, 3.4 * cm, 3.0 * cm])
    t_alloc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, alt_row]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(t_alloc)
    story.append(Spacer(1, 10))

    # 4. Top Holdings Table
    story.append(Paragraph("3. Dettaglio Principali Strumenti Finanziari in Portafoglio", section_style))
    df_holdings = asset_sum["df_holdings"]

    holdings_rows = [[
        Paragraph("Simbolo", cell_header_center),
        Paragraph("Denominazione Strumento", cell_header),
        Paragraph("Q.tà", cell_header_right),
        Paragraph("PMC", cell_header_right),
        Paragraph("Prezzo", cell_header_right),
        Paragraph("Controvalore", cell_header_right),
        Paragraph("P&L (€)", cell_header_right),
        Paragraph("Peso %", cell_header_right)
    ]]

    if not df_holdings.empty:
        top_h = df_holdings.head(10)
        for _, h in top_h.iterrows():
            holdings_rows.append([
                Paragraph(str(h["symbol"]), cell_center),
                Paragraph(str(h["name"])[:28], cell_style),
                Paragraph(f"{float(h['quantity']):,.2f}", cell_style_right),
                Paragraph(f"€ {float(h['average_buy_price']):,.2f}", cell_style_right),
                Paragraph(f"€ {float(h['current_price']):,.2f}", cell_style_right),
                Paragraph(f"€ {float(h['market_value']):,.2f}", cell_style_right),
                Paragraph(f"€ {float(h['unrealized_pl']):+,.2f}", cell_style_right),
                Paragraph(f"{float(h['weight_pct']):.1f}%", cell_style_right)
            ])
    else:
        holdings_rows.append([Paragraph("Nessun titolo presente", cell_style)] * 8)

    t_holdings = Table(holdings_rows, colWidths=[2.2 * cm, 4.4 * cm, 1.8 * cm, 2.0 * cm, 2.0 * cm, 2.6 * cm, 2.0 * cm, 1.0 * cm])
    t_holdings.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, alt_row]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(t_holdings)
    story.append(Spacer(1, 10))

    # 5. Cashflow Statement Summary
    story.append(Paragraph("4. Sintesi Estratto Conto e Flussi di Liquidità", section_style))
    cf_data = [
        [
            Paragraph("<b>Saldo Iniziale Periodo</b>", cell_style),
            Paragraph(f"€ {cash_sum['initial_balance']:,.2f}", cell_style_right),
            Paragraph("<b>Saldo Finale Effettivo</b>", cell_bold),
            Paragraph(f"<b>€ {cash_sum['final_balance']:,.2f}</b>", cell_bold_right)
        ],
        [
            Paragraph("Totale Entrate / Accrediti", cell_style),
            Paragraph(f"€ {cash_sum['total_inflows']:,.2f}", cell_style_right),
            Paragraph("Flusso Netto di Cassa", cell_style),
            Paragraph(f"€ {cash_sum['net_cashflow']:+,.2f}", cell_style_right)
        ],
        [
            Paragraph("Totale Uscite / Addebiti", cell_style),
            Paragraph(f"€ {cash_sum['total_outflows']:,.2f}", cell_style_right),
            Paragraph("Tasso di Risparmio", cell_style),
            Paragraph(f"{cash_sum['savings_rate_pct']:.1f}%", cell_style_right)
        ]
    ]
    t_cf = Table(cf_data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
    t_cf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
    ]))
    story.append(t_cf)
    story.append(Spacer(1, 14))

    # Disclaimer footer
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#94A3B8")
    )
    story.append(Paragraph(
        "LUCAINVESTRATTO è un software analitico ad uso personale. I dati e i rendimenti passati non costituiscono garanzia "
        "di risultati futuri né consulenza finanziaria personalizzata ai sensi del TUF / MiFID II.",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
