"""
SQLite storage engine and repository for LUCAINVESTRATTO.
Handles persistent storage for bank accounts, transactions, and holdings,
plus initialization of realistic demo data.
"""
import os
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import random

from contextlib import contextmanager

from lucainvestratto.models import BankAccount, Transaction, Holding

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "lucainvestratto.db")

class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Accounts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                bank_name TEXT,
                account_type TEXT,
                currency TEXT DEFAULT 'EUR',
                iban TEXT,
                initial_balance REAL DEFAULT 0.0,
                notes TEXT,
                created_at TEXT
            )
            """)

            # Transactions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                date TEXT NOT NULL,
                value_date TEXT,
                type TEXT NOT NULL,
                category TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'EUR',
                description TEXT,
                asset_symbol TEXT,
                quantity REAL,
                unit_price REAL,
                fees REAL DEFAULT 0.0,
                notes TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
            )
            """)

            # Holdings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                sector TEXT,
                geography TEXT,
                currency TEXT DEFAULT 'EUR',
                quantity REAL NOT NULL,
                average_buy_price REAL NOT NULL,
                current_price REAL NOT NULL,
                annual_dividend_yield REAL DEFAULT 0.0,
                duration REAL DEFAULT 0.0,
                notes TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
            )
            """)
            conn.commit()

    # ================= ACCOUNTS =================
    def get_accounts(self) -> List[BankAccount]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY name ASC")
            rows = cursor.fetchall()
            return [BankAccount.from_dict(dict(r)) for r in rows]

    def get_account_by_id(self, account_id: str) -> Optional[BankAccount]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            return BankAccount.from_dict(dict(row)) if row else None

    def save_account(self, account: BankAccount) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO accounts (id, name, bank_name, account_type, currency, iban, initial_balance, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account.id, account.name, account.bank_name, account.account_type, account.currency,
                  account.iban, account.initial_balance, account.notes, account.created_at))
            conn.commit()

    def delete_account(self, account_id: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM holdings WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM transactions WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()

    # ================= TRANSACTIONS =================
    def get_transactions(self, account_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Transaction]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM transactions WHERE 1=1"
            params: list = []

            if account_id and account_id != "all":
                query += " AND account_id = ?"
                params.append(account_id)
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC, id DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Transaction.from_dict(dict(r)) for r in rows]

    def save_transaction(self, tx: Transaction) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO transactions (id, account_id, date, value_date, type, category, amount, currency, description, asset_symbol, quantity, unit_price, fees, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx.id, tx.account_id, tx.date, tx.value_date, tx.type, tx.category, tx.amount, tx.currency,
                  tx.description, tx.asset_symbol, tx.quantity, tx.unit_price, tx.fees, tx.notes))
            conn.commit()

    def save_transactions(self, transactions: List[Transaction]) -> int:
        if not transactions:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for tx in transactions:
                cursor.execute("""
                INSERT OR REPLACE INTO transactions (id, account_id, date, value_date, type, category, amount, currency, description, asset_symbol, quantity, unit_price, fees, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (tx.id, tx.account_id, tx.date, tx.value_date, tx.type, tx.category, tx.amount, tx.currency,
                      tx.description, tx.asset_symbol, tx.quantity, tx.unit_price, tx.fees, tx.notes))
            conn.commit()
            return len(transactions)

    def delete_transaction(self, tx_id: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            conn.commit()

    def clear_transactions(self, account_id: Optional[str] = None) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if account_id and account_id != "all":
                cursor.execute("DELETE FROM transactions WHERE account_id = ?", (account_id,))
            else:
                cursor.execute("DELETE FROM transactions")
            conn.commit()

    # ================= HOLDINGS =================
    def get_holdings(self, account_id: Optional[str] = None) -> List[Holding]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if account_id and account_id != "all":
                cursor.execute("SELECT * FROM holdings WHERE account_id = ? ORDER BY asset_class ASC, symbol ASC", (account_id,))
            else:
                cursor.execute("SELECT * FROM holdings ORDER BY asset_class ASC, symbol ASC")
            rows = cursor.fetchall()
            return [Holding.from_dict(dict(r)) for r in rows]

    def save_holding(self, holding: Holding) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO holdings (id, account_id, symbol, name, asset_class, sector, geography, currency, quantity, average_buy_price, current_price, annual_dividend_yield, duration, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (holding.id, holding.account_id, holding.symbol, holding.name, holding.asset_class, holding.sector,
                  holding.geography, holding.currency, holding.quantity, holding.average_buy_price, holding.current_price,
                  holding.annual_dividend_yield, holding.duration, holding.notes))
            conn.commit()

    def save_holdings(self, holdings: List[Holding]) -> int:
        if not holdings:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for h in holdings:
                cursor.execute("""
                INSERT OR REPLACE INTO holdings (id, account_id, symbol, name, asset_class, sector, geography, currency, quantity, average_buy_price, current_price, annual_dividend_yield, duration, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (h.id, h.account_id, h.symbol, h.name, h.asset_class, h.sector,
                      h.geography, h.currency, h.quantity, h.average_buy_price, h.current_price,
                      h.annual_dividend_yield, h.duration, h.notes))
            conn.commit()
            return len(holdings)

    def delete_holding(self, holding_id: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
            conn.commit()

    def clear_holdings(self, account_id: Optional[str] = None) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if account_id and account_id != "all":
                cursor.execute("DELETE FROM holdings WHERE account_id = ?", (account_id,))
            else:
                cursor.execute("DELETE FROM holdings")
            conn.commit()

    # ================= DEMO DATA LOADER =================
    def load_demo_data(self, reset: bool = False) -> None:
        if reset:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM holdings")
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM accounts")
                conn.commit()

        # Check if already populated
        if len(self.get_accounts()) > 0 and not reset:
            return

        # 1. Accounts
        acc_fineco = BankAccount(
            id="acc_fineco",
            name="Fineco Bank - Trading & Titoli",
            bank_name="FinecoBank S.p.A.",
            account_type="Dossier Titoli / Brokerage",
            currency="EUR",
            iban="IT60X0538701600000012345678",
            initial_balance=18450.0,
            notes="Conto principale per investimenti azionari ed ETF UCITS."
        )
        acc_intesa = BankAccount(
            id="acc_intesa",
            name="Intesa Sanpaolo - Conto Corrente",
            bank_name="Intesa Sanpaolo S.p.A.",
            account_type="Conto Corrente",
            currency="EUR",
            iban="IT99C03069096061000000876543",
            initial_balance=8720.50,
            notes="Conto operativo per stipendio e spese correnti personali."
        )
        acc_degiro = BankAccount(
            id="acc_degiro",
            name="Degiro - Global Portfolio",
            bank_name="Degiro / flatexDEGIRO Bank",
            account_type="Dossier Titoli / Brokerage",
            currency="EUR",
            iban="DE89370400440532013000",
            initial_balance=5300.0,
            notes="Portafoglio internazionale e azioni USA tech ad alta crescita."
        )
        acc_deposito = BankAccount(
            id="acc_deposito",
            name="Banca Mediolanum - Conto Deposito",
            bank_name="Banca Mediolanum",
            account_type="Conto Deposito",
            currency="EUR",
            iban="IT12Z0306234210000001122334",
            initial_balance=25000.0,
            notes="Fondo di emergenza e liquidità remunerata a tasso fisso garantito."
        )

        for acc in [acc_fineco, acc_intesa, acc_degiro, acc_deposito]:
            self.save_account(acc)

        # 2. Holdings (Investment Portfolio)
        holdings = [
            # Fineco Holdings
            Holding(
                id="h_swda",
                account_id="acc_fineco",
                symbol="SWDA.MI",
                name="iShares Core MSCI World UCITS ETF",
                asset_class="ETF / Fondi (ETFs & Funds)",
                sector="Azionario Globale Diversificato",
                geography="Globale",
                quantity=450.0,
                average_buy_price=82.40,
                current_price=104.85,
                annual_dividend_yield=1.45,
                notes="Core holding a replica fisica ad accumulazione."
            ),
            Holding(
                id="h_eimi",
                account_id="acc_fineco",
                symbol="EIMI.MI",
                name="iShares Core MSCI EM IMI UCITS ETF",
                asset_class="ETF / Fondi (ETFs & Funds)",
                sector="Azionario Mercati Emergenti",
                geography="Emergenti",
                quantity=320.0,
                average_buy_price=27.50,
                current_price=31.90,
                annual_dividend_yield=2.10,
                notes="Esposizione paesi emergenti (Asia, America Latina)."
            ),
            Holding(
                id="h_btp2037",
                account_id="acc_fineco",
                symbol="IT0005436693",
                name="BTP 4.00% Scadenza 2037 (Repubblica Italiana)",
                asset_class="Obbligazionario (Bonds / Fixed Income)",
                sector="Titoli di Stato Sovrani",
                geography="Italia",
                quantity=200.0,
                average_buy_price=98.20,
                current_price=102.65,
                annual_dividend_yield=4.00,
                duration=9.8,
                notes="Cedola semestrale fissa del 4% annuo."
            ),
            Holding(
                id="h_gold",
                account_id="acc_fineco",
                symbol="SGLD.L",
                name="Invesco Physical Gold ETC",
                asset_class="Materie Prime & Oro (Commodities & Gold)",
                sector="Metalli Preziosi",
                geography="Globale",
                quantity=75.0,
                average_buy_price=178.50,
                current_price=225.40,
                annual_dividend_yield=0.0,
                notes="Copertura inflazione e bene rifugio."
            ),
            Holding(
                id="h_xeon",
                account_id="acc_fineco",
                symbol="XEON.DE",
                name="Xtrackers II EUR Overnight Rate Swap UCITS ETF",
                asset_class="Liquidità & Monetario (Cash & Money Market)",
                sector="Monetario Euro / €STR",
                geography="Europa",
                quantity=110.0,
                average_buy_price=138.20,
                current_price=143.10,
                annual_dividend_yield=3.25,
                notes="Remunerazione della liquidità a tasso interbancario BCE."
            ),

            # Degiro Holdings
            Holding(
                id="h_aapl",
                account_id="acc_degiro",
                symbol="AAPL",
                name="Apple Inc. Common Stock",
                asset_class="Azionario (Equities)",
                sector="Tecnologia (Consumer Electronics)",
                geography="Stati Uniti",
                quantity=65.0,
                average_buy_price=168.00,
                current_price=232.50,
                annual_dividend_yield=0.55,
                notes="Leader ecosistema hardware, software e servizi."
            ),
            Holding(
                id="h_msft",
                account_id="acc_degiro",
                symbol="MSFT",
                name="Microsoft Corporation",
                asset_class="Azionario (Equities)",
                sector="Tecnologia (Cloud & Enterprise AI)",
                geography="Stati Uniti",
                quantity=40.0,
                average_buy_price=330.00,
                current_price=448.20,
                annual_dividend_yield=0.75,
                notes="Esposizione primaria su Cloud Azure e Generative AI."
            ),
            Holding(
                id="h_asml",
                account_id="acc_degiro",
                symbol="ASML.AS",
                name="ASML Holding NV",
                asset_class="Azionario (Equities)",
                sector="Semiconduttori & Litografia EUV",
                geography="Europa",
                quantity=18.0,
                average_buy_price=640.00,
                current_price=820.00,
                annual_dividend_yield=0.90,
                notes="Monopolio mondiale macchinari litografia estrema ultravioletta."
            ),
            Holding(
                id="h_btc",
                account_id="acc_degiro",
                symbol="BTC",
                name="21Shares Bitcoin Core ETP",
                asset_class="Criptovalute (Crypto)",
                sector="Digital Assets",
                geography="Globale",
                quantity=250.0,
                average_buy_price=38.50,
                current_price=68.90,
                annual_dividend_yield=0.0,
                notes="Quota satellite asimmetrica ad alto potenziale."
            )
        ]
        self.save_holdings(holdings)

        # 3. Realistic Transactions over past 12 months
        base_date = date.today()
        transactions: List[Transaction] = []

        # Monthly salaries into Intesa Sanpaolo
        for m in range(12, 0, -1):
            d = base_date - timedelta(days=m * 30 - 27)
            transactions.append(Transaction(
                id=f"tx_sal_{m}",
                account_id="acc_intesa",
                date=d.isoformat(),
                value_date=d.isoformat(),
                type="Entrata (Inflow)",
                category="Stipendio / Reddito",
                amount=3650.0,
                currency="EUR",
                description=f"Accredito Emolumenti e Stipendio Mese {d.strftime('%B %Y')}",
                notes="Accredito mensile automatico da datore di lavoro."
            ))

            # Monthly living expenses
            d_exp1 = base_date - timedelta(days=m * 30 - 15)
            transactions.append(Transaction(
                id=f"tx_rent_{m}",
                account_id="acc_intesa",
                date=d_exp1.isoformat(),
                type="Uscita (Outflow)",
                category="Spese Fisse / Utenze",
                amount=-1150.0,
                currency="EUR",
                description="Canone di Locazione & Spese Condominiali",
                notes="Pagamento bonifico affitto abitazione."
            ))

            # Monthly utility / credit card
            d_exp2 = base_date - timedelta(days=m * 30 - 10)
            transactions.append(Transaction(
                id=f"tx_card_{m}",
                account_id="acc_intesa",
                date=d_exp2.isoformat(),
                type="Uscita (Outflow)",
                category="Spese Fisse / Utenze",
                amount=-720.40,
                currency="EUR",
                description="Addebito Carta di Credito (Spese varie, trasporti, ristorazione)",
                notes="Estratto conto carta di credito."
            ))

            # Monthly PAC Transfer from Intesa to Fineco (PAC ETF)
            d_pac = base_date - timedelta(days=m * 30 - 5)
            transactions.append(Transaction(
                id=f"tx_pac_out_{m}",
                account_id="acc_intesa",
                date=d_pac.isoformat(),
                type="Giroconto Interno (Transfer)",
                category="Bonifico / Giroconto",
                amount=-1200.0,
                currency="EUR",
                description="Giroconto versamento periodico PAC investimenti su Fineco",
                notes="Piano di Accumulo Capitale periodico."
            ))
            transactions.append(Transaction(
                id=f"tx_pac_in_{m}",
                account_id="acc_fineco",
                date=d_pac.isoformat(),
                type="Entrata (Inflow)",
                category="Bonifico / Giroconto",
                amount=1200.0,
                currency="EUR",
                description="Ricezione bonifico periodico da Intesa Sanpaolo per PAC",
                notes="Provvista liquida per acquisti azionari ed ETF."
            ))

            # ETF Purchases on Fineco
            d_buy = base_date - timedelta(days=m * 30 - 3)
            transactions.append(Transaction(
                id=f"tx_buy_swda_{m}",
                account_id="acc_fineco",
                date=d_buy.isoformat(),
                type="Acquisto Titoli (Buy)",
                category="Investimento Capitale",
                amount=-950.0,
                currency="EUR",
                description="Acquisto automatico Replay SWDA.MI iShares MSCI World",
                asset_symbol="SWDA.MI",
                quantity=10.0,
                unit_price=95.0,
                fees=2.95,
                notes="Esecuzione piano Replay mensile senza commissioni di custodia."
            ))

        # Semi-annual BTP coupon payments (Cedole)
        d_coup1 = base_date - timedelta(days=180)
        d_coup2 = base_date - timedelta(days=10)
        transactions.append(Transaction(
            id="tx_coup_1",
            account_id="acc_fineco",
            date=d_coup1.isoformat(),
            type="Dividendo / Cedola (Income)",
            category="Cedole Obbligazionarie",
            amount=350.0,
            currency="EUR",
            description="Accredito Cedola Semestrale BTP 4% 2037 (Netto ritenuta 12.5%)",
            asset_symbol="IT0005436693",
            notes="Cedola semestrale su nominale 20.000€ tassata ad aliquota agevolata."
        ))
        transactions.append(Transaction(
            id="tx_coup_2",
            account_id="acc_fineco",
            date=d_coup2.isoformat(),
            type="Dividendo / Cedola (Income)",
            category="Cedole Obbligazionarie",
            amount=350.0,
            currency="EUR",
            description="Accredito Cedola Semestrale BTP 4% 2037 (Netto ritenuta 12.5%)",
            asset_symbol="IT0005436693",
            notes="Cedola semestrale ordinaria."
        ))

        # Dividends from Apple & Microsoft on Degiro
        transactions.append(Transaction(
            id="tx_div_aapl",
            account_id="acc_degiro",
            date=(base_date - timedelta(days=45)).isoformat(),
            type="Dividendo / Cedola (Income)",
            category="Dividendi Azionari",
            amount=68.50,
            currency="EUR",
            description="Dividendo Apple Inc. (Q3 Cash Dividend net of withholding tax)",
            asset_symbol="AAPL",
            fees=1.20,
            notes="Dividendo trimestrale netto accreditato su Degiro."
        ))
        transactions.append(Transaction(
            id="tx_div_msft",
            account_id="acc_degiro",
            date=(base_date - timedelta(days=70)).isoformat(),
            type="Dividendo / Cedola (Income)",
            category="Dividendi Azionari",
            amount=75.20,
            currency="EUR",
            description="Dividendo Microsoft Corp. (Quarterly Cash Dividend)",
            asset_symbol="MSFT",
            fees=1.20,
            notes="Dividendo trimestrale."
        ))

        # Interest paid by Banca Mediolanum Conto Deposito
        transactions.append(Transaction(
            id="tx_int_depo",
            account_id="acc_deposito",
            date=(base_date - timedelta(days=15)).isoformat(),
            type="Interessi Attivi (Interest)",
            category="Interessi Bancari",
            amount=625.0,
            currency="EUR",
            description="Liquidazione trimestrale interessi attivi lordi 3.50% p.a.",
            fees=162.50,  # 26% tax
            notes="Interessi netti accreditati su conto deposito vincolato."
        ))

        # Save all transactions
        self.save_transactions(transactions)


# Singleton database instance
db = Database()
