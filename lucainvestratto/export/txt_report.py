"""
Text / ASCII report generator (.txt) for LUCAINVESTRATTO.
Creates a FactSet/Bloomberg terminal formatted monospaced brief.
"""
from typing import List
from datetime import datetime

from lucainvestratto.models import BankAccount, Holding, Transaction
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics


def generate_txt_report(
    accounts: List[BankAccount],
    holdings: List[Holding],
    transactions: List[Transaction],
    account_filter_name: str = "Tutti i conti (Consolidato)",
    benchmark_code: str = "MSCI_WORLD"
) -> str:
    cash_sum = calculate_cashflow_summary(transactions, accounts)
    asset_sum = calculate_asset_summary(holdings)
    risk_sum = calculate_risk_metrics(holdings, benchmark_code=benchmark_code)

    tot_liquidita = cash_sum["final_balance"]
    tot_investito = asset_sum["total_market_value"]
    patrimonio_totale = tot_liquidita + tot_investito

    lines = []
    sep = "=" * 80
    subsep = "-" * 80

    lines.append(sep)
    lines.append(" LUCAINVESTRATTO :: REPORT PATRIMONIALE & ANALISI INVESTIMENTI")
    lines.append(f" Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Perimetro: {account_filter_name}")
    lines.append(f" Benchmark di riferimento: {benchmark_code} ({risk_sum['benchmark_name']})")
    lines.append(sep)
    lines.append("")

    # 1. EXECUTIVE SUMMARY & KPIS
    lines.append("[1] SINTESI ESECUTIVA & METRICHE ISTITUZIONALI FACTSET")
    lines.append(subsep)
    lines.append(f"  Patrimonio Totale Netto:       € {patrimonio_totale:>15,.2f} | Indice di Sharpe (Ann.):     {risk_sum['sharpe_ratio']:>10.2f}")
    lines.append(f"  Liquidità Totale Conti:        € {tot_liquidita:>15,.2f} | Indice di Sortino:          {risk_sum['sortino_ratio']:>10.2f}")
    lines.append(f"  Controvalore Portafoglio:      € {tot_investito:>15,.2f} | Indice di Calmar:           {risk_sum['calmar_ratio']:>10.2f}")
    lines.append(f"  Capitale Investito (PMC):      € {asset_sum['total_invested']:>15,.2f} | Volatilità Annualizzata:    {risk_sum['volatility_annualized']:>9.2f}%")
    lines.append(f"  Plus/Minusvalenza Latente (€): € {asset_sum['total_unrealized_pl']:>15,.2f} | Massimo Drawdown (MDD):     {risk_sum['max_drawdown']:>9.2f}%")
    lines.append(f"  Plus/Minusvalenza Latente (%):   {asset_sum['total_unrealized_pl_pct']:>15.2f}% | Value at Risk (VaR 95% Ann.):{risk_sum['var_95_annual']:>9.2f}%")
    lines.append(f"  Rendimento Annualizzato (CAGR):  {risk_sum['cagr']:>15.2f}% | Beta vs Benchmark:          {risk_sum['beta']:>10.2f}")
    lines.append(f"  Flusso Cassa Netto Periodo:    € {cash_sum['net_cashflow']:>15,.2f} | Alfa di Jensen:             {risk_sum['alpha_jensen']:>9.2f}%")
    lines.append(f"  Tasso di Risparmio Medio:        {cash_sum['savings_rate_pct']:>15.1f}% | R-Squared (R²):             {risk_sum['r_squared']:>10.2f}")
    lines.append(subsep)
    lines.append("")

    # 2. ASSET ALLOCATION
    lines.append("[2] RIPARTIZIONE ASSET ALLOCATION")
    lines.append(subsep)
    lines.append(f"  {'Asset Class':<35} | {'Controvalore (€)':>18} | {'Peso (%)':>10} | {'P&L (€)':>12}")
    lines.append(subsep)
    df_class = asset_sum["df_by_class"]
    if not df_class.empty:
        for _, r in df_class.iterrows():
            lines.append(f"  {str(r['asset_class']):<35} | € {float(r['market_value']):>16,.2f} | {float(r['weight_pct']):>9.1f}% | € {float(r['unrealized_pl']):>10,.2f}")
    else:
        lines.append("  Nessuna posizione registrata.")
    lines.append(subsep)
    lines.append("")

    # 3. DETTAGLIO POSIZIONI
    lines.append("[3] DETTAGLIO STRUMENTI IN PORTAFOGLIO (TOP POSIZIONI)")
    lines.append(subsep)
    lines.append(f"  {'Simbolo':<12} {'Denominazione':<24} {'Q.tà':>8} {'PMC (€)':>10} {'Prezzo':>10} {'Controvalore':>14} {'P&L %':>8}")
    lines.append(subsep)
    df_holdings = asset_sum["df_holdings"]
    if not df_holdings.empty:
        for _, h in df_holdings.head(15).iterrows():
            lines.append(
                f"  {str(h['symbol']):<12} "
                f"{str(h['name'])[:23]:<24} "
                f"{float(h['quantity']):>8.1f} "
                f"{float(h['average_buy_price']):>10.2f} "
                f"{float(h['current_price']):>10.2f} "
                f"€ {float(h['market_value']):>12,.2f} "
                f"{float(h['unrealized_pl_pct']):>+7.1f}%"
            )
    else:
        lines.append("  Nessun titolo presente.")
    lines.append(subsep)
    lines.append("")

    # 4. ESTRATTO CONTO SINTESI
    lines.append("[4] SINTESI ESTRATTO CONTO E MOVIMENTI BANCARI")
    lines.append(subsep)
    lines.append(f"  Saldo Iniziale Complessivo:      € {cash_sum['initial_balance']:>15,.2f}")
    lines.append(f"  Totale Accrediti / Entrate:      € {cash_sum['total_inflows']:>15,.2f}")
    lines.append(f"  Totale Addebiti / Uscite:        € {cash_sum['total_outflows']:>15,.2f}")
    lines.append(f"  Flusso Netto di Cassa:           € {cash_sum['net_cashflow']:>15,.2f}")
    lines.append(f"  Saldo Finale Effettivo:          € {cash_sum['final_balance']:>15,.2f}")
    lines.append(f"  Numero Movimenti Rilevati:         {cash_sum['transactions_count']:>15}")
    lines.append(sep)
    lines.append(" Fine report LUCAINVESTRATTO. Documento riservato ad uso personale.")
    lines.append(sep)

    return "\n".join(lines)
