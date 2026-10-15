"""
Settings and user preferences manager for LUCAINVESTRATTO.
Handles persistent color themes, custom color pickers, button and window gradients,
custom external background images, transparency controls (glassmorphism),
and notification thresholds.
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "settings.json")


def hex_to_rgba(hex_code: str, opacity: float = 1.0) -> str:
    """Converts a hex color (#RRGGBB or #RGB) to an rgba(r, g, b, a) CSS string."""
    try:
        hex_code = hex_code.strip().lstrip("#")
        if len(hex_code) == 3:
            hex_code = "".join([c * 2 for c in hex_code])
        if len(hex_code) == 6:
            r = int(hex_code[0:2], 16)
            g = int(hex_code[2:4], 16)
            b = int(hex_code[4:6], 16)
            return f"rgba({r}, {g}, {b}, {max(0.0, min(1.0, opacity)):.3f})"
    except Exception:
        pass
    return f"rgba(255, 255, 255, {opacity:.3f})"


THEME_PRESETS: Dict[str, Dict[str, str]] = {
    "factset_navy": {
        "name": "FactSet Dark Navy (Predefinito)",
        "primary_color": "#2563EB",
        "header_bg_start": "#0F172A",
        "header_bg_end": "#1E293B",
        "card_border": "#CBD5E1",
        "accent_color": "#38BDF8",
        "positive_color": "#16A34A",
        "negative_color": "#DC2626",
        "btn_gradient_start": "#2563EB",
        "btn_gradient_end": "#1E40AF",
        "card_gradient_start": "#FFFFFF",
        "card_gradient_end": "#F8FAFC"
    },
    "bloomberg_terminal": {
        "name": "Bloomberg Amber & Black Terminal",
        "primary_color": "#F59E0B",
        "header_bg_start": "#09090B",
        "header_bg_end": "#18181B",
        "card_border": "#3F3F46",
        "accent_color": "#FBBF24",
        "positive_color": "#22C55E",
        "negative_color": "#EF4444",
        "btn_gradient_start": "#F59E0B",
        "btn_gradient_end": "#B45309",
        "card_gradient_start": "#18181B",
        "card_gradient_end": "#27272A"
    },
    "emerald_wealth": {
        "name": "Private Wealth Emerald Green",
        "primary_color": "#059669",
        "header_bg_start": "#064E3B",
        "header_bg_end": "#022C22",
        "card_border": "#A7F3D0",
        "accent_color": "#10B981",
        "positive_color": "#10B981",
        "negative_color": "#E11D48",
        "btn_gradient_start": "#059669",
        "btn_gradient_end": "#047857",
        "card_gradient_start": "#FFFFFF",
        "card_gradient_end": "#ECFDF5"
    },
    "cyber_violet": {
        "name": "Cyber Violet & Deep Indigo",
        "primary_color": "#8B5CF6",
        "header_bg_start": "#1E1B4B",
        "header_bg_end": "#312E81",
        "card_border": "#C4B5FD",
        "accent_color": "#C084FC",
        "positive_color": "#34D399",
        "negative_color": "#F43F5E",
        "btn_gradient_start": "#8B5CF6",
        "btn_gradient_end": "#6D28D9",
        "card_gradient_start": "#1F172A",
        "card_gradient_end": "#2E1065"
    },
    "classic_slate": {
        "name": "Classic Minimalist Slate",
        "primary_color": "#475569",
        "header_bg_start": "#1E293B",
        "header_bg_end": "#334155",
        "card_border": "#94A3B8",
        "accent_color": "#64748B",
        "positive_color": "#15803D",
        "negative_color": "#B91C1C",
        "btn_gradient_start": "#475569",
        "btn_gradient_end": "#334155",
        "card_gradient_start": "#FFFFFF",
        "card_gradient_end": "#F1F5F9"
    }
}

# Curated High-Definition Background Wallpaper Presets
PRESET_BACKGROUND_IMAGES: Dict[str, str] = {
    "Nessuna (Sfondo Colore Base)": "",
    "Modern Financial Architecture (High-Rise)": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=2000&q=80",
    "Trading Floor & Financial Displays": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=2000&q=80",
    "Dark Minimalist Geometric Grid": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=2000&q=80",
    "Abstract Deep Blue Cyber Mesh": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=2000&q=80",
    "Global Wealth & Luxury Minimal Gold": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=2000&q=80"
}


@dataclass
class AppSettings:
    # 1. Theme and Base Colors
    theme_preset: str = "factset_navy"
    custom_primary_color: str = "#2563EB"
    custom_accent_color: str = "#38BDF8"
    use_custom_colors: bool = False

    # 2. Gradients (Degradanti) for Buttons and Windows
    gradient_buttons_enabled: bool = True
    gradient_btn_start: str = "#2563EB"
    gradient_btn_end: str = "#1E40AF"

    gradient_cards_enabled: bool = True
    gradient_card_start: str = "#FFFFFF"
    gradient_card_end: str = "#F8FAFC"

    # 3. Background Images (Sfondo esterno)
    background_type: str = "default"  # "default", "image_preset", "image_url", "image_upload"
    background_preset_key: str = "Nessuna (Sfondo Colore Base)"
    background_image_url: str = ""
    background_image_base64: str = ""
    background_overlay_opacity: float = 0.82  # Dark overlay transparency (0.0 to 1.0)

    # 4. Transparency & Glassmorphism (Trasparenze)
    card_opacity_pct: float = 90.0           # Card & window opacity (20% to 100%)
    card_blur_px: int = 12                   # Backdrop blur in pixels (0 to 30)
    sidebar_opacity_pct: float = 95.0        # Sidebar opacity

    # 5. Notifications & Alert thresholds
    alert_max_drawdown_enabled: bool = True
    alert_max_drawdown_pct: float = 8.0
    
    alert_min_cash_enabled: bool = True
    alert_min_cash_amount: float = 5000.0
    
    alert_max_weight_enabled: bool = True
    alert_max_weight_pct: float = 25.0
    
    alert_high_expense_enabled: bool = True
    alert_high_expense_amount: float = 1200.0

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
            preset["btn_gradient_start"] = self.gradient_btn_start
            preset["btn_gradient_end"] = self.gradient_btn_end
            preset["card_gradient_start"] = self.gradient_card_start
            preset["card_gradient_end"] = self.gradient_card_end
        return preset

    def get_effective_background_image(self) -> str:
        if self.background_type == "image_preset":
            return PRESET_BACKGROUND_IMAGES.get(self.background_preset_key, "")
        elif self.background_type == "image_url":
            return self.background_image_url.strip()
        elif self.background_type == "image_upload":
            return self.background_image_base64.strip()
        return ""


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
