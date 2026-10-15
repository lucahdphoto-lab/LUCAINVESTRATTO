"""
Cash flow and bank statement analytics engine for LUCAINVESTRATTO.
Computes daily running balances, monthly aggregation, categorization breakdown,
savings rates, and period-over-period cash flow statistics.
"""
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from lucainvestratto.models import Transaction, BankAccount


def calculate_cashflow_summary(
    transactions: List[Transaction],
    accounts: List[BankAccount],
    selected_account_id: str = "all"
) -> Dict[str, Any]:
    """
    Computes complete statement cashflow KPIs, monthly series, category breakdowns,
    and cumulative balance curve.
    """
    # Calculate starting initial balance
    if selected_account_id and selected_account_id != "all":
        initial_cash = sum(a.initial_balance for a in accounts if a.id == selected_account_id)
    else:
        initial_cash = sum(a.initial_balance for a in accounts)

    if not transactions:
        return {
            "initial_balance": initial_cash,
            "total_inflows": 0.0,
            "total_outflows": 0.0,
            "net_cashflow": 0.0,
            "final_balance": initial_cash,
            "savings_rate_pct": 0.0,
            "df_daily": pd.DataFrame(),
            "df_monthly": pd.DataFrame(),
            "category_inflows": pd.DataFrame(),
            "category_outflows": pd.DataFrame(),
            "transactions_count": 0
        }

    # Convert transactions to DataFrame
    data = []
    for tx in transactions:
        data.append({
            "id": tx.id,
            "account_id": tx.account_id,
            "date": pd.to_datetime(tx.date),
            "date_str": tx.date,
            "type": tx.type,
            "category": tx.category or "Altro",
            "amount": float(tx.amount),
            "currency": tx.currency,
            "description": tx.description,
            "fees": float(tx.fees or 0.0)
        })

    df = pd.DataFrame(data)
    df.sort_values(by="date", ascending=True, inplace=True)

    # Inflows (positive amounts) vs Outflows (negative amounts)
    # Ignore internal transfers (Giroconto) in net totals to avoid double counting if all accounts selected
    if selected_account_id == "all":
        df_effective = df[~df["type"].str.contains("Giroconto", case=False, na=False)].copy()
    else:
        df_effective = df.copy()

    total_inflows = float(df_effective[df_effective["amount"] > 0]["amount"].sum())
    total_outflows = abs(float(df_effective[df_effective["amount"] < 0]["amount"].sum()))
    net_cashflow = total_inflows - total_outflows
    final_balance = initial_cash + net_cashflow

    savings_rate = (net_cashflow / total_inflows * 100.0) if total_inflows > 0 else 0.0

    # Daily running balance curve
    df_daily = df.groupby("date")["amount"].sum().reset_index()
    df_daily.sort_values(by="date", ascending=True, inplace=True)
    df_daily["cumulative_cashflow"] = df_daily["amount"].cumsum()
    df_daily["balance"] = initial_cash + df_daily["cumulative_cashflow"]

    # Monthly aggregation
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    
    monthly_in = df[df["amount"] > 0].groupby("year_month")["amount"].sum()
    monthly_out = df[df["amount"] < 0].groupby("year_month")["amount"].sum().abs()
    
    all_months = sorted(list(set(df["year_month"].tolist())))
    monthly_data = []
    for m in all_months:
        inflow = float(monthly_in.get(m, 0.0))
        outflow = float(monthly_out.get(m, 0.0))
        net = inflow - outflow
        monthly_data.append({
            "Mese": m,
            "Entrate": inflow,
            "Uscite": outflow,
            "Netto": net
        })
    df_monthly = pd.DataFrame(monthly_data)

    # Category breakdowns
    inflows_mask = df["amount"] > 0
    outflows_mask = df["amount"] < 0

    df_cat_in = df[inflows_mask].groupby("category")["amount"].sum().reset_index()
    df_cat_in.columns = ["Categoria", "Totale (€)"]
    df_cat_in["Percentuale (%)"] = (df_cat_in["Totale (€)"] / total_inflows * 100.0) if total_inflows > 0 else 0.0
    df_cat_in.sort_values(by="Totale (€)", ascending=False, inplace=True)

    df_cat_out = df[outflows_mask].groupby("category")["amount"].sum().abs().reset_index()
    df_cat_out.columns = ["Categoria", "Totale (€)"]
    df_cat_out["Percentuale (%)"] = (df_cat_out["Totale (€)"] / total_outflows * 100.0) if total_outflows > 0 else 0.0
    df_cat_out.sort_values(by="Totale (€)", ascending=False, inplace=True)

    return {
        "initial_balance": initial_cash,
        "total_inflows": total_inflows,
        "total_outflows": total_outflows,
        "net_cashflow": net_cashflow,
        "final_balance": final_balance,
        "savings_rate_pct": savings_rate,
        "df_daily": df_daily,
        "df_monthly": df_monthly,
        "category_inflows": df_cat_in,
        "category_outflows": df_cat_out,
        "transactions_count": len(transactions)
    }
