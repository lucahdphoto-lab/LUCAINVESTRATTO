"""
Base parser utilities and result structures for LUCAINVESTRATTO.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import re

from lucainvestratto.models import Transaction, Holding


@dataclass
class ParseResult:
    success: bool = True
    message: str = ""
    transactions: List[Transaction] = field(default_factory=list)
    holdings: List[Holding] = field(default_factory=list)
    detected_type: str = "transactions"  # "transactions" or "holdings"
    raw_df_preview: Optional[Any] = None
    errors: List[str] = field(default_factory=list)


def clean_number(val: Any) -> float:
    """
    Safely converts strings with European or US number formatting to float.
    Examples:
    '1.234,56' -> 1234.56
    '- € 1.500,00' -> -1500.00
    '1,234.56' -> 1234.56
    '1250' -> 1250.0
    """
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    # Remove currency symbols and non-numeric chars except -, +, ., ,
    s = re.sub(r"[^\d.,\-+]", "", s)
    if not s or s in ["-", "+"]:
        return 0.0

    # Determine decimal separator
    if "," in s and "." in s:
        # e.g. 1.234,56 (European) vs 1,234.56 (US)
        if s.rfind(",") > s.rfind("."):
            # European: '.' is thousands, ',' is decimal
            s = s.replace(".", "").replace(",", ".")
        else:
            # US: ',' is thousands, '.' is decimal
            s = s.replace(",", "")
    elif "," in s:
        # e.g. 1234,56 -> replace comma with dot
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_flexible_date(date_val: Any) -> str:
    """
    Parses various date formats to ISO YYYY-MM-DD.
    Supports DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, etc.
    """
    if not date_val:
        return date.today().isoformat()
    if isinstance(date_val, (date, datetime)):
        return date_val.strftime("%Y-%m-%d")

    s = str(date_val).strip()
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%Y/%m/%d", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try regex fallback for DD/MM/YYYY
    match = re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", s)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return date.today().isoformat()
