"""
Unified file parser router for LUCAINVESTRATTO.
Routes files based on extension (.xlsx, .csv, .txt, .png, .jpg) to their specialized parser.
"""
import os
from typing import Optional

from lucainvestratto.parsers.base import ParseResult
from lucainvestratto.parsers.csv_parser import parse_csv
from lucainvestratto.parsers.excel_parser import parse_excel
from lucainvestratto.parsers.txt_parser import parse_txt
from lucainvestratto.parsers.image_parser import parse_image


def parse_statement_file(file_bytes: bytes, filename: str, account_id: str, sheet_name: Optional[str] = None) -> ParseResult:
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".xlsx", ".xls"]:
        return parse_excel(file_bytes, account_id, sheet_name=sheet_name)
    elif ext == ".csv":
        return parse_csv(file_bytes, account_id, filename=filename)
    elif ext == ".txt":
        return parse_txt(file_bytes, account_id)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return parse_image(file_bytes, account_id, filename=filename)
    else:
        res = ParseResult()
        res.success = False
        res.message = f"Formato file '{ext}' non supportato. Formati validi: .xlsx, .csv, .txt, .png, .jpg"
        return res
