"""
Snapshot and monthly reconciliation analytics engine for LUCAINVESTRATTO.
Provides:
1. Reconciliation (Quadratura) between bank statement snapshot images and internal books.
2. Historical trajectory analysis across monthly snapshots.
3. Multi-period asset allocation drift and breakdown.
4. Smart textual parsing helper for asset amounts and weights.
"""
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

from lucainvestratto.models import PortfolioSnapshot, Holding, BankAccount, Transaction
from lucainvestratto.parsers.base import clean_number


def reconcile_snapshot_with_actual(
    snapshot: PortfolioSnapshot,
    holdings: List[Holding],
    accounts: List[BankAccount],
    transactions: Optional[List[Transaction]] = None
) -> Dict[str, Any]:
    """
    Performs comprehensive reconciliation (Quadratura) between a bank snapshot
    and internal system records (accounts cash + holdings market value).
    
    Returns delta metrics, reconciliation status, and breakdown by asset class.
    """
    # 1. Filter accounts/holdings if snapshot is tied to a specific account
    target_acc_id = snapshot.account_id
    if target_acc_id and target_acc_id != "all":
        acc_list = [a for a in accounts if a.id == target_acc_id]
        h_list = [h for h in holdings if h.account_id == target_acc_id]
        tx_list = [t for t in (transactions or []) if t.account_id == target_acc_id]
    else:
        acc_list = accounts
        h_list = holdings
        tx_list = transactions or []

    # 2. Internal Cash Calculation
    # If transactions exist, calculate running balance up to snapshot date if possible
    snap_date_str = snapshot.snapshot_date
    internal_cash = 0.0
    for a in acc_list:
        # Starting balance
        balance = float(a.initial_balance)
        # Add cashflow up to snapshot date
        if tx_list:
            acc_txs = [t for t in tx_list if t.account_id == a.id]
            for t in acc_txs:
                if t.date <= snap_date_str:
                    # Income / Buy / Sell / Expense impacts
                    t_type = (t.type or "").lower()
                    amt = float(t.amount)
                    fees = float(t.fees or 0.0)
                    if any(w in t_type for w in ["accredito", "income", "interessi", "dividendo", "stipendio"]):
                        balance += amt - fees
                    elif any(w in t_type for w in ["spesa", "addebito", "expense", "commissione", "imposta"]):
                        balance -= (amt + fees)
                    elif "acquisto" in t_type or "buy" in t_type:
                        balance -= (amt + fees)
                    elif "vendita" in t_type or "sell" in t_type:
                        balance += (amt - fees)
                    elif "giroconto" in t_type or "transfer" in t_type:
                        balance += amt
        internal_cash += balance

    # 3. Internal Invested Calculation
    internal_invested = sum(h.market_value for h in h_list)
    internal_total_wealth = internal_cash + internal_invested

    # 4. Deltas
    reported_total = float(snapshot.total_wealth or 0.0)
    reported_cash = float(snapshot.liquid_cash or 0.0)
    reported_invested = float(snapshot.invested_amount or 0.0)

    # If snapshot invested is 0 but reported total > cash, infer invested
    if reported_invested == 0.0 and reported_total > reported_cash:
        reported_invested = reported_total - reported_cash

    delta_total = reported_total - internal_total_wealth
    delta_cash = reported_cash - internal_cash
    delta_invested = reported_invested - internal_invested

    delta_pct = (delta_total / internal_total_wealth * 100.0) if internal_total_wealth > 0 else 0.0

    # 5. Status determination
    abs_delta = abs(delta_total)
    if abs_delta < 1.0:
        status = "PERFETTAMENTE_QUADRATO"
        status_label = "✅ Perfettamente Quadrato"
        status_color = "#10b981"
        status_desc = "Il patrimonio riportato dall'estratto coincide al centesimo con la contabilità interna."
    elif abs_delta <= 50.0 or abs(delta_pct) <= 0.5:
        status = "DISCREPANZA_LIEVE"
        status_label = "⚠️ Discrepanza Minore (< 0.5% o < 50€)"
        status_color = "#f59e0b"
        status_desc = "Differenziale fisiologico dovuto a ratei d'interesse non ancora accreditati o arrotondamenti di cambio valuta."
    else:
        status = "DISCREPANZA_SIGNIFICATIVA"
        status_label = "❌ Discrepanza da Riconciliare"
        status_color = "#ef4444"
        status_desc = "Differenza rilevante: possibile movimento non censito, cedola non inserita o variazione mark-to-market dei prezzi."

    # 6. Allocation Level Comparison
    snapshot_allocs = snapshot.get_allocations()
    # Build internal asset class mapping
    internal_class_sums: Dict[str, float] = {}
    for h in h_list:
        cls_name = h.asset_class or "Altro / Non Classificato"
        internal_class_sums[cls_name] = internal_class_sums.get(cls_name, 0.0) + h.market_value
    
    if internal_cash > 0:
        internal_class_sums["Liquidità & Conti"] = internal_class_sums.get("Liquidità & Conti", 0.0) + internal_cash

    # Merge comparisons
    alloc_rows = []
    seen_classes = set()

    for item in snapshot_allocs:
        cls_name = item.get("asset_class", "Non specificato")
        seen_classes.add(cls_name)
        snap_amt = float(item.get("amount", 0.0))
        snap_pct = float(item.get("weight_pct", 0.0))
        
        # Match with internal
        intern_amt = internal_class_sums.get(cls_name, 0.0)
        # If no direct match, check partial string match
        if intern_amt == 0.0:
            for k, v in internal_class_sums.items():
                if k.lower() in cls_name.lower() or cls_name.lower() in k.lower():
                    intern_amt = v
                    break

        intern_pct = (intern_amt / internal_total_wealth * 100.0) if internal_total_wealth > 0 else 0.0
        d_amt = snap_amt - intern_amt
        d_p = snap_pct - intern_pct

        alloc_rows.append({
            "Classe Attivo": cls_name,
            "Importo Snapshot (€)": snap_amt,
            "Peso Snapshot (%)": round(snap_pct, 2),
            "Importo Sistema (€)": intern_amt,
            "Peso Sistema (%)": round(intern_pct, 2),
            "Scostamento (€)": d_amt,
            "Scostamento (%)": round(d_p, 2),
            "Allineato": "✅" if abs(d_amt) < 10.0 else ("⚠️" if abs(d_amt) < 250.0 else "❌")
        })

    df_alloc_comp = pd.DataFrame(alloc_rows) if alloc_rows else pd.DataFrame()

    return {
        "snapshot_id": snapshot.id,
        "snapshot_date": snapshot.snapshot_date,
        "reported_total": reported_total,
        "reported_cash": reported_cash,
        "reported_invested": reported_invested,
        "internal_total": internal_total_wealth,
        "internal_cash": internal_cash,
        "internal_invested": internal_invested,
        "delta_total": delta_total,
        "delta_cash": delta_cash,
        "delta_invested": delta_invested,
        "delta_pct": delta_pct,
        "status": status,
        "status_label": status_label,
        "status_color": status_color,
        "status_desc": status_desc,
        "df_alloc_comparison": df_alloc_comp
    }


def calculate_snapshot_trends(snapshots: List[PortfolioSnapshot]) -> Dict[str, Any]:
    """
    Computes historical time-series analytics, monthly capital gains,
    MoM changes, and asset allocation evolution across stored snapshots.
    """
    if not snapshots:
        return {
            "has_data": False,
            "count": 0,
            "df_snapshots": pd.DataFrame(),
            "df_allocations_history": pd.DataFrame(),
            "total_gain": 0.0,
            "total_gain_pct": 0.0,
            "cagr": 0.0,
            "latest_wealth": 0.0,
            "earliest_wealth": 0.0
        }

    # Sort chronological
    sorted_snaps = sorted(snapshots, key=lambda s: s.snapshot_date)

    rows = []
    alloc_history_rows = []

    for i, s in enumerate(sorted_snaps):
        tot = float(s.total_wealth or 0.0)
        cash = float(s.liquid_cash or 0.0)
        inv = float(s.invested_amount or 0.0)
        if inv == 0.0 and tot > cash:
            inv = tot - cash

        prev_tot = float(sorted_snaps[i - 1].total_wealth or 0.0) if i > 0 else tot
        mom_eur = tot - prev_tot if i > 0 else 0.0
        mom_pct = ((tot - prev_tot) / prev_tot * 100.0) if (i > 0 and prev_tot > 0) else 0.0

        rows.append({
            "id": s.id,
            "Data Snapshot": s.snapshot_date,
            "Patrimonio Totale (€)": tot,
            "Liquidità (€)": cash,
            "Investito (€)": inv,
            "Variazione Mensile (€)": mom_eur,
            "Variazione Mensile (%)": mom_pct,
            "Note": s.notes or "",
            "Immagine": "Presente" if s.image_base64 else "Nessuna"
        })

        # Process allocations for multi-period drift
        allocs = s.get_allocations()
        for a in allocs:
            alloc_history_rows.append({
                "Data": s.snapshot_date,
                "Classe Attivo": a.get("asset_class", "Altro"),
                "Importo (€)": float(a.get("amount", 0.0)),
                "Percentuale (%)": float(a.get("weight_pct", 0.0))
            })

    df_snaps = pd.DataFrame(rows)
    df_alloc_hist = pd.DataFrame(alloc_history_rows) if alloc_history_rows else pd.DataFrame()

    earliest_w = sorted_snaps[0].total_wealth
    latest_w = sorted_snaps[-1].total_wealth
    total_gain = latest_w - earliest_w
    total_gain_pct = (total_gain / earliest_w * 100.0) if earliest_w > 0 else 0.0

    # Calculate CAGR if more than 30 days between first and last
    cagr = 0.0
    try:
        d1 = datetime.fromisoformat(sorted_snaps[0].snapshot_date)
        d2 = datetime.fromisoformat(sorted_snaps[-1].snapshot_date)
        days = (d2 - d1).days
        if days >= 30 and earliest_w > 0 and latest_w > 0:
            years = days / 365.25
            cagr = ((latest_w / earliest_w) ** (1.0 / years) - 1.0) * 100.0
    except Exception:
        cagr = 0.0

    return {
        "has_data": True,
        "count": len(sorted_snaps),
        "df_snapshots": df_snaps,
        "df_allocations_history": df_alloc_hist,
        "total_gain": total_gain,
        "total_gain_pct": total_gain_pct,
        "cagr": cagr,
        "latest_wealth": latest_w,
        "earliest_wealth": earliest_w,
        "latest_date": sorted_snaps[-1].snapshot_date,
        "earliest_date": sorted_snaps[0].snapshot_date
    }


def parse_raw_text_to_allocations(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses unstructured lines from OCR, copy-pasted bank statement reports or notes
    into a structured list of asset class breakdown dictionaries.
    
    Recognizes patterns such as:
    - 'Azionario Globale: 50.000 € (35%)'
    - 'Liquidità 25000 18%'
    - 'ETF Obbligazionari | 30,500.00 | 25.5%'
    """
    if not raw_text or not raw_text.strip():
        return []

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    allocations = []

    for line in lines:
        # Check percentage pattern: e.g. 25.5% or 25% or 25,5%
        pct_match = re.search(r'(\d+[\.,]?\d*)\s*%', line)
        weight_pct = float(pct_match.group(1).replace(',', '.')) if pct_match else 0.0

        # Remove percentage part from text to extract amounts and labels
        cleaned = re.sub(r'\(?\s*\d+[\.,]?\d*\s*%\s*\)?', '', line)

        # Find potential currency / amount numbers: e.g. 50.000,00 or 30.000 or 20000
        num_matches = re.findall(r'(?:^|[\s:;|\(\[])([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,2})?|[0-9]+(?:[.,][0-9]{1,2})?)(?=$|[\s€\)\],;])', cleaned)
        amount = 0.0
        if num_matches:
            candidates = [clean_number(m) for m in num_matches if clean_number(m) > 0]
            if candidates:
                amount = max(candidates)

        # Extract name
        # Strip numbers, symbols, delimiters
        name = re.sub(r'[\d.,€%|:;()\-]', ' ', line).strip()
        name = re.sub(r'\s+', ' ', name)

        if not name:
            name = "Classe Sconosciuta"

        allocations.append({
            "asset_class": name,
            "amount": amount,
            "weight_pct": weight_pct
        })

    # If weights are missing, recalculate weights from amounts
    total_parsed_amt = sum(a["amount"] for a in allocations)
    if total_parsed_amt > 0:
        for a in allocations:
            if a["weight_pct"] == 0.0:
                a["weight_pct"] = round((a["amount"] / total_parsed_amt) * 100.0, 2)

    return allocations
