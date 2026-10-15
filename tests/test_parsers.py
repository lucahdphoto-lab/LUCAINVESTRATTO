"""
Comprehensive automated tests for LUCAINVESTRATTO:
- CSV parser (transactions & holdings)
- Excel parser (.xlsx)
- Text parser (.txt)
- Image parser (.png / .jpg)
- Report generators (.pdf, .xlsx, .txt)
"""
import io
import os
import unittest
from datetime import date
from PIL import Image
import pandas as pd

from lucainvestratto.db import db
from lucainvestratto.parsers import parse_statement_file
from lucainvestratto.export import generate_pdf_report, generate_excel_report, generate_txt_report


class TestLucaInvestratto(unittest.TestCase):

    def setUp(self):
        db.load_demo_data(reset=True)
        self.accounts = db.get_accounts()
        self.holdings = db.get_holdings()
        self.transactions = db.get_transactions()
        self.account_id = self.accounts[0].id

    def test_csv_transactions_parser(self):
        csv_data = """Data;Descrizione;Importo;Categoria
15/05/2024;Bonifico Ricevuto Stipendio;+3500,00;Stipendio
20/05/2024;Supermercato Esselunga;-120,50;Alimentari
25/05/2024;Ristorante Pizzeria;-45,00;Svago
""".encode("utf-8")

        res = parse_statement_file(csv_data, "estratto_conto.csv", self.account_id)
        self.assertTrue(res.success)
        self.assertEqual(res.detected_type, "transactions")
        self.assertEqual(len(res.transactions), 3)
        self.assertEqual(res.transactions[0].amount, 3500.0)
        self.assertEqual(res.transactions[1].amount, -120.50)

    def test_csv_holdings_parser(self):
        csv_holdings = """ISIN;Titolo;Quantità;PMC;Prezzo;Asset Class
IE00BK5BQT80;Vanguard FTSE All-World;150;105,20;121,50;ETF / Fondi
US0378331005;Apple Inc.;50;150,00;220,00;Azionario
""".encode("utf-8")

        res = parse_statement_file(csv_holdings, "portafoglio.csv", self.account_id)
        self.assertTrue(res.success)
        self.assertEqual(res.detected_type, "holdings")
        self.assertEqual(len(res.holdings), 2)
        self.assertEqual(res.holdings[0].symbol, "IE00BK5BQT80")
        self.assertEqual(res.holdings[0].quantity, 150.0)
        self.assertEqual(res.holdings[0].current_price, 121.50)

    def test_excel_parser(self):
        df = pd.DataFrame([
            {"Data": "2024-06-01", "Descrizione": "Cedola BTP", "Importo": "400.00", "Categoria": "Cedole"},
            {"Data": "2024-06-05", "Descrizione": "Spesa Bolletta Luce", "Importo": "-85.30", "Categoria": "Utenze"}
        ])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Movimenti")
        excel_bytes = buffer.getvalue()

        res = parse_statement_file(excel_bytes, "estratto.xlsx", self.account_id)
        self.assertTrue(res.success)
        self.assertEqual(len(res.transactions), 2)

    def test_txt_parser(self):
        txt_data = """
ESTRATTO CONTO BANCARIO MENSILE
10/01/2024 Accredito Canone Affitto +800,00 EUR
12/01/2024 Pagamento Bolletta Gas -115,20 EUR
18/01/2024 Rifornimento Carburante -70,00 EUR
""".encode("utf-8")

        res = parse_statement_file(txt_data, "estratto.txt", self.account_id)
        self.assertTrue(res.success)
        self.assertEqual(len(res.transactions), 3)
        self.assertEqual(res.transactions[0].amount, 800.0)
        self.assertEqual(res.transactions[1].amount, -115.20)

    def test_image_parser(self):
        # Create a small valid test PNG image
        img = Image.new("RGB", (200, 100), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        res = parse_statement_file(png_bytes, "screenshot_saldo.png", self.account_id)
        self.assertTrue(res.success)

    def test_exports(self):
        pdf_bytes = generate_pdf_report(self.accounts, self.holdings, self.transactions)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

        xlsx_bytes = generate_excel_report(self.accounts, self.holdings, self.transactions)
        self.assertGreater(len(xlsx_bytes), 1000)

        txt_str = generate_txt_report(self.accounts, self.holdings, self.transactions)
        self.assertIn("LUCAINVESTRATTO", txt_str)
        self.assertIn("Indice di Sharpe", txt_str)


if __name__ == "__main__":
    unittest.main()
