# Creator-Voiced Image Prompts — Design Spec

**Date:** 2026-06-15
**Status:** Draft
**Author:** Brainstorming session with Vikash Roy
**Related specs:**
- [Tiered Slide Image Generation](./2026-06-15-tiered-slide-image-generation-design.md) — the cost-tier system
- [GPT Image 1 Mini Strategy](./2026-06-15-gpt-image-1-mini-strategy-design.md) — alternative model

## Problem

The current slide image generation pipeline produces carousels that look like **AI art with text slapped on**, not like the work of a Gen Z content creator. Three root causes:

1. **Generic, marketing-fluff prompts.** `_GENERATION_SYSTEM_PROMPT` instructs the LLM to "include style, mood, colors, composition" — words the LLM has no concrete referent for. DALL-E receives "abstract background, minimalist, modern, beautiful" and produces what every other AI carousel tool produces.
2. **No visual identity per project.** Every article in every project gets the same flavorless "abstract" background. A health brand and a finance brand look identical.
3. **DALL-E is asked to render the full slide, OR a background, never a designed layout.** Current `DalleSlideImageStrategy` asks for "abstract background for a social media slide" with no awareness that text will be overlaid in a specific zone. PIL compensates with a 45% black overlay to ensure readability — but that overlay is a band-aid for a missing composition.

**Goals:**
- Visuals should look like a content creator directed them, not a marketing AI generated them.
- Visual identity must be per-project, anchored in Gen Z "soft editorial" vocabulary.
- Cost stays in the 1–2 DALL-E calls per carousel range (per the tiered strategy).
- Text rendering remains 100% accurate (PIL with Inter font).
- Quality ceiling: a designer reviewing the output should not be able to tell it was generated.

**Non-goals:**
- Switching to a different LLM for text generation.
- Animated carousels or video output.
- Letting the user upload reference images for fine-tuning.

## Solution: Three Layered Changes

1. **Project-templated style presets** — each Project picks one preset at creation time. The preset locks the palette and aesthetic vocabulary.
2. **Creator-voiced image briefs** — `_GENERATION_SYSTEM_PROMPT` instructs the LLM to write the `image_prompt` as a structured creative-direction brief, with concrete reference vocabulary.
3. **Text-accurate hybrid generation** — DALL-E composes a **designed-for-text background** with intentional negative space in a chosen `text_zone`. PIL drops the real text into that zone using Inter.

The result: DALL-E is no longer a typesetter or a generic "abstract" generator. It is a **compositional director** that designs where the text will live. PIL is no longer compensating for missing composition — it is honoring it.

## Architecture

### Component Map

```
Project (style_preset="tech_editorial")
  └── style_preset → services/style_presets.py → { palette, style, vibe }
       │
       ▼
content_generation_agent (agents/nodes.py)
  └── emits 5 SlideData, each with:
       - hook_type, text_content, caption, emoji
       - image_prompt (structured brief, see template below)
       - text_zone (where the overlay text will land)
       - visual_type (minimalist | thematic | generative)
       │
       ▼
slide_verification_agent
  └── confirms all fields are valid
       │
       ▼
DalleSlideImageStrategy (services/image.py)
  └── composes final DALL-E prompt = slide.image_prompt
       + preset.style + preset.palette + text_zone instruction
  └── calls DALL-E for `generative` slides only
       │
       ▼
composite_text_on_background (services/renderer.py)
  └── accepts background_bytes (NEW) or background_url
  └── applies lighter overlay (24% black) only when text_zone demands it
  └── renders emoji, text_content, caption, counter via PIL
  └── honors text_zone for text positioning
       │
       ▼
ImageOptimizationService → upload_file (R2)
```

### 1. Style Preset Module (NEW)

New file: `apps/api/src/services/style_presets.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StylePreset:
    name: str
    palette: list[str]   # 3-4 hex colors
    style: str           # creator-vocabulary style description
    vibe: str            # 1-2 word mood summary

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
```

### 2. Slide Data Model Update

In `apps/api/src/agents/state.py`:

```python
from typing import Literal

TextZone = Literal[
    "center-bottom third",  # default for most slides
    "full center",          # for hero/hook slides with short text
    "lower-left aligned",   # for editorial asymmetric layouts
    "right half clear",     # for split-composition layouts
]

VisualType = Literal["minimalist", "thematic", "generative"]

class SlideData(TypedDict):
    hook_type: str
    text_content: str
    caption: str
    image_prompt: str
    emoji: str
    text_zone: TextZone
    visual_type: VisualType
```

The SQLAlchemy `Slide` model in `models/core.py` needs matching columns. Alembic migration adds both, nullable, with defaults so old rows don't break the migration:

```python
# In models/core.py Slide class
text_zone: Mapped[Optional[str]] = mapped_column(String(32), default="center-bottom third")
visual_type: Mapped[Optional[str]] = mapped_column(String(16), default="minimalist")
```

### 3. Updated System Prompts

In `apps/api/src/agents/nodes.py`, the `image_prompt` field instructions change from:

```python
"image_prompt": "A detailed prompt for generating a matching visual. Include style, mood, colors, composition."
```

to:

```python
"""The image_prompt is a CREATIVE DIRECTION for a social media slide layout. 
Describe the BACKGROUND COMPOSITION as a designer would brief an art director.

Use this template (one line per field):
  ROLE: <hook | context | insight | proof | cta> — what this slide does in the carousel
  PALETTE: <pick 2-3 colors from the project's preset: {palette}>
  FOCAL: <the main visual element, e.g., "abstract chrome sphere", "folded paper texture", "botanical line drawing">
  TEXT_ZONE: <where the overlay text will land. Pick ONE:
             - "center-bottom third" (default, most slides)
             - "full center" (for short hero text)
             - "lower-left aligned" (editorial layouts)
             - "right half clear" (split-composition)>
  COMPOSITION: <what's in the text zone — "negative space", "soft gradient into background", "subtle paper texture">
  REFERENCE: <1-2 real-world references from "Substack, Are.na, Kinfolk, 
             Pinterest editorial, magazine spread, Linear docs, Goop wellness, 
             Bloomberg Pursuits, Apple keynote minimal">
  MOOD: <1-2 words: "quiet authority", "warm urgency", "editorial confidence">
  AVOID: <from the negative list: faces, stock photos, neon, rainbow gradients, 
         "AI-looking" glossy renders, busy collages, AND CRITICALLY: 
         no text, letters, words, or typographic marks in the image>

The image is a SLIDE BACKGROUND. The real text will be overlaid later in a 
consistent brand font. The image must support, not compete with, that text.
Composition: 1080x1080 square.
"""
```

And the refinement prompt (`_REFINEMENT_SYSTEM_PROMPT`) gains the same image_prompt guidance plus a hard rule:

```
The image_prompt must NEVER direct DALL-E to render text. The text is overlaid 
separately. DALL-E's job is to design a composed background with a clear empty 
text zone in the specified text_zone position.
```

The fallback slide dicts (currently lines 292–296) need updating to include `text_zone` and `visual_type` defaults:

```python
# BEFORE
{"hook_type": "bold_claim", "text_content": article['title'], "caption": ..., "image_prompt": f"...", "emoji": "🔥"},

# AFTER
{"hook_type": "bold_claim", "text_content": article['title'], "caption": ..., 
 "image_prompt": f"ROLE: hook\nPALETTE: {industry_warm_accent}\nFOCAL: bold typography metaphor\n"
                 f"TEXT_ZONE: full center\nCOMPOSITION: negative space\n"
                 f"REFERENCE: Substack hero, Apple keynote minimal\nMOOD: quiet authority",
 "emoji": "🔥", "text_zone": "full center", "visual_type": "generative"},
```

### 4. Updated DALL-E Strategy

In `apps/api/src/services/image.py`, `DalleSlideImageStrategy.generate_and_save`:

```python
async def generate_and_save(
    self, db, slide, article, project, idx, total
) -> Optional[str]:
    import uuid
    from services.style_presets import get_preset
    from services.renderer import composite_text_on_background
    from services.storage import upload_file
    
    preset = get_preset(project.style_preset)
    
    # Compose the final DALL-E prompt from three sources:
    #   1. The LLM's creative-direction brief (slide.image_prompt)
    #   2. The project's locked style (preset.style, preset.palette)
    #   3. The text-zone constraint (DALL-E must leave that area empty)
    dalle_prompt = (
        f"{slide.image_prompt}\n\n"
        f"FORMAT: 1080x1080 square, social media carousel slide background.\n"
        f"STYLE LOCK: {preset.style}\n"
        f"COLOR PALETTE (use ONLY these, with at most 20% accent): "
        f"{', '.join(preset.palette)}\n"
        f"LEAVE A CLEAR {slide.text_zone.upper()} zone empty for text overlay.\n"
        f"DO NOT include any text, letters, words, or typography in the image.\n"
        f"NO faces, no people, no stock photos, no neon gradients, "
        f"no glossy AI-render look, no busy collages."
    )
    
    image_service = get_image_generation_service()
    raw_bytes = await image_service.generate(dalle_prompt)
    if not raw_bytes:
        return None
    
    # Pass the bytes directly to the renderer (no URL round-trip)
    rendered_bytes = await composite_text_on_background(
        text_content=slide.text_content or "",
        emoji=slide.emoji,
        caption=slide.caption,
        background_url=None,
        background_bytes=raw_bytes,   # NEW
        text_zone=slide.text_zone,    # NEW
        slide_index=idx,
        total_slides=total,
    )
    
    optimized = ImageOptimizationService.optimize_for_web(rendered_bytes, quality=85)
    file_name = f"slides/article_{article.id}_slide_{idx}_{uuid.uuid4().hex[:8]}.webp"
    return await upload_file(optimized, file_name, content_type="image/webp")
```

### 5. Renderer Update

In `apps/api/src/services/renderer.py`, `composite_text_on_background` gains two new parameters:

```python
async def composite_text_on_background(
    text_content: str,
    emoji: Optional[str],
    caption: Optional[str],
    background_url: Optional[str] = None,
    background_bytes: Optional[bytes] = None,   # NEW
    text_zone: str = "center-bottom third",     # NEW
    slide_index: int = 0,
    total_slides: int = 5,
) -> bytes:
    """Renders slide text onto a background (URL or bytes)."""
    
    if not background_url and not background_bytes:
        raise ValueError("Either background_url or background_bytes is required.")
    
    def _render():
        # Load background
        if background_bytes:
            img = Image.open(io.BytesIO(background_bytes))
        else:
            # ... existing URL loading logic (R2, localhost, http) ...
            pass
        
        img = img.convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
        
        # Lighter overlay than current 45% — DALL-E already designed the 
        # text zone to be empty, so we trust the composition.
        # Only apply the overlay if the text_zone is "center-bottom third" 
        # or "lower-left aligned" (positions where DALL-E cooperation is reliable).
        # For "full center" hero slides, skip the overlay entirely.
        if text_zone in ("center-bottom third", "lower-left aligned"):
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 60))  # ~24% opacity
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        
        # ... existing font resolution and counter logic ...
        
        # Position based on text_zone
        if text_zone == "full center":
            start_y = 540 - 60  # vertically centered
        elif text_zone == "lower-left aligned":
            start_y = 720
            # use left-aligned text variant
        else:  # "center-bottom third" (default) and "right half clear"
            start_y = 700  # current behavior, centered horizontally
        
        # Draw emoji, text, caption using existing helpers
        # ...
        
        # ... save and return WebP ...
```

The `draw_centered_text` helper needs a `left-aligned` mode for `lower-left aligned` slides. Implementation: pass an `align` parameter that switches between centered and left-aligned text placement.

### 6. Slide Verification

In `_GEN`-style verification in `agents/nodes.py`, the existing rule:

```python
if 10 < len(text) < 300 and slide.get("hook_type") and slide.get("image_prompt"):
```

extends to:

```python
VALID_TEXT_ZONES = {"center-bottom third", "full center", "lower-left aligned", "right half clear"}
VALID_VISUAL_TYPES = {"minimalist", "thematic", "generative"}

if (10 < len(text) < 300 
    and slide.get("hook_type") 
    and slide.get("image_prompt")
    and slide.get("text_zone") in VALID_TEXT_ZONES
    and slide.get("visual_type") in VALID_VISUAL_TYPES):
```

Missing or invalid `text_zone` or `visual_type` causes the slide to fail validation.

### 7. Worker Wiring

In `apps/api/src/workers/tasks.py`, the strategy dispatch becomes per-slide. The existing per-article loop in `_render_slides_for_article` iterates slides and calls `_generate_slide_image(article, slide, project)`. The strategy resolution inside that function changes from:

```python
# BEFORE
strategy = SlideImageStrategyFactory.get_strategy(project)
```

to:

```python
# AFTER
strategy = SlideImageStrategyFactory.get_strategy(slide.visual_type)
```

Per the [tiered strategy spec](./2026-06-15-tiered-slide-image-generation-design.md), the factory is keyed by `visual_type`, not by project. The visual_type tag is decided by the LLM during `content_generation_agent` based on slide role:

| Slide | Default visual_type | Default text_zone |
|---|---|---|
| 1 (Hook) | `generative` | `full center` |
| 2 (Context) | `thematic` | `center-bottom third` |
| 3 (Insight) | `generative` if concept demands, else `minimalist` | `center-bottom third` |
| 4 (Proof) | `minimalist` | `center-bottom third` |
| 5 (CTA) | `minimalist` | `lower-left aligned` |

This is the 1–2 generative slides per carousel target from the tiered strategy spec.

### 8. API Surface

The `SlideOut` schema in `apps/api/src/api/approvals.py` grows:

```python
class SlideOut(BaseModel):
    id: int
    hook_type: str
    text_content: str
    caption: Optional[str]
    image_prompt: str
    emoji: Optional[str]
    image_url: Optional[str]
    text_zone: Optional[str]      # NEW
    visual_type: Optional[str]    # NEW
```

The endpoint signatures are unchanged. Frontend can read `visual_type` to show a "Generative" / "Template" / "Gradient" badge per slide (cost transparency), and `text_zone` to position the edit preview correctly.

### 9. Project Creation Flow

The Project creation form gains one dropdown: **Visual Style Preset**, with the 6 presets from `style_presets.py` and a "General Soft" default. The choice is stored as `Project.style_preset: str` (nullable for backward compat — defaults to `general_soft` in code).

API change in `apps/api/src/api/projects.py` and `schemas/project.py`:

```python
# In ProjectIn
style_preset: Optional[str] = "general_soft"

# In ProjectOut
style_preset: Optional[str]
```

## Data Flow

1. **User creates a project** and picks a style preset (e.g., `tech_editorial`).
2. **Project is saved** with `style_preset` in DB.
3. **Workflow runs.** `content_generation_agent` receives `state["industry"]` and the resolved preset's palette. The system prompt embeds the palette in the brief template.
4. **LLM generates 5 slides.** Each slide's `image_prompt` follows the structured brief format (ROLE, PALETTE, FOCAL, TEXT_ZONE, COMPOSITION, REFERENCE, MOOD, AVOID). Each slide's `visual_type` and `text_zone` are decided by the LLM based on slide role.
5. **`slide_verification_agent`** validates all fields. Slides with invalid `text_zone` or `visual_type` are rejected.
6. **Repository saves** slides to DB (new columns).
7. **Image worker** iterates slides. For each slide:
   - Look up strategy via `SlideImageStrategyFactory.get_strategy(slide.visual_type)`.
   - For `generative`: call DALL-E with the composed prompt (brief + preset + text_zone).
   - For `thematic` / `minimalist`: render via PIL with preset palette.
8. **`DalleSlideImageStrategy`** passes the raw bytes + `text_zone` to `composite_text_on_background`.
9. **PIL** renders emoji, text, caption, counter into the chosen zone. Light overlay (24%) only when the zone demands it.
10. **WebP optimized and uploaded** to R2.
11. **Approval UI** shows the slide with a small badge indicating the strategy used.

## Error Handling

- **LLM returns invalid `text_zone` or `visual_type`:** verification rejects the slide, agent re-runs with corrected prompt. After 2 retries, fallback slides (with hardcoded valid values) are used.
- **DALL-E fills the text zone anyway:** for `center-bottom third` and `lower-left aligned` zones, the 24% overlay provides a safety net for readability. For `full center` and `right half clear` zones (no overlay), this is a known risk — the user hits Regenerate. Acceptable degradation for v1. v2 enhancement: add a "regenerate just the text zone" mask flow.
- **DALL-E hallucinates text in the image anyway:** the AVOID instructions and explicit "DO NOT include any text" usually work. If text appears, the overlay can be raised to 60% for that slide only (add as a recovery path).
- **Theme library lookup fails (unknown style_preset):** falls back to `general_soft`. Logged at `INFO`, never raises.
- **R2 upload fails:** bubbles up to the worker, article goes to `failed`. **No change.**

## Testing

Extend `apps/api/tests/test_image_strategies.py`:

- `get_preset("tech_editorial")` returns the correct palette, style, and vibe.
- `get_preset("unknown")` returns `general_soft` (no exception).
- `DalleSlideImageStrategy.generate_and_save` composes the expected prompt from a stubbed LLM brief + preset. Use a mocked `get_image_generation_service` and assert on the composed prompt string.
- `composite_text_on_background` with `background_bytes` produces a valid 1080×1080 WebP.
- `composite_text_on_background` with each `text_zone` value places text in the correct region (snapshot test for one known input per zone).

Extend `apps/api/tests/test_agents.py`:

- `content_generation_agent` produces slides with valid `text_zone` and `visual_type` for happy path and fallback.
- `slide_verification_agent` rejects slides with missing or invalid `text_zone`.
- `slide_verification_agent` rejects slides with missing or invalid `visual_type`.

Extend `apps/api/tests/test_renderer.py`:

- The text-positioning logic for each `text_zone` produces stable output (snapshot tests).

## Rollout

This is a single integrated change with multiple touch points. Implementation order:

1. **Add `style_presets.py`** with all 6 presets and unit tests.
2. **Alembic migration** adding `style_preset` to `Project` and `text_zone` + `visual_type` to `Slide` (all nullable, with safe defaults).
3. **Update SlideData TypedDict** with new fields.
4. **Update `_GENERATION_SYSTEM_PROMPT` and `_REFINEMENT_SYSTEM_PROMPT`** with the structured brief template.
5. **Update fallback slides** in the `except` branch of `content_generation_agent`.
6. **Update `DalleSlideImageStrategy`** to compose the new prompt and pass bytes to renderer.
7. **Update `composite_text_on_background`** to accept `background_bytes` and `text_zone`.
8. **Update `SlideImageStrategyFactory`** to dispatch on `visual_type` (per the tiered strategy spec).
9. **Update `slide_verification_agent`** with new validation rules.
10. **Update `SlideOut` schema** in the API.
11. **Update Project creation UI** with the style preset dropdown.
12. **Tests** at each layer.

Backward compatibility: existing projects in the DB have `style_preset = NULL` → resolved to `general_soft` in code. Existing slides have `text_zone` and `visual_type` NULL → factory raises on `visual_type=NULL` (intentional — old slides need re-generation to pick up the new fields, per the tiered strategy spec's migration story).

## Open Risks

- **DALL-E compliance with "leave a clear zone empty" is unreliable.** Empirically, ~20% of generations will partially fill the text zone with busy elements. **Mitigation:** the 24% overlay on default zones still ensures readability. **Future:** add a "regenerate just the text zone" mask flow as a v2 feature.
- **Reference vocabulary can age.** "Substack meets Linear docs" is current as of mid-2026. If the Gen Z aesthetic shifts, presets need refreshing. **Mitigation:** presets are a single file with clear semantic naming. Refresh cycle: quarterly review.
- **LLM may overuse `generative` for visual_type if the cost-awareness prompt isn't strong enough.** **Mitigation:** the system prompt explicitly maps slide roles to default visual_types (Hook/Insight = generative, others = cheap). The fallback hardcodes the right values. Add telemetry on `visual_type` distribution post-launch.
- **Style preset selection adds friction to project creation.** **Mitigation:** "General Soft" is the default. Users can ignore the dropdown entirely and get a sensible result. The dropdown is for users who care about brand consistency.
- **Adding `background_bytes` to the renderer changes the public-ish API.** The `composite_text_on_background` function is called from multiple places — `DalleSlideImageStrategy`, `TemplateCompositingSlideImageStrategy`, and the existing per-slide worker loop. All call sites must be updated together. **Mitigation:** the parameter is optional with a default of `None`, so old call sites that pass `background_url` continue to work unchanged.

## Out of Scope (Future)

- Reference image upload for fine-tuning.
- Animated or video carousel output.
- A/B testing of style presets with real performance data.
- Per-slide regenerate with text-zone masking.
- Multilingual aesthetic vocabulary (the current references are English/American-skewed).
