"""
Text statement parser (.txt) for LUCAINVESTRATTO.
Handles delimited text, structured logs, and pattern-based regex extraction from bank statements.
"""
import re
from typing import List, Dict, Any
import pandas as pd

from lucainvestratto.models import Transaction
from lucainvestratto.parsers.base import ParseResult, clean_number, parse_flexible_date


def parse_txt(file_bytes: bytes, account_id: str) -> ParseResult:
    result = ParseResult()
    result.detected_type = "transactions"

    text = ""
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if not text:
        result.success = False
        result.message = "Impossibile leggere il file di testo con codifiche standard."
        return result

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        result.success = False
        result.message = "Il file di testo è vuoto."
        return result

    tx_list: List[Transaction] = []

    # Regex for typical bank statement line:
    # E.g.: "15/04/2024 Pagamento POS Supermercato -45,80 EUR"
    # or "2024-03-27 | Accredito Stipendio | +3.200,00"
    date_regex = re.compile(r"(\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}\b|\b\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}\b)")
    amount_regex = re.compile(r"([+-]?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})|\b\d+[.,]\d{2}\b)")

    for line in lines:
        date_match = date_regex.search(line)
        if not date_match:
            continue

        raw_date = date_match.group(1)
        iso_date = parse_flexible_date(raw_date)

        # Remove date from line to find amount and description
        remainder = line[:date_match.start()] + " " + line[date_match.end():]
        amounts = amount_regex.findall(remainder)

        if not amounts:
            continue

        # Usually the last numeric figure in a bank line is the amount or balance
        raw_amt = amounts[-1]
        amt = clean_number(raw_amt)

        # Check if preceded by minus or debit keywords
        lower_line = line.lower()
        if "-" in raw_amt or "addebito" in lower_line or "prelievo" in lower_line or "spesa" in lower_line or "uscita" in lower_line:
            amt = -abs(amt)
        elif "+" in raw_amt or "accredito" in lower_line or "stipendio" in lower_line or "entrata" in lower_line:
            amt = abs(amt)

        # Clean description: strip date and amount from line
        desc = remainder.replace(raw_amt, "").strip()
        desc = re.sub(r"[|;,\t]+", " ", desc)
        desc = re.sub(r"\s{2,}", " ", desc).strip()
        if not desc:
            desc = "Movimento estratto conto"

        cat = "Altro"
        if "stipendio" in desc.lower():
            cat = "Stipendio / Reddito"
        elif "dividendo" in desc.lower() or "cedola" in desc.lower():
            cat = "Dividendi Azionari"
        elif "affitto" in desc.lower() or "canone" in desc.lower():
            cat = "Spese Fisse / Utenze"
        elif "bonifico" in desc.lower() or "giroconto" in desc.lower():
            cat = "Bonifico / Giroconto"
        elif "commission" in desc.lower():
            cat = "Commissioni Bancarie / Trading"

        tx_type = "Entrata (Inflow)" if amt >= 0 else "Uscita (Outflow)"

        tx_list.append(Transaction(
            account_id=account_id,
            date=iso_date,
            type=tx_type,
            category=cat,
            amount=amt,
            currency="EUR",
            description=desc
        ))

    if tx_list:
        result.transactions = tx_list
        result.message = f"Estratte con successo {len(tx_list)} transazioni dal file .txt."
    else:
        result.success = False
        result.message = "Nessuna riga di transazione valida con data e importo individuata nel file di testo."

    return result
