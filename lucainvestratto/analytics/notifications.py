"""
Notification and automated alert engine for LUCAINVESTRATTO.
Evaluates portfolio and bank statements against user-configured risk and cash flow thresholds.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

from lucainvestratto.models import Holding, Transaction, BankAccount
from lucainvestratto.settings import AppSettings
from lucainvestratto.analytics.assets import calculate_asset_summary
from lucainvestratto.analytics.cashflow import calculate_cashflow_summary
from lucainvestratto.analytics.risk import calculate_risk_metrics


@dataclass
class AlertItem:
    id: str
    title: str
    message: str
    level: str  # "danger", "warning", "info"
    icon: str
    current_value: str
    threshold_value: str


def evaluate_alerts(
    settings: AppSettings,
    accounts: List[BankAccount],
    holdings: List[Holding],
    transactions: List[Transaction]
) -> List[AlertItem]:
    alerts: List[AlertItem] = []

    # 1. Cash Balance Alert
    if settings.alert_min_cash_enabled:
        cash_sum = calculate_cashflow_summary(transactions, accounts)
        tot_cash = cash_sum["final_balance"]
        if tot_cash < settings.alert_min_cash_amount:
            alerts.append(AlertItem(
                id="alert_low_cash",
                title="Liquidità Sotto la Soglia Minima",
                message=f"La liquidità totale disponibile è pari a € {tot_cash:,.2f}, inferiore alla soglia di sicurezza impostata.",
                level="danger" if tot_cash < (settings.alert_min_cash_amount * 0.5) else "warning",
                icon="🚨" if tot_cash < (settings.alert_min_cash_amount * 0.5) else "⚠️",
                current_value=f"€ {tot_cash:,.2f}",
                threshold_value=f"€ {settings.alert_min_cash_amount:,.2f}"
            ))

    # 2. Portfolio Drawdown Alert
    if settings.alert_max_drawdown_enabled and holdings:
        risk_sum = calculate_risk_metrics(holdings)
        mdd = abs(risk_sum["current_drawdown"])
        if mdd >= settings.alert_max_drawdown_pct:
            alerts.append(AlertItem(
                id="alert_drawdown",
                title="Superamento Soglia Massimo Drawdown",
                message=f"Il drawdown attuale del portafoglio dal picco è pari al {mdd:.2f}%, superiore al limite di tolleranza impostato.",
                level="danger",
                icon="📉",
                current_value=f"-{mdd:.2f}%",
                threshold_value=f"{settings.alert_max_drawdown_pct:.1f}%"
            ))

    # 3. Asset Concentration Alert
    if settings.alert_max_weight_enabled and holdings:
        asset_sum = calculate_asset_summary(holdings)
        df_h = asset_sum["df_holdings"]
        if not df_h.empty:
            overweighted = df_h[df_h["weight_pct"] >= settings.alert_max_weight_pct]
            for _, h in overweighted.iterrows():
                alerts.append(AlertItem(
                    id=f"alert_weight_{h['symbol']}",
                    title=f"Eccesso di Concentrazione: {h['symbol']}",
                    message=f"Il titolo '{h['name']}' ({h['symbol']}) pesa per il {h['weight_pct']:.1f}% del portafoglio, superando la soglia di diversificazione del {settings.alert_max_weight_pct:.1f}%.",
                    level="warning",
                    icon="⚖️",
                    current_value=f"{h['weight_pct']:.1f}%",
                    threshold_value=f"{settings.alert_max_weight_pct:.1f}%"
                ))

    # 4. Large Outflow / Expense Alert
    if settings.alert_high_expense_enabled and transactions:
        large_outflows = [t for t in transactions if t.amount < -settings.alert_high_expense_amount]
        if large_outflows:
            latest_large = sorted(large_outflows, key=lambda x: x.date, reverse=True)[0]
            alerts.append(AlertItem(
                id="alert_high_expense",
                title="Rilevata Spesa / Uscita Rilevante",
                message=f"Rilevata operazione di importo elevato: '{latest_large.description}' pari a € {abs(latest_large.amount):,.2f} in data {latest_large.date}.",
                level="info",
                icon="💳",
                current_value=f"€ {abs(latest_large.amount):,.2f}",
                threshold_value=f"€ {settings.alert_high_expense_amount:,.2f}"
            ))

    return alerts
