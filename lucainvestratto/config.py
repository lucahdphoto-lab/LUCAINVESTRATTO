"""
Configuration settings for LUCAINVESTRATTO.
Defines constants, standard asset classes, benchmarks, currencies, and default parameters.
"""
from dataclasses import dataclass
from typing import Dict, List

APP_NAME = "LUCAINVESTRATTO"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Piattaforma Professionale di Gestione Multi-Conto & Analisi Finanziaria"

# Default Base Currency
DEFAULT_BASE_CURRENCY = "EUR"

# Standard Supported Currencies
SUPPORTED_CURRENCIES = ["EUR", "USD", "CHF", "GBP", "JPY"]

# Asset Classes recognized by LUCAINVESTRATTO
ASSET_CLASSES: List[str] = [
    "Azionario (Equities)",
    "Obbligazionario (Bonds / Fixed Income)",
    "ETF / Fondi (ETFs & Funds)",
    "Liquidità & Monetario (Cash & Money Market)",
    "Materie Prime & Oro (Commodities & Gold)",
    "Criptovalute (Crypto)",
    "Immobiliare & Alternativi (Real Estate & Alternatives)"
]

# Standard Transaction Types
TRANSACTION_TYPES: List[str] = [
    "Entrata (Inflow)",
    "Uscita (Outflow)",
    "Acquisto Titoli (Buy)",
    "Vendita Titoli (Sell)",
    "Dividendo / Cedola (Income)",
    "Commissioni / Spese (Fees)",
    "Giroconto Interno (Transfer)",
    "Interessi Attivi (Interest)"
]

# Standard Transaction Categories
TRANSACTION_CATEGORIES: List[str] = [
    "Stipendio / Reddito",
    "Dividendi Azionari",
    "Cedole Obbligazionarie",
    "Interessi Bancari",
    "Plusvalenze Realizzate",
    "Investimento Capitale",
    "Commissioni Bancarie / Trading",
    "Imposte & Tasse Finanziarie (Tobin / Capital Gain)",
    "Spese Fisse / Utenze",
    "Bonifico / Giroconto",
    "Altro"
]

# Account Types
ACCOUNT_TYPES: List[str] = [
    "Conto Corrente",
    "Conto Deposito",
    "Dossier Titoli / Brokerage",
    "Portafoglio Cripto",
    "Altro"
]

# Benchmark definitions for professional risk & return comparison
@dataclass
class BenchmarkInfo:
    code: str
    name: str
    asset_type: str
    annual_return: float  # Expected / historical annual return (decimal, e.g. 0.08 for 8%)
    volatility: float     # Annual volatility (decimal, e.g. 0.15 for 15%)

BENCHMARKS: Dict[str, BenchmarkInfo] = {
    "MSCI_WORLD": BenchmarkInfo(
        code="MSCI_WORLD",
        name="MSCI World Index (Net Total Return EUR)",
        asset_type="Azionario Globale",
        annual_return=0.092,
        volatility=0.145
    ),
    "SP500": BenchmarkInfo(
        code="SP500",
        name="S&P 500 (EUR Hedged)",
        asset_type="Azionario USA",
        annual_return=0.105,
        volatility=0.155
    ),
    "FTSE_MIB": BenchmarkInfo(
        code="FTSE_MIB",
        name="FTSE MIB (Italia)",
        asset_type="Azionario Italia",
        annual_return=0.078,
        volatility=0.180
    ),
    "BLOOMBERG_AGG": BenchmarkInfo(
        code="BLOOMBERG_AGG",
        name="Bloomberg Euro-Aggregate Bond Index",
        asset_type="Obbligazionario Euro",
        annual_return=0.035,
        volatility=0.055
    ),
    "EUR_CASH": BenchmarkInfo(
        code="EUR_CASH",
        name="€STR / BCE Depo Rate (Cash Benchmark)",
        asset_type="Monetario Euro",
        annual_return=0.030,
        volatility=0.005
    )
}

# Professional Analysis Default Parameters
DEFAULT_RISK_FREE_RATE = 0.030  # 3.0% annual risk-free rate (BCE reference)
DEFAULT_TRADING_DAYS_PER_YEAR = 252
DEFAULT_CONFIDENCE_LEVEL_VAR = 0.95  # 95% VaR
DEFAULT_CONFIDENCE_LEVEL_VAR_99 = 0.99  # 99% VaR
