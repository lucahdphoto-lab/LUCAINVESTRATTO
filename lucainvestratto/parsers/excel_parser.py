"""
Excel (.xlsx / .xls) parser for LUCAINVESTRATTO.
Supports multi-sheet workbooks, automatic detection of bank statements and investment positions.
"""
import io
import hashlib
from typing import List, Dict, Any, Optional
import pandas as pd

from lucainvestratto.models import Transaction, Holding
from lucainvestratto.parsers.base import ParseResult, clean_number, parse_flexible_date


def parse_excel(file_bytes: bytes, account_id: str, sheet_name: Optional[str] = None) -> ParseResult:
    result = ParseResult()

    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_names = excel_file.sheet_names
    except Exception as e:
        result.success = False
        result.message = f"Errore nell'apertura del file Excel: {str(e)}"
        return result

    # Select sheet
    target_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0]

    try:
        df = pd.read_excel(excel_file, sheet_name=target_sheet, dtype=str)
    except Exception as e:
        result.success = False
        result.message = f"Errore nella lettura del foglio '{target_sheet}': {str(e)}"
        return result

    df.columns = [str(c).strip().lower() for c in df.columns]
    result.raw_df_preview = df.head(10)

    # Detect if holdings or transactions
    holdings_keywords = ["titolo", "symbol", "ticker", "isin", "isin code", "strumento", "quantità", "shares", "pmc"]
    is_holdings = any(any(k in col for k in holdings_keywords) for col in df.columns)

    if is_holdings:
        result.detected_type = "holdings"
        symbol_col = next((c for c in df.columns if any(k in c for k in ["symbol", "ticker", "isin", "titolo", "codice"])), None)
        name_col = next((c for c in df.columns if any(k in c for k in ["name", "nome", "descrizione", "denominazione"])), symbol_col)
        qty_col = next((c for c in df.columns if any(k in c for k in ["quantit", "shares", "quote", "qta", "qty"])), None)
        pmc_col = next((c for c in df.columns if any(k in c for k in ["pmc", "prezzo acquisto", "cost", "prezzo medio", "buy price"])), None)
        price_col = next((c for c in df.columns if any(k in c for k in ["prezzo", "price", "ultimo", "valore", "close"])), pmc_col)
        class_col = next((c for c in df.columns if any(k in c for k in ["classe", "class", "tipo", "asset", "categoria"])), None)

        if not symbol_col or not qty_col:
            result.success = False
            result.message = "Colonne minime per posizioni (Simbolo/ISIN e Quantità) non trovate nel foglio Excel."
            return result

        holdings_list: List[Holding] = []
        for idx, row in df.iterrows():
            sym = str(row[symbol_col]).strip()
            if not sym or sym.lower() in ["nan", "none", ""]:
                continue
            name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else sym
            qty = clean_number(row[qty_col]) if qty_col and pd.notna(row[qty_col]) else 0.0
            pmc = clean_number(row[pmc_col]) if pmc_col and pd.notna(row[pmc_col]) else 0.0
            price = clean_number(row[price_col]) if price_col and pd.notna(row[price_col]) else pmc
            if price == 0.0:
                price = pmc
            asset_class = str(row[class_col]).strip() if class_col and pd.notna(row[class_col]) else "Azionario (Equities)"

            if qty > 0:
                h_id = f"h_{account_id}_{sym.strip().upper()}"
                holdings_list.append(Holding(
                    id=h_id,
                    account_id=account_id,
                    symbol=sym,
                    name=name,
                    asset_class=asset_class,
                    quantity=qty,
                    average_buy_price=pmc,
                    current_price=price
                ))

        result.holdings = holdings_list
        result.message = f"Rilevate con successo {len(holdings_list)} posizioni dal foglio Excel '{target_sheet}'."
    else:
        result.detected_type = "transactions"
        date_col = next((c for c in df.columns if any(k in c for k in ["data", "date", "valuta", "operazione"])), None)
        amount_col = next((c for c in df.columns if any(k in c for k in ["importo", "amount", "totale", "saldo", "euro", "valore"])), None)
        inflow_col = next((c for c in df.columns if any(k in c for k in ["avere", "entrate", "accredito", "inflow"])), None)
        outflow_col = next((c for c in df.columns if any(k in c for k in ["dare", "uscite", "addebito", "outflow"])), None)
        desc_col = next((c for c in df.columns if any(k in c for k in ["descrizione", "causale", "dettaglio", "beneficiario", "note"])), None)
        cat_col = next((c for c in df.columns if any(k in c for k in ["categoria", "category"])), None)

        if not date_col:
            result.success = False
            result.message = "Colonna con la data non trovata nel foglio Excel."
            return result

        tx_list: List[Transaction] = []
        for idx, row in df.iterrows():
            raw_date = row[date_col]
            if pd.isna(raw_date) or not str(raw_date).strip():
                continue

            iso_date = parse_flexible_date(raw_date)
            
            amt = 0.0
            if amount_col and pd.notna(row[amount_col]):
                amt = clean_number(row[amount_col])
            elif inflow_col or outflow_col:
                inflow_amt = clean_number(row[inflow_col]) if inflow_col and pd.notna(row[inflow_col]) else 0.0
                outflow_amt = clean_number(row[outflow_col]) if outflow_col and pd.notna(row[outflow_col]) else 0.0
                amt = inflow_amt - abs(outflow_amt)

            desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else "Movimento bancario"
            cat = str(row[cat_col]).strip() if cat_col and pd.notna(row[cat_col]) else "Altro"

            tx_type = "Entrata (Inflow)" if amt >= 0 else "Uscita (Outflow)"
            if "cedola" in desc.lower() or "dividendo" in desc.lower():
                tx_type = "Dividendo / Cedola (Income)"
                cat = "Dividendi Azionari" if "dividendo" in desc.lower() else "Cedole Obbligazionarie"
            elif "acquisto" in desc.lower() or "buy" in desc.lower():
                tx_type = "Acquisto Titoli (Buy)"
                cat = "Investimento Capitale"
            elif "giroconto" in desc.lower():
                tx_type = "Giroconto Interno (Transfer)"
                cat = "Bonifico / Giroconto"

            tx_sig = f"{account_id}_{iso_date}_{round(amt, 2)}_{desc.strip().lower()}"
            tx_id = f"tx_{hashlib.md5(tx_sig.encode('utf-8')).hexdigest()[:12]}"
            tx_list.append(Transaction(
                id=tx_id,
                account_id=account_id,
                date=iso_date,
                type=tx_type,
                category=cat,
                amount=amt,
                currency="EUR",
                description=desc
            ))

        result.transactions = tx_list
        result.message = f"Rilevate con successo {len(tx_list)} transazioni dal foglio Excel '{target_sheet}'."

    return result
