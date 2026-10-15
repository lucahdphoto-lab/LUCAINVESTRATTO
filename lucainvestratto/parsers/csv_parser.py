"""
CSV bank statement and investment positions parser for LUCAINVESTRATTO.
Supports auto-delimiter detection (; , tab), European number formats,
and automatic column detection.
"""
import io
import csv
from typing import List, Dict, Any, Optional
import pandas as pd

from lucainvestratto.models import Transaction, Holding
from lucainvestratto.parsers.base import ParseResult, clean_number, parse_flexible_date


def parse_csv(file_bytes: bytes, account_id: str, filename: str = "") -> ParseResult:
    result = ParseResult()

    # Try different encodings
    text_content = ""
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            text_content = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if not text_content:
        result.success = False
        result.message = "Impossibile decodificare il file CSV con le codifiche standard."
        return result

    # Detect delimiter
    sample = text_content[:4096]
    delimiter = ";"
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        delimiter = dialect.delimiter
    except Exception:
        if ";" in sample and sample.count(";") > sample.count(","):
            delimiter = ";"
        elif "\t" in sample:
            delimiter = "\t"
        else:
            delimiter = ","

    try:
        df = pd.read_csv(io.StringIO(text_content), sep=delimiter, dtype=str)
    except Exception as e:
        result.success = False
        result.message = f"Errore durante la lettura del CSV: {str(e)}"
        return result

    # Clean column names
    df.columns = [str(c).strip().lower() for c in df.columns]
    result.raw_df_preview = df.head(10)

    # Determine if this CSV represents Holdings/Investments or Bank Transactions
    holdings_keywords = ["titolo", "symbol", "ticker", "isin", "isin code", "strumento", "quantità", "shares", "pmc"]
    is_holdings = any(any(k in col for k in holdings_keywords) for col in df.columns)

    if is_holdings:
        result.detected_type = "holdings"
        # Parse Holdings
        symbol_col = next((c for c in df.columns if any(k in c for k in ["symbol", "ticker", "isin", "titolo", "codice"])), None)
        name_col = next((c for c in df.columns if any(k in c for k in ["name", "nome", "descrizione", "denominazione"])), symbol_col)
        qty_col = next((c for c in df.columns if any(k in c for k in ["quantit", "shares", "quote", "qta", "qty"])), None)
        pmc_col = next((c for c in df.columns if any(k in c for k in ["pmc", "prezzo acquisto", "cost", "prezzo medio", "buy price"])), None)
        price_col = next((c for c in df.columns if any(k in c for k in ["prezzo", "price", "ultimo", "valore", "close"])), pmc_col)
        class_col = next((c for c in df.columns if any(k in c for k in ["classe", "class", "tipo", "asset", "categoria"])), None)

        if not symbol_col or not qty_col:
            result.success = False
            result.message = "Colonne minime per posizioni (Simbolo/ISIN e Quantità) non trovate nel file."
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
                holdings_list.append(Holding(
                    account_id=account_id,
                    symbol=sym,
                    name=name,
                    asset_class=asset_class,
                    quantity=qty,
                    average_buy_price=pmc,
                    current_price=price
                ))

        result.holdings = holdings_list
        result.message = f"Rilevate con successo {len(holdings_list)} posizioni di investimento dal file CSV."
    else:
        result.detected_type = "transactions"
        # Parse Bank Transactions
        date_col = next((c for c in df.columns if any(k in c for k in ["data", "date", "valuta", "operazione"])), None)
        amount_col = next((c for c in df.columns if any(k in c for k in ["importo", "amount", "totale", "saldo", "euro", "valore"])), None)
        inflow_col = next((c for c in df.columns if any(k in c for k in ["avere", "entrate", "accredito", "inflow"])), None)
        outflow_col = next((c for c in df.columns if any(k in c for k in ["dare", "uscite", "addebito", "outflow"])), None)
        desc_col = next((c for c in df.columns if any(k in c for k in ["descrizione", "causale", "dettaglio", "beneficiario", "note"])), None)
        cat_col = next((c for c in df.columns if any(k in c for k in ["categoria", "category"])), None)

        if not date_col:
            result.success = False
            result.message = "Colonna con la data dell'operazione non individuata."
            return result

        tx_list: List[Transaction] = []
        for idx, row in df.iterrows():
            raw_date = row[date_col]
            if pd.isna(raw_date) or not str(raw_date).strip():
                continue

            iso_date = parse_flexible_date(raw_date)
            
            # Determine amount
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

            tx_list.append(Transaction(
                account_id=account_id,
                date=iso_date,
                type=tx_type,
                category=cat,
                amount=amt,
                currency="EUR",
                description=desc
            ))

        result.transactions = tx_list
        result.message = f"Rilevate con successo {len(tx_list)} transazioni di estratto conto dal file CSV."

    return result
