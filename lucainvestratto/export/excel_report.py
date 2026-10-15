"""
Institutional Excel report generator for LUCAINVESTRATTO.
Creates a professional multi-sheet formatted workbook (.xlsx) using OpenPyXL.
"""
import io
from typing import List, Dict, Any
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from lucainvestratto.models import BankAccount, Holding, Transaction
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics


def generate_excel_report(
    accounts: List[BankAccount],
    holdings: List[Holding],
    transactions: List[Transaction],
    account_filter_name: str = "Tutti i conti (Consolidato)",
    benchmark_code: str = "MSCI_WORLD"
) -> bytes:
    wb = openpyxl.Workbook()

    # Styling definitions
    font_title = Font(name="Calibri", size=16, bold=True, color="0F172A")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="64748B")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=11, bold=True, color="1E293B")
    font_normal = Font(name="Calibri", size=10, color="1E293B")
    
    fill_header = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    fill_sub_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    fill_alt = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_card = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Compute analytics
    cash_sum = calculate_cashflow_summary(transactions, accounts)
    asset_sum = calculate_asset_summary(holdings)
    risk_sum = calculate_risk_metrics(holdings, benchmark_code=benchmark_code)

    tot_liquidita = cash_sum["final_balance"]
    tot_investito = asset_sum["total_market_value"]
    patrimonio_totale = tot_liquidita + tot_investito

    # ================= SHEET 1: SINTESI & METRICHE =================
    ws1 = wb.active
    ws1.title = "Sintesi & Metriche Rischio"
    ws1.views.sheetView[0].showGridLines = True

    ws1["A1"] = "LUCAINVESTRATTO - REPORT ESECUTIVO & ANALISI PROFESSIONALE"
    ws1["A1"].font = font_title
    ws1["A2"] = f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Perimetro: {account_filter_name} | Benchmark: {benchmark_code}"
    ws1["A2"].font = font_subtitle

    # KPI Table
    ws1["A4"] = "INDICATORE PATRIMONIALE"
    ws1["B4"] = "VALORE (€)"
    ws1["D4"] = "METRICA DI RISCHIO FACTSET"
    ws1["E4"] = "VALORE"
    for col in ["A4", "B4", "D4", "E4"]:
        ws1[col].font = font_header
        ws1[col].fill = fill_header
        ws1[col].alignment = Alignment(horizontal="center")

    kpi_left = [
        ("Patrimonio Netto Totale", patrimonio_totale, "€ #,##0.00"),
        ("Liquidità Totale Conti", tot_liquidita, "€ #,##0.00"),
        ("Controvalore Portafoglio", tot_investito, "€ #,##0.00"),
        ("Costo Storico (PMC)", asset_sum["total_invested"], "€ #,##0.00"),
        ("Plus/Minusvalenza Latente", asset_sum["total_unrealized_pl"], "€ #,##0.00"),
        ("Plus/Minusvalenza %", asset_sum["total_unrealized_pl_pct"] / 100.0, "+0.00%;-0.00%"),
        ("Flusso Netto Cassa Periodo", cash_sum["net_cashflow"], "€ #,##0.00"),
        ("Tasso di Risparmio", cash_sum["savings_rate_pct"] / 100.0, "0.0%")
    ]

    kpi_right = [
        ("Indice di Sharpe (Ann.)", risk_sum["sharpe_ratio"], "0.00"),
        ("Indice di Sortino", risk_sum["sortino_ratio"], "0.00"),
        ("Rendimento Annualizzato (CAGR)", risk_sum["cagr"] / 100.0, "+0.00%;-0.00%"),
        ("Volatilità Annualizzata", risk_sum["volatility_annualized"] / 100.0, "0.00%"),
        ("Massimo Drawdown (MDD)", risk_sum["max_drawdown"] / 100.0, "0.00%"),
        ("Value at Risk (VaR 95% Ann.)", risk_sum["var_95_annual"] / 100.0, "0.00%"),
        ("Beta vs Benchmark", risk_sum["beta"], "0.00"),
        ("Alfa di Jensen", risk_sum["alpha_jensen"] / 100.0, "+0.00%;-0.00%")
    ]

    for idx, (label, val, fmt) in enumerate(kpi_left, start=5):
        ws1[f"A{idx}"] = label
        ws1[f"A{idx}"].font = font_bold if idx == 5 else font_normal
        ws1[f"A{idx}"].border = thin_border
        ws1[f"B{idx}"] = val
        ws1[f"B{idx}"].font = font_bold if idx == 5 else font_normal
        ws1[f"B{idx}"].number_format = fmt
        ws1[f"B{idx}"].border = thin_border

    for idx, (label, val, fmt) in enumerate(kpi_right, start=5):
        ws1[f"D{idx}"] = label
        ws1[f"D{idx}"].font = font_normal
        ws1[f"D{idx}"].border = thin_border
        ws1[f"E{idx}"] = val
        ws1[f"E{idx}"].font = font_bold if idx in [5, 6, 7] else font_normal
        ws1[f"E{idx}"].number_format = fmt
        ws1[f"E{idx}"].border = thin_border

    # ================= SHEET 2: ASSET ALLOCATION =================
    ws2 = wb.create_sheet(title="Asset Allocation")
    ws2.views.sheetView[0].showGridLines = True
    ws2["A1"] = "RIPARTIZIONE PORTAFOGLIO PER ASSET CLASS"
    ws2["A1"].font = font_title

    headers_alloc = ["Asset Class", "Controvalore (€)", "Costo Storico (€)", "Peso (%)", "P&L (€)", "Rendimento (%)"]
    for col_idx, h in enumerate(headers_alloc, 1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    df_class = asset_sum["df_by_class"]
    if not df_class.empty:
        for row_idx, r in enumerate(df_class.itertuples(), start=4):
            ws2.cell(row=row_idx, column=1, value=str(r.asset_class)).font = font_bold
            
            c2 = ws2.cell(row=row_idx, column=2, value=float(r.market_value))
            c2.number_format = "€ #,##0.00"
            c2.font = font_normal

            c3 = ws2.cell(row=row_idx, column=3, value=float(r.total_cost))
            c3.number_format = "€ #,##0.00"
            c3.font = font_normal

            c4 = ws2.cell(row=row_idx, column=4, value=float(r.weight_pct) / 100.0)
            c4.number_format = "0.0%"
            c4.font = font_normal

            c5 = ws2.cell(row=row_idx, column=5, value=float(r.unrealized_pl))
            c5.number_format = "€ #,##0.00"
            c5.font = font_normal

            c6 = ws2.cell(row=row_idx, column=6, value=float(r.pl_pct) / 100.0)
            c6.number_format = "+0.00%;-0.00%"
            c6.font = font_normal

            for c in range(1, 7):
                ws2.cell(row=row_idx, column=c).border = thin_border
                if row_idx % 2 == 0:
                    ws2.cell(row=row_idx, column=c).fill = fill_alt

    # ================= SHEET 3: POSIZIONI DETTAGLIATE =================
    ws3 = wb.create_sheet(title="Posizioni Portafoglio")
    ws3.views.sheetView[0].showGridLines = True
    ws3["A1"] = "DETTAGLIO TITOLI ED ASSET IN PORTAFOGLIO"
    ws3["A1"].font = font_title

    headers_pos = [
        "Simbolo / ISIN", "Nome Strumento", "Asset Class", "Settore", "Geo",
        "Quantità", "PMC (€)", "Prezzo Attuale (€)", "Costo Totale (€)",
        "Controvalore (€)", "P&L (€)", "Rendimento (%)", "Peso (%)", "Yield Dividendo (%)"
    ]
    for col_idx, h in enumerate(headers_pos, 1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    df_holdings = asset_sum["df_holdings"]
    if not df_holdings.empty:
        for row_idx, h in enumerate(df_holdings.itertuples(), start=4):
            ws3.cell(row=row_idx, column=1, value=str(h.symbol)).font = font_bold
            ws3.cell(row=row_idx, column=2, value=str(h.name)).font = font_normal
            ws3.cell(row=row_idx, column=3, value=str(h.asset_class)).font = font_normal
            ws3.cell(row=row_idx, column=4, value=str(h.sector)).font = font_normal
            ws3.cell(row=row_idx, column=5, value=str(h.geography)).font = font_normal

            ws3.cell(row=row_idx, column=6, value=float(h.quantity)).number_format = "#,##0.00"
            ws3.cell(row=row_idx, column=7, value=float(h.average_buy_price)).number_format = "€ #,##0.00"
            ws3.cell(row=row_idx, column=8, value=float(h.current_price)).number_format = "€ #,##0.00"
            ws3.cell(row=row_idx, column=9, value=float(h.total_cost)).number_format = "€ #,##0.00"
            ws3.cell(row=row_idx, column=10, value=float(h.market_value)).number_format = "€ #,##0.00"
            ws3.cell(row=row_idx, column=11, value=float(h.unrealized_pl)).number_format = "€ #,##0.00"
            ws3.cell(row=row_idx, column=12, value=float(h.unrealized_pl_pct) / 100.0).number_format = "+0.00%;-0.00%"
            ws3.cell(row=row_idx, column=13, value=float(h.weight_pct) / 100.0).number_format = "0.0%"
            ws3.cell(row=row_idx, column=14, value=float(h.annual_dividend_yield) / 100.0).number_format = "0.00%"

            for c in range(1, 15):
                ws3.cell(row=row_idx, column=c).border = thin_border
                if row_idx % 2 == 0:
                    ws3.cell(row=row_idx, column=c).fill = fill_alt

    # ================= SHEET 4: ESTRATTO CONTO =================
    ws4 = wb.create_sheet(title="Estratto Conto Transazioni")
    ws4.views.sheetView[0].showGridLines = True
    ws4["A1"] = "ESTRATTO CONTO E MOVIMENTI BANCARI"
    ws4["A1"].font = font_title

    headers_tx = ["Data", "Conto ID", "Tipo Operazione", "Categoria", "Importo (€)", "Valuta", "Descrizione / Causale", "Titolo"]
    for col_idx, h in enumerate(headers_tx, 1):
        cell = ws4.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    for row_idx, tx in enumerate(transactions, start=4):
        ws4.cell(row=row_idx, column=1, value=tx.date).font = font_normal
        ws4.cell(row=row_idx, column=2, value=tx.account_id).font = font_normal
        ws4.cell(row=row_idx, column=3, value=tx.type).font = font_normal
        ws4.cell(row=row_idx, column=4, value=tx.category).font = font_normal

        amt_cell = ws4.cell(row=row_idx, column=5, value=float(tx.amount))
        amt_cell.number_format = "€ #,##0.00"
        amt_cell.font = font_bold

        ws4.cell(row=row_idx, column=6, value=tx.currency).font = font_normal
        ws4.cell(row=row_idx, column=7, value=tx.description).font = font_normal
        ws4.cell(row=row_idx, column=8, value=tx.asset_symbol or "").font = font_normal

        for c in range(1, 9):
            ws4.cell(row=row_idx, column=c).border = thin_border
            if row_idx % 2 == 0:
                ws4.cell(row=row_idx, column=c).fill = fill_alt

    # Auto-fit columns across all sheets
    for ws in [ws1, ws2, ws3, ws4]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
