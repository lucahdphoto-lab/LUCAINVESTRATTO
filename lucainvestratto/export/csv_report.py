"""
CSV report generator for LUCAINVESTRATTO.
Produces clean, institutional-grade CSV exports where all numeric columns
are strictly typed as numbers (float/int), never as text strings or formatted currency.
Compatible with Microsoft Excel, Google Sheets, Pandas, PowerBI, and terminal tools.
"""
import io
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from lucainvestratto.models import BankAccount, Holding, Transaction
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics


def _clean_num(val: Any, default: float = 0.0) -> float:
    """Ensures value is a clean float without NaN or text format."""
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def generate_transactions_csv(
    transactions: List[Transaction],
    accounts: List[BankAccount],
    delimiter: str = ",",
    decimal: str = "."
) -> bytes:
    """
    Generates a CSV export of bank and portfolio transactions.
    All monetary and quantity columns (Importo, Commissioni, Quantita, Prezzo_Unitario)
    are strictly numeric (float), with no text symbols or currency characters.
    """
    acc_map = {a.id: a.name for a in accounts}

    rows = []
    for tx in transactions:
        qty = _clean_num(tx.quantity, default=np.nan) if tx.quantity is not None else np.nan
        price = _clean_num(tx.unit_price, default=np.nan) if tx.unit_price is not None else np.nan
        fees = _clean_num(tx.fees, default=0.0)
        amt = _clean_num(tx.amount, default=0.0)

        rows.append({
            "Data": str(tx.date or ""),
            "Conto_ID": str(tx.account_id or ""),
            "Conto_Nome": acc_map.get(tx.account_id, str(tx.account_id or "")),
            "Tipo_Operazione": str(tx.type or ""),
            "Categoria": str(tx.category or "Altro"),
            "Importo": amt,
            "Commissioni": fees,
            "Valuta": str(tx.currency or "EUR"),
            "Descrizione": str(tx.description or ""),
            "Titolo_Ticker": str(tx.asset_symbol or ""),
            "Quantita": qty,
            "Prezzo_Unitario": price,
            "Note": str(tx.notes or "")
        })

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=[
            "Data", "Conto_ID", "Conto_Nome", "Tipo_Operazione", "Categoria",
            "Importo", "Commissioni", "Valuta", "Descrizione", "Titolo_Ticker",
            "Quantita", "Prezzo_Unitario", "Note"
        ])

    csv_str = df.to_csv(index=False, sep=delimiter, decimal=decimal)
    return csv_str.encode("utf-8-sig")


def generate_holdings_csv(
    holdings: List[Holding],
    delimiter: str = ",",
    decimal: str = "."
) -> bytes:
    """
    Generates a CSV export of detailed portfolio positions.
    All numeric fields (Quantita, PMC, Prezzo_Attuale, Costo_Totale, Controvalore,
    P&L, Rendimento %, Peso %, Yield %, Reddito Annuo) are pure floats.
    """
    asset_sum = calculate_asset_summary(holdings)
    df_holdings = asset_sum.get("df_holdings", pd.DataFrame())

    if df_holdings.empty:
        cols = [
            "Simbolo_ISIN", "Nome_Titolo", "Classe_Attivo", "Settore", "Geografia",
            "Valuta", "Quantita", "PMC_Prezzo_Medio_Carico", "Prezzo_Attuale",
            "Costo_Totale", "Controvalore_Attuale", "Plus_Minusvalenza_Latente",
            "Rendimento_Percentuale", "Peso_Portafoglio_Percentuale",
            "Yield_Dividendo_Percentuale", "Reddito_Annuo_Stimato", "Duration"
        ]
        return pd.DataFrame(columns=cols).to_csv(index=False, sep=delimiter, decimal=decimal).encode("utf-8-sig")

    rows = []
    for h in df_holdings.itertuples():
        qty = _clean_num(getattr(h, "quantity", 0.0))
        pmc = _clean_num(getattr(h, "average_buy_price", 0.0))
        px = _clean_num(getattr(h, "current_price", 0.0))
        cost = _clean_num(getattr(h, "total_cost", 0.0))
        mv = _clean_num(getattr(h, "market_value", 0.0))
        pl = _clean_num(getattr(h, "unrealized_pl", 0.0))
        pl_pct = _clean_num(getattr(h, "unrealized_pl_pct", 0.0))
        weight_pct = _clean_num(getattr(h, "weight_pct", 0.0))
        div_yield = _clean_num(getattr(h, "annual_dividend_yield", 0.0))
        income = _clean_num(getattr(h, "expected_annual_income", 0.0))
        duration = _clean_num(getattr(h, "duration", 0.0))

        rows.append({
            "Simbolo_ISIN": str(getattr(h, "symbol", "")),
            "Nome_Titolo": str(getattr(h, "name", "")),
            "Classe_Attivo": str(getattr(h, "asset_class", "")),
            "Settore": str(getattr(h, "sector", "")),
            "Geografia": str(getattr(h, "geography", "")),
            "Valuta": str(getattr(h, "currency", "EUR")),
            "Quantita": qty,
            "PMC_Prezzo_Medio_Carico": pmc,
            "Prezzo_Attuale": px,
            "Costo_Totale": cost,
            "Controvalore_Attuale": mv,
            "Plus_Minusvalenza_Latente": pl,
            "Rendimento_Percentuale": pl_pct,
            "Peso_Portafoglio_Percentuale": weight_pct,
            "Yield_Dividendo_Percentuale": div_yield,
            "Reddito_Annuo_Stimato": income,
            "Duration": duration
        })

    df = pd.DataFrame(rows)
    csv_str = df.to_csv(index=False, sep=delimiter, decimal=decimal)
    return csv_str.encode("utf-8-sig")


def generate_asset_allocation_csv(
    holdings: List[Holding],
    delimiter: str = ",",
    decimal: str = "."
) -> bytes:
    """
    Generates a CSV export of asset allocation breakdown by asset class.
    All numeric fields (Controvalore, Costo_Totale, Peso_Pct, P&L, Rendimento_Pct)
    are strictly numeric (float).
    """
    asset_sum = calculate_asset_summary(holdings)
    df_class = asset_sum.get("df_by_class", pd.DataFrame())

    if df_class.empty:
        cols = ["Classe_Attivo", "Controvalore", "Costo_Totale", "Peso_Percentuale", "Plus_Minusvalenza", "Rendimento_Percentuale"]
        return pd.DataFrame(columns=cols).to_csv(index=False, sep=delimiter, decimal=decimal).encode("utf-8-sig")

    rows = []
    for r in df_class.itertuples():
        rows.append({
            "Classe_Attivo": str(getattr(r, "asset_class", "")),
            "Controvalore": _clean_num(getattr(r, "market_value", 0.0)),
            "Costo_Totale": _clean_num(getattr(r, "total_cost", 0.0)),
            "Peso_Percentuale": _clean_num(getattr(r, "weight_pct", 0.0)),
            "Plus_Minusvalenza": _clean_num(getattr(r, "unrealized_pl", 0.0)),
            "Rendimento_Percentuale": _clean_num(getattr(r, "pl_pct", 0.0))
        })

    df = pd.DataFrame(rows)
    csv_str = df.to_csv(index=False, sep=delimiter, decimal=decimal)
    return csv_str.encode("utf-8-sig")


def generate_risk_kpi_csv(
    holdings: List[Holding],
    accounts: List[BankAccount],
    transactions: List[Transaction],
    benchmark_code: str = "MSCI_WORLD",
    delimiter: str = ",",
    decimal: str = "."
) -> bytes:
    """
    Generates a CSV export of portfolio executive KPIs and FactSet risk metrics.
    Every metric value is strictly numeric (float).
    """
    cash_sum = calculate_cashflow_summary(transactions, accounts)
    asset_sum = calculate_asset_summary(holdings)
    risk_sum = calculate_risk_metrics(holdings, benchmark_code=benchmark_code)

    tot_liquidita = _clean_num(cash_sum.get("final_balance", 0.0))
    tot_investito = _clean_num(asset_sum.get("total_market_value", 0.0))
    patrimonio_totale = tot_liquidita + tot_investito

    items = [
        # Patrimoniali
        ("Patrimonio", "Patrimonio Netto Totale", patrimonio_totale, "EUR"),
        ("Patrimonio", "Liquidità Totale Conti", tot_liquidita, "EUR"),
        ("Patrimonio", "Controvalore Portafoglio", tot_investito, "EUR"),
        ("Patrimonio", "Costo Storico (PMC)", _clean_num(asset_sum.get("total_invested", 0.0)), "EUR"),
        ("Patrimonio", "Plus/Minusvalenza Latente", _clean_num(asset_sum.get("total_unrealized_pl", 0.0)), "EUR"),
        ("Patrimonio", "Plus/Minusvalenza Percentuale", _clean_num(asset_sum.get("total_unrealized_pl_pct", 0.0)), "%"),
        ("Patrimonio", "Flusso Netto Cassa Periodo", _clean_num(cash_sum.get("net_cashflow", 0.0)), "EUR"),
        ("Patrimonio", "Tasso di Risparmio", _clean_num(cash_sum.get("savings_rate_pct", 0.0)), "%"),
        ("Patrimonio", "Dividendi Annui Attesi", _clean_num(asset_sum.get("expected_annual_income", 0.0)), "EUR"),
        ("Patrimonio", "Portfolio Dividend Yield", _clean_num(asset_sum.get("portfolio_dividend_yield", 0.0)), "%"),
        # Rischio & Performance
        ("Rischio & Benchmark", "Indice di Sharpe", _clean_num(risk_sum.get("sharpe_ratio", 0.0)), "Ratio"),
        ("Rischio & Benchmark", "Indice di Sortino", _clean_num(risk_sum.get("sortino_ratio", 0.0)), "Ratio"),
        ("Rischio & Benchmark", "Indice di Calmar", _clean_num(risk_sum.get("calmar_ratio", 0.0)), "Ratio"),
        ("Rischio & Benchmark", "Indice di Treynor", _clean_num(risk_sum.get("treynor_ratio", 0.0)), "Ratio"),
        ("Rischio & Benchmark", "Rendimento Annualizzato (CAGR)", _clean_num(risk_sum.get("cagr", 0.0)), "%"),
        ("Rischio & Benchmark", "Benchmark CAGR", _clean_num(risk_sum.get("bmk_cagr", 0.0)), "%"),
        ("Rischio & Benchmark", "Volatilità Annualizzata", _clean_num(risk_sum.get("volatility_annualized", 0.0)), "%"),
        ("Rischio & Benchmark", "Downside Deviation", _clean_num(risk_sum.get("downside_deviation", 0.0)), "%"),
        ("Rischio & Benchmark", "Massimo Drawdown (MDD)", _clean_num(risk_sum.get("max_drawdown", 0.0)), "%"),
        ("Rischio & Benchmark", "Value at Risk (VaR 95% Annuale)", _clean_num(risk_sum.get("var_95_annual", 0.0)), "%"),
        ("Rischio & Benchmark", "Value at Risk (VaR 99% Annuale)", _clean_num(risk_sum.get("var_99_annual", 0.0)), "%"),
        ("Rischio & Benchmark", "Conditional VaR (CVaR 95% Annuale)", _clean_num(risk_sum.get("cvar_95_annual", 0.0)), "%"),
        ("Rischio & Benchmark", "Beta vs Benchmark", _clean_num(risk_sum.get("beta", 1.0)), "Beta"),
        ("Rischio & Benchmark", "Alfa di Jensen (Alpha)", _clean_num(risk_sum.get("alpha_jensen", 0.0)), "%"),
        ("Rischio & Benchmark", "Coefficiente Determinazione (R2)", _clean_num(risk_sum.get("r_squared", 0.0)), "R2"),
        ("Rischio & Benchmark", "Tracking Error vs Benchmark", _clean_num(risk_sum.get("tracking_error", 0.0)), "%"),
        ("Rischio & Benchmark", "Information Ratio", _clean_num(risk_sum.get("information_ratio", 0.0)), "Ratio"),
        ("Rischio & Benchmark", "Win Rate Giornaliero", _clean_num(risk_sum.get("win_rate", 0.0)), "%")
    ]

    df = pd.DataFrame(items, columns=["Categoria", "Metrica", "Valore_Numerico", "Unita_Misura"])
    csv_str = df.to_csv(index=False, sep=delimiter, decimal=decimal)
    return csv_str.encode("utf-8-sig")
