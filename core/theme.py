"""Nautilus OS - Design System
This module contains the core theme configuration for the Nautilus OS design system."""

#=========================================================================
# Colors
#=========================================================================

COLORS = {
    # Backgrounds (deep navy)
    "bg_light":   "#0F1E2E",
    "bg_mid":     "#152A3E",
    "bg_dark":    "#0A1628",

    # Teal accents
    "teal":       "#0E7C94",
    "teal_light": "#17A5BC",
    "teal_dim":   "#0A5F72",

    # Ice/sky accents
    "ice":        "#90C8D8",
    "ice_light":  "#B8E0EC",
    "ice_dim":    "#6CAEBE",

    # Coral (warm accent)
    "coral":      "#FF6F61",
    "coral_dim":  "#FF8E80",
    "coral_deep": "#E55B50",

    # Text (cool-tinted)
    "text":       "#C8DAE4",
    "text_dark":  "#E8F0F4",
    "text_muted": "#6882A0",

    # Status
    "success":    "#3DC98A",
    "warning":    "#FFB74D",
    "error":      "#FF5252",

    # Surfaces
    "hover":      "#1A3048",
    "pressed":    "#0D1A2A",
    "selected":   "#1A5068",

    # Borders
    "border":       "#1E3A52",
    "border_light": "#2A4A60",
    "border_dark":  "#14283A",

    # Legacy aliases (used by Surfline vault)
    "wood":       "#0A5F72",
    "wood_light": "#17A5BC",
    "wood_dark":  "#0A1628",

    # Gamification
    "gold":        "#FFD700",
    "gold_dim":    "#B8960F",
    "xp_blue":     "#4FC3F7",

    # Cybersec status
    "scan_green":  "#00E676",
    "alert_red":   "#FF1744",
    "stealth":     "#7C4DFF",
    "warning_alt": "#FF9100",

    # Arcade
    "arcade_pink": "#FF4081",
    "arcade_cyan": "#00E5FF",
}

#=========================================================================
# FONTS
#=========================================================================

FONTS = {
    "ui": "Segoe UI",
    "mono": "JetBrains Mono",
    "size_xs": 10,
    "size_sm": 12,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 18,
    "size_xxl": 20,
    "size_title": 24,
}

#=========================================================================
# Border Radius
#=========================================================================

RADIUS_SM = "8px"
RADIUS_MD = "12px"
RADIUS_LG = "16px"