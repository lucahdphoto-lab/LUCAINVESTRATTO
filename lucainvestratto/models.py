"""
Domain models for LUCAINVESTRATTO.
Includes BankAccount, Transaction, Holding, and RiskMetrics dataclasses with serialization support.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, Dict, Any
import uuid

@dataclass
class BankAccount:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    bank_name: str = ""
    account_type: str = "Conto Corrente"
    currency: str = "EUR"
    iban: str = ""
    initial_balance: float = 0.0
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BankAccount":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    account_id: str = ""
    date: str = field(default_factory=lambda: date.today().isoformat())
    value_date: Optional[str] = None
    type: str = "Uscita (Outflow)"
    category: str = "Altro"
    amount: float = 0.0  # Positive = credit/inflow, Negative = debit/outflow
    currency: str = "EUR"
    description: str = ""
    asset_symbol: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    fees: Optional[float] = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Holding:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    account_id: str = ""
    symbol: str = ""  # Ticker or ISIN
    name: str = ""
    asset_class: str = "Azionario (Equities)"
    sector: str = "Generale"
    geography: str = "Globale"
    currency: str = "EUR"
    quantity: float = 0.0
    average_buy_price: float = 0.0  # PMC (Prezzo Medio di Carico)
    current_price: float = 0.0      # Current market price
    annual_dividend_yield: float = 0.0  # e.g. 2.5 for 2.5%
    duration: float = 0.0          # For bonds
    notes: str = ""

    @property
    def total_cost(self) -> float:
        return self.quantity * self.average_buy_price

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pl(self) -> float:
        return self.market_value - self.total_cost

    @property
    def unrealized_pl_pct(self) -> float:
        if self.total_cost > 0:
            return ((self.market_value - self.total_cost) / self.total_cost) * 100.0
        return 0.0

    @property
    def expected_annual_income(self) -> float:
        return self.market_value * (self.annual_dividend_yield / 100.0)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_cost"] = self.total_cost
        d["market_value"] = self.market_value
        d["unrealized_pl"] = self.unrealized_pl
        d["unrealized_pl_pct"] = self.unrealized_pl_pct
        d["expected_annual_income"] = self.expected_annual_income
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Holding":
        clean = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**clean)


@dataclass
class RiskMetrics:
    total_invested: float = 0.0
    total_market_value: float = 0.0
    total_unrealized_pl: float = 0.0
    total_unrealized_pl_pct: float = 0.0
    expected_annual_income: float = 0.0
    portfolio_dividend_yield: float = 0.0
    
    # Professional metrics (FactSet / Investing.com)
    cagr: float = 0.0                  # Annualized return
    cumulative_return: float = 0.0     # Total cumulative return %
    volatility_annualized: float = 0.0 # Annualized standard deviation %
    sharpe_ratio: float = 0.0          # (Return - R_f) / Volatility
    sortino_ratio: float = 0.0         # (Return - R_f) / Downside Deviation
    max_drawdown: float = 0.0          # Max peak-to-trough decline %
    calmar_ratio: float = 0.0          # CAGR / Max Drawdown
    var_95_annual: float = 0.0         # Value at Risk 95% annual %
    var_99_annual: float = 0.0         # Value at Risk 99% annual %
    cvar_95_annual: float = 0.0        # Conditional VaR (Expected Shortfall) %
    beta: float = 1.0                  # Beta relative to chosen benchmark
    alpha_jensen: float = 0.0          # Jensen's Alpha %
    r_squared: float = 0.0             # Coefficient of determination R²
    tracking_error: float = 0.0        # Tracking error vs benchmark %
    information_ratio: float = 0.0     # Alpha / Tracking error
    risk_free_rate: float = 0.03       # 3% standard BCE rate
    benchmark_name: str = "MSCI World"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    account_id: str = "all"
    snapshot_date: str = field(default_factory=lambda: date.today().isoformat())
    total_wealth: float = 0.0
    liquid_cash: float = 0.0
    invested_amount: float = 0.0
    allocations_json: str = "[]"  # JSON list of dicts: [{"asset_class": "...", "amount": 1000.0, "weight_pct": 20.0}]
    image_filename: str = ""
    image_base64: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_allocations(self) -> list:
        import json
        try:
            return json.loads(self.allocations_json) if self.allocations_json else []
        except Exception:
            return []

    def set_allocations(self, alloc_list: list) -> None:
        import json
        self.allocations_json = json.dumps(alloc_list, ensure_ascii=False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioSnapshot":
        clean = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**clean)
