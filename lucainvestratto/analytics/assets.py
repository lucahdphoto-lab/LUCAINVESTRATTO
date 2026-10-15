"""
Asset allocation and holdings analytics engine for LUCAINVESTRATTO.
Computes multi-dimensional allocation (class, sector, geography, currency),
cost basis (PMC), unrealized P&L, expected dividend cash flow, and portfolio concentration.
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from lucainvestratto.models import Holding


def calculate_asset_summary(holdings: List[Holding]) -> Dict[str, Any]:
    """
    Computes portfolio-wide valuation, asset class breakdown,
    geographical and sector distributions, performance ranking, and concentration risk.
    """
    if not holdings:
        return {
            "total_invested": 0.0,
            "total_market_value": 0.0,
            "total_unrealized_pl": 0.0,
            "total_unrealized_pl_pct": 0.0,
            "expected_annual_income": 0.0,
            "portfolio_dividend_yield": 0.0,
            "hhi_concentration": 0.0,
            "df_holdings": pd.DataFrame(),
            "df_by_class": pd.DataFrame(),
            "df_by_sector": pd.DataFrame(),
            "df_by_geography": pd.DataFrame(),
            "df_by_currency": pd.DataFrame(),
            "top_gainers": pd.DataFrame(),
            "top_losers": pd.DataFrame(),
            "count": 0
        }

    # Extract holdings data
    rows = []
    total_market_value = 0.0
    total_invested = 0.0
    total_income = 0.0

    for h in holdings:
        cost = h.total_cost
        mv = h.market_value
        pl = h.unrealized_pl
        pl_pct = h.unrealized_pl_pct
        income = h.expected_annual_income

        total_invested += cost
        total_market_value += mv
        total_income += income

        rows.append({
            "id": h.id,
            "account_id": h.account_id,
            "symbol": h.symbol,
            "name": h.name,
            "asset_class": h.asset_class,
            "sector": h.sector,
            "geography": h.geography,
            "currency": h.currency,
            "quantity": h.quantity,
            "average_buy_price": h.average_buy_price,
            "current_price": h.current_price,
            "total_cost": cost,
            "market_value": mv,
            "unrealized_pl": pl,
            "unrealized_pl_pct": pl_pct,
            "annual_dividend_yield": h.annual_dividend_yield,
            "expected_annual_income": income,
            "duration": h.duration
        })

    df_holdings = pd.DataFrame(rows)

    # Calculate Weights
    if total_market_value > 0:
        df_holdings["weight_pct"] = (df_holdings["market_value"] / total_market_value) * 100.0
    else:
        df_holdings["weight_pct"] = 0.0

    # Sort holdings by weight
    df_holdings.sort_values(by="market_value", ascending=False, inplace=True)

    # Portfolio metrics
    total_unrealized_pl = total_market_value - total_invested
    total_unrealized_pl_pct = (total_unrealized_pl / total_invested * 100.0) if total_invested > 0 else 0.0
    portfolio_dividend_yield = (total_income / total_market_value * 100.0) if total_market_value > 0 else 0.0

    # Herfindahl-Hirschman Index (Concentration measure: sum of squared weights)
    hhi = float(np.sum((df_holdings["weight_pct"] / 100.0) ** 2))

    # Aggregations
    def aggregate_by_dim(dim_col: str) -> pd.DataFrame:
        agg = df_holdings.groupby(dim_col).agg(
            market_value=("market_value", "sum"),
            total_cost=("total_cost", "sum"),
            unrealized_pl=("unrealized_pl", "sum"),
            expected_income=("expected_annual_income", "sum")
        ).reset_index()
        agg["weight_pct"] = (agg["market_value"] / total_market_value * 100.0) if total_market_value > 0 else 0.0
        agg["pl_pct"] = np.where(agg["total_cost"] > 0, (agg["unrealized_pl"] / agg["total_cost"]) * 100.0, 0.0)
        agg.sort_values(by="market_value", ascending=False, inplace=True)
        return agg

    df_by_class = aggregate_by_dim("asset_class")
    df_by_sector = aggregate_by_dim("sector")
    df_by_geography = aggregate_by_dim("geography")
    df_by_currency = aggregate_by_dim("currency")

    # Top Gainers / Losers
    top_gainers = df_holdings.sort_values(by="unrealized_pl_pct", ascending=False).head(5)
    top_losers = df_holdings.sort_values(by="unrealized_pl_pct", ascending=True).head(5)

    return {
        "total_invested": total_invested,
        "total_market_value": total_market_value,
        "total_unrealized_pl": total_unrealized_pl,
        "total_unrealized_pl_pct": total_unrealized_pl_pct,
        "expected_annual_income": total_income,
        "portfolio_dividend_yield": portfolio_dividend_yield,
        "hhi_concentration": hhi,
        "df_holdings": df_holdings,
        "df_by_class": df_by_class,
        "df_by_sector": df_by_sector,
        "df_by_geography": df_by_geography,
        "df_by_currency": df_by_currency,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "count": len(holdings)
    }
