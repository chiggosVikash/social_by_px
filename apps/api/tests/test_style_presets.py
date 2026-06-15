# apps/api/tests/test_style_presets.py
import pytest
from services.style_presets import get_preset, PRESETS

def test_get_preset_returns_valid_tech_editorial():
    preset = get_preset("tech_editorial")
    assert preset.name == "tech_editorial"
    assert len(preset.palette) == 4
    assert "#1a1a1a" in preset.palette
    assert "Substack" in preset.style
    assert "Linear" in preset.style

def test_get_preset_unknown_returns_default():
    preset = get_preset("unknown_preset")
    assert preset.name == "general_soft"
    assert preset.vibe == "balanced, versatile, quietly professional"

def test_all_presets_have_valid_palette():
    for preset in PRESETS.values():
        assert len(preset.palette) >= 3
        assert all(color.startswith("#") and len(color) == 7 for color in preset.palette)
