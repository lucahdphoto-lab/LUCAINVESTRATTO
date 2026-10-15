"""
Data audit, alignment and recalculation engine for LUCAINVESTRATTO.
Performs integrity checks, duplicate detection, running cashflow reconciliation,
and portfolio recalculation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import pandas as pd

from lucainvestratto.db import db
from lucainvestratto.models import BankAccount, Transaction, Holding


@dataclass
class AuditReport:
    total_accounts: int = 0
    total_transactions: int = 0
    total_holdings: int = 0
    duplicate_transactions_count: int = 0
    orphaned_transactions_count: int = 0
    orphaned_holdings_count: int = 0
    unbalanced_transfers_count: int = 0
    invalid_holdings_count: int = 0
    account_balances: List[Dict[str, Any]] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)
    status: str = "OK"  # "OK", "WARNING", "ERROR"


def run_data_audit() -> AuditReport:
    accounts = db.get_accounts()
    transactions = db.get_transactions()
    holdings = db.get_holdings()

    report = AuditReport(
        total_accounts=len(accounts),
        total_transactions=len(transactions),
        total_holdings=len(holdings)
    )

    account_ids = {a.id for a in accounts}

    # 1. Orphaned records
    orphaned_tx = [t for t in transactions if t.account_id not in account_ids]
    report.orphaned_transactions_count = len(orphaned_tx)
    if orphaned_tx:
        report.issues_found.append(f"Trovate {len(orphaned_tx)} transazioni orfane (collegate a conti non più esistenti).")

    orphaned_h = [h for h in holdings if h.account_id not in account_ids]
    report.orphaned_holdings_count = len(orphaned_h)
    if orphaned_h:
        report.issues_found.append(f"Trovati {len(orphaned_h)} titoli orfani (collegati a conti non più esistenti).")

    # 2. Duplicate Transactions
    seen = set()
    dup_count = 0
    for tx in transactions:
        key = (tx.account_id, tx.date, round(tx.amount, 2), tx.description.strip().lower())
        if key in seen:
            dup_count += 1
        else:
            seen.add(key)
    report.duplicate_transactions_count = dup_count
    if dup_count > 0:
        report.issues_found.append(f"Rilevate {dup_count} transazioni identiche o duplicate nel database.")

    # 3. Invalid holdings
    invalid_h = [h for h in holdings if h.quantity <= 0 or h.current_price < 0 or h.average_buy_price < 0]
    report.invalid_holdings_count = len(invalid_h)
    if invalid_h:
        report.issues_found.append(f"Rilevati {len(invalid_h)} titoli con quantità o prezzo non validi (<= 0).")

    # 4. Unbalanced internal transfers (Giroconti)
    transfers = [t for t in transactions if "giroconto" in t.type.lower() or "giroconto" in t.category.lower()]
    net_transfer = sum(t.amount for t in transfers)
    if abs(net_transfer) > 0.05 and len(transfers) > 0:
        report.unbalanced_transfers_count = len(transfers)
        report.issues_found.append(f"Disallineamento nei giroconti interni: sbilanciamento netto di € {net_transfer:+,.2f}.")

    # 5. Account balances check
    for acc in accounts:
        acc_txs = [t for t in transactions if t.account_id == acc.id]
        net_flow = sum(t.amount for t in acc_txs)
        final_cash = acc.initial_balance + net_flow
        acc_h = [h for h in holdings if h.account_id == acc.id]
        total_inv = sum(h.market_value for h in acc_h)

        report.account_balances.append({
            "Conto": acc.name,
            "Banca": acc.bank_name or "-",
            "Saldo Iniziale": acc.initial_balance,
            "Flusso Transazioni": net_flow,
            "Liquidità Effettiva": final_cash,
            "Portafoglio Investito": total_inv,
            "Patrimonio Totale": final_cash + total_inv,
            "Numero Movimenti": len(acc_txs),
            "Numero Titoli": len(acc_h)
        })

    if report.issues_found:
        report.status = "WARNING"
    else:
        report.status = "OK"

    return report


def execute_recalculation_and_alignment() -> Dict[str, Any]:
    """
    Executes automated data cleansing and recalculation:
    1. Removes orphaned records.
    2. De-duplicates identical transactions.
    3. Normalizes and recomputes holding totals.
    """
    accounts = db.get_accounts()
    transactions = db.get_transactions()
    holdings = db.get_holdings()
    account_ids = {a.id for a in accounts}

    removed_orphans_tx = 0
    removed_orphans_h = 0
    removed_duplicates = 0

    # 1. Clean orphaned records
    for t in transactions:
        if t.account_id not in account_ids:
            db.delete_transaction(t.id)
            removed_orphans_tx += 1

    for h in holdings:
        if h.account_id not in account_ids:
            db.delete_holding(h.id)
            removed_orphans_h += 1

    # 2. De-duplicate transactions
    fresh_txs = db.get_transactions()
    seen = set()
    for tx in fresh_txs:
        key = (tx.account_id, tx.date, round(tx.amount, 2), tx.description.strip().lower())
        if key in seen:
            db.delete_transaction(tx.id)
            removed_duplicates += 1
        else:
            seen.add(key)

    # 3. Re-save/normalize holdings to ensure all computed fields are up-to-date
    fresh_h = db.get_holdings()
    for h in fresh_h:
        # Guarantee non-negative values
        h.quantity = max(0.0, float(h.quantity))
        h.average_buy_price = max(0.0, float(h.average_buy_price))
        h.current_price = max(0.0, float(h.current_price))
        db.save_holding(h)

    return {
        "success": True,
        "removed_orphans_transactions": removed_orphans_tx,
        "removed_orphans_holdings": removed_orphans_h,
        "removed_duplicates": removed_duplicates,
        "normalized_holdings": len(fresh_h),
        "total_active_accounts": len(accounts),
        "message": f"Allineamento completato: {removed_duplicates} duplicati rimossi, {removed_orphans_tx + removed_orphans_h} record orfani eliminati, {len(fresh_h)} posizioni ricalcolate."
    }
