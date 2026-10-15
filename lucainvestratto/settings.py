"""
Settings and user preferences manager for LUCAINVESTRATTO.
Handles persistent color themes, custom color pickers, and notification thresholds.
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "settings.json")

THEME_PRESETS: Dict[str, Dict[str, str]] = {
    "factset_navy": {
        "name": "FactSet Dark Navy (Predefinito)",
        "primary_color": "#2563EB",
        "header_bg_start": "#0F172A",
        "header_bg_end": "#1E293B",
        "card_border": "#CBD5E1",
        "accent_color": "#38BDF8",
        "positive_color": "#16A34A",
        "negative_color": "#DC2626"
    },
    "bloomberg_terminal": {
        "name": "Bloomberg Amber & Black Terminal",
        "primary_color": "#F59E0B",
        "header_bg_start": "#09090B",
        "header_bg_end": "#18181B",
        "card_border": "#3F3F46",
        "accent_color": "#FBBF24",
        "positive_color": "#22C55E",
        "negative_color": "#EF4444"
    },
    "emerald_wealth": {
        "name": "Private Wealth Emerald Green",
        "primary_color": "#059669",
        "header_bg_start": "#064E3B",
        "header_bg_end": "#022C22",
        "card_border": "#A7F3D0",
        "accent_color": "#10B981",
        "positive_color": "#10B981",
        "negative_color": "#E11D48"
    },
    "cyber_violet": {
        "name": "Cyber Violet & Deep Indigo",
        "primary_color": "#8B5CF6",
        "header_bg_start": "#1E1B4B",
        "header_bg_end": "#312E81",
        "card_border": "#C4B5FD",
        "accent_color": "#C084FC",
        "positive_color": "#34D399",
        "negative_color": "#F43F5E"
    },
    "classic_slate": {
        "name": "Classic Minimalist Slate",
        "primary_color": "#475569",
        "header_bg_start": "#1E293B",
        "header_bg_end": "#334155",
        "card_border": "#94A3B8",
        "accent_color": "#64748B",
        "positive_color": "#15803D",
        "negative_color": "#B91C1C"
    }
}

@dataclass
class AppSettings:
    # Theme configuration
    theme_preset: str = "factset_navy"
    custom_primary_color: str = "#2563EB"
    custom_accent_color: str = "#38BDF8"
    use_custom_colors: bool = False

    # Notifications & Alert thresholds
    alert_max_drawdown_enabled: bool = True
    alert_max_drawdown_pct: float = 8.0     # Notify if portfolio drawdown > 8%
    
    alert_min_cash_enabled: bool = True
    alert_min_cash_amount: float = 5000.0   # Notify if cash < 5,000 EUR
    
    alert_max_weight_enabled: bool = True
    alert_max_weight_pct: float = 25.0      # Notify if single asset > 25% of portfolio
    
    alert_high_expense_enabled: bool = True
    alert_high_expense_amount: float = 1200.0 # Notify on outflows > 1,200 EUR

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        clean = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**clean)

    def get_active_colors(self) -> Dict[str, str]:
        preset = THEME_PRESETS.get(self.theme_preset, THEME_PRESETS["factset_navy"]).copy()
        if self.use_custom_colors:
            preset["primary_color"] = self.custom_primary_color
            preset["accent_color"] = self.custom_accent_color
        return preset


def load_settings() -> AppSettings:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppSettings.from_dict(data)
        except Exception:
            pass
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
