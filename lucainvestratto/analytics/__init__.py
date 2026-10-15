"""
Analytics package for LUCAINVESTRATTO.
"""
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics
from lucainvestratto.analytics.snapshots import (
    reconcile_snapshot_with_actual,
    calculate_snapshot_trends,
    parse_raw_text_to_allocations
)

__all__ = [
    "calculate_cashflow_summary",
    "calculate_asset_summary",
    "calculate_risk_metrics",
    "reconcile_snapshot_with_actual",
    "calculate_snapshot_trends",
    "parse_raw_text_to_allocations"
]

