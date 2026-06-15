# apps/api/src/services/style_presets.py
from dataclasses import dataclass

@dataclass(frozen=True)
class StylePreset:
    name: str
    palette: list[str]
    style: str
    vibe: str

PRESETS: dict[str, StylePreset] = {
    "tech_editorial": StylePreset(
        name="tech_editorial",
        palette=["#1a1a1a", "#f4f1ec", "#c9a47a", "#3d3d3d"],
        style=("soft editorial tech aesthetic, Substack meets Linear docs, "
               "muted earth tones with a single warm accent, generous whitespace, "
               "monochromatic composition, clean geometry"),
        vibe="considered, quiet authority, magazine spread",
    ),
    "health_warm": StylePreset(
        name="health_warm",
        palette=["#e8dcc4", "#c4a484", "#7a8471", "#3a3530"],
        style=("soft wellness editorial, Kinfolk meets Goop, "
               "warm cream backgrounds with botanical line-drawing motifs, "
               "muted sage and terracotta accents, airy typography"),
        vibe="calm, restorative, hand-crafted",
    ),
    "finance_paper": StylePreset(
        name="finance_paper",
        palette=["#f5f1e8", "#1f2937", "#92400e", "#6b7280"],
        style=("editorial finance, Bloomberg Pursuits meets The Economist, "
               "cream paper aesthetic with charcoal type, single accent of burnt sienna, "
               "subtle data-line motif in background"),
        vibe="trustworthy, considered, premium without luxury",
    ),
    "education_warm": StylePreset(
        name="education_warm",
        palette=["#fdf6e3", "#268bd2", "#cb4b16", "#586e75"],
        style=("academic editorial, Are.na meets Kinfolk, "
               "warm cream paper with confident serif type suggested, "
               "single bold accent color per composition, scholarly warmth"),
        vibe="curious, inviting, intellectually generous",
    ),
    "marketing_bold": StylePreset(
        name="marketing_bold",
        palette=["#0a0a0a", "#fef3c7", "#ec4899", "#fafafa"],
        style=("bold creative agency aesthetic, Apple keynote meets modern Dribbble, "
               "high contrast with single warm focal, negative space dominant, "
               "editorial confidence, single pop color"),
        vibe="confident, energetic, premium without ornament",
    ),
    "general_soft": StylePreset(
        name="general_soft",
        palette=["#f5f1e8", "#2d2d2d", "#a8754e", "#888888"],
        style=("soft editorial generalist, Substack meets Pinterest moodboard, "
               "neutral cream and charcoal with one warm accent, quiet and considered"),
        vibe="balanced, versatile, quietly professional",
    ),
}

def get_preset(name: str) -> StylePreset:
    return PRESETS.get(name, PRESETS["general_soft"])
