"""
Image parser (.png / .jpg) for LUCAINVESTRATTO.
Handles screenshots and receipts of bank statements or portfolio dashboards.
Uses Gemini Vision multimodal API if available, with intelligent OCR / structured fallback.
"""
import os
import io
import json
import re
from typing import List, Dict, Any, Optional
from PIL import Image

from lucainvestratto.models import Transaction, Holding
from lucainvestratto.parsers.base import ParseResult, clean_number, parse_flexible_date


def parse_image(file_bytes: bytes, account_id: str, filename: str = "") -> ParseResult:
    result = ParseResult()

    try:
        image = Image.open(io.BytesIO(file_bytes))
        width, height = image.size
    except Exception as e:
        result.success = False
        result.message = f"File immagine non valido o corrotto: {str(e)}"
        return result

    # Check for Gemini API key
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            prompt = """
            Sei un analista finanziario esperto. Analizza questa immagine di un estratto conto bancario o di un portafoglio investimenti.
            Estrai i dati in formato JSON strutturato con una delle due chiavi:
            1) Se contiene movimenti bancari / estratto conto:
            {
               "type": "transactions",
               "items": [
                  {"date": "YYYY-MM-DD", "description": "descrizione causale", "amount": 123.45, "category": "categoria spesa o entrata"}
               ]
            }
            (Usa importi positivi per entrate/accrediti, negativi per uscite/addebiti)
            
            2) Se contiene un portafoglio titoli / posizioni / azioni / ETF:
            {
               "type": "holdings",
               "items": [
                  {"symbol": "TICKER o ISIN", "name": "Nome Titolo", "quantity": 10.0, "current_price": 100.0, "average_buy_price": 90.0, "asset_class": "Azionario"}
               ]
            }
            Restituisci ESCLUSIVAMENTE il blocco JSON valido, senza testo markdown aggiuntivo.
            """

            response = model.generate_content([prompt, image])
            raw_text = response.text.strip()
            
            # Clean markdown codeblocks
            raw_text = re.sub(r"^```json\s*", "", raw_text)
            raw_text = re.sub(r"^```\s*", "", raw_text)
            raw_text = re.sub(r"```$", "", raw_text).strip()

            parsed = json.loads(raw_text)
            if parsed.get("type") == "holdings":
                result.detected_type = "holdings"
                holdings_list = []
                for item in parsed.get("items", []):
                    holdings_list.append(Holding(
                        account_id=account_id,
                        symbol=item.get("symbol", "N/A"),
                        name=item.get("name", item.get("symbol", "Asset")),
                        asset_class=item.get("asset_class", "Azionario (Equities)"),
                        quantity=clean_number(item.get("quantity", 1)),
                        average_buy_price=clean_number(item.get("average_buy_price", 0)),
                        current_price=clean_number(item.get("current_price", 0))
                    ))
                result.holdings = holdings_list
                result.message = f"Gemini Vision AI ha estratto con successo {len(holdings_list)} posizioni dall'immagine."
                return result
            else:
                result.detected_type = "transactions"
                tx_list = []
                for item in parsed.get("items", []):
                    amt = clean_number(item.get("amount", 0))
                    desc = item.get("description", "Movimento estratto da immagine")
                    tx_type = "Entrata (Inflow)" if amt >= 0 else "Uscita (Outflow)"
                    tx_list.append(Transaction(
                        account_id=account_id,
                        date=parse_flexible_date(item.get("date")),
                        type=tx_type,
                        category=item.get("category", "Altro"),
                        amount=amt,
                        description=desc
                    ))
                result.transactions = tx_list
                result.message = f"Gemini Vision AI ha estratto con successo {len(tx_list)} transazioni dall'immagine."
                return result

        except Exception as e:
            # Fallback to local image handler if API fails or rate limited
            pass

    # Local fallback pattern extractor
    # Attempt local pytesseract if available
    try:
        import pytesseract
        ocr_text = pytesseract.image_to_string(image)
        from lucainvestratto.parsers.txt_parser import parse_txt
        ocr_result = parse_txt(ocr_text.encode("utf-8"), account_id)
        if ocr_result.success and (ocr_result.transactions or ocr_result.holdings):
            ocr_result.message = f"OCR Locale ha estratto {len(ocr_result.transactions)} transazioni dall'immagine."
            return ocr_result
    except Exception:
        pass

    # Graceful fallback: Image loaded successfully, guide the user
    result.detected_type = "transactions"
    result.message = (
        f"Immagine caricata con successo ({width}x{height} px). "
        "Per l'estrazione automatica via Vision AI impostare la chiave GEMINI_API_KEY nel sistema, "
        "oppure inserire i movimenti rilevati visivamente."
    )
    result.success = True
    return result
