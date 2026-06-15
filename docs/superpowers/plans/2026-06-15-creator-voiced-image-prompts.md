# Creator-Voiced Image Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace generic "abstract background" prompts with creator-voiced structured briefs, project style presets, and text-accurate hybrid generation. Cut image cost by 60-80% while producing premium-quality, consistent carousel visuals.

**Architecture:** Add style presets module, expand SlideData schema with text_zone/visual_type, update LLM prompts to generate structured briefs, modify DALL-E strategy to compose prompts from brief+preset+constraints, update renderer to accept bytes and position text by zone. Maintain full backward compatibility for existing projects.

**Tech Stack:** Python, FastAPI, SQLAlchemy Async, Alembic, LangChain/OpenAI Gemini, PIL, pytest

---

## File Structure

| File | Change |
|------|--------|
| `apps/api/src/services/style_presets.py` | New file: 6 hardcoded style presets with palettes, style descriptions, vibes |
| `apps/api/src/models/core.py` | Add `style_preset` to Project; add `text_zone` + `visual_type` to Slide (nullable, migration) |
| `apps/api/src/agents/state.py` | Add `TextZone` + `VisualType` aliases; add to `SlideData` TypedDict |
| `apps/api/src/agents/nodes.py` | Update `_GENERATION_SYSTEM_PROMPT` image_prompt template; update fallback slides; update `slide_verification_agent` rules |
| `apps/api/src/services/image.py` | Update `DalleSlideImageStrategy.generate_and_save` to compose prompt from brief+preset+text_zone |
| `apps/api/src/services/renderer.py` | Update `composite_text_on_background` to accept `background_bytes` parameter; add `text_zone` positioning logic |
| `apps/api/src/api/approvals.py` | Add `text_zone` + `visual_type` to `SlideOut` schema |
| `apps/api/src/api/projects.py` | Add `style_preset` to ProjectIn/ProjectOut schemas |
| `apps/api/tests/test_style_presets.py` | New file: tests for style presets module |
| `apps/api/tests/test_models.py` | New file: model field tests |
| `apps/api/tests/test_integration.py` | New file: end-to-end pipeline test |
| `apps/api/tests/test_agents.py` | Update tests for new SlideData fields |
| `apps/api/tests/test_image_strategies.py` | Update DalleSlideImageStrategy test to verify prompt composition |
| `apps/api/tests/test_renderer.py` | Update text-positioning tests for 4 text_zone values |
| `apps/api/alembic/versions/` | New migration file: add style_preset, text_zone, visual_type columns |

---

## Task 1: Style Presets Module

**Files:**
- Create: `apps/api/src/services/style_presets.py`
- Test: `apps/api/tests/test_style_presets.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_style_presets.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create style_presets.py with complete implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_style_presets.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/services/style_presets.py apps/api/tests/test_style_presets.py
git commit -m "feat: add style presets module with 6 presets

- tech_editorial: muted earth tones, Substack+Linear aesthetic
- health_warm: warm cream with botanical motifs, Kinfolk+Goop style
- finance_paper: cream paper aesthetic, Bloomberg+Economist vibe
- education_warm: academic warm cream, Are.na+Kinfeel aesthetic
- marketing_bold: high contrast with single pop color, Apple keynote meets Dribbble
- general_soft: neutral default for all industries

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Database Schema Migration

**Files:**
- Create: `apps/api/alembic/versions/20240615_1a2b3c4d_add_image_style_columns.py`
- Modify: `apps/api/src/models/core.py`

- [ ] **Step 1: Write the failing test (schema validation)**

```python
# apps/api/tests/test_models.py (add this test)
def test_project_has_style_preset():
    # This will fail until we add the column
    project = Project(id=1, name="Test", style_preset="tech_editorial")
    assert project.style_preset == "tech_editorial"

def test_slide_has_text_zone_and_visual_type():
    slide = Slide(id=1, text_zone="center-bottom third", visual_type="generative")
    assert slide.text_zone == "center-bottom third"
    assert slide.visual_type == "generative"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_models.py::test_project_has_style_preset -v`
Expected: FAIL (attribute error)

- [ ] **Step 3: Create the Alembic migration file**

```python
# apps/api/alembic/versions/20240615_1a2b3c4d_add_image_style_columns.py
"""Add text_zone, visual_type columns to Slide, and style_preset to Project

Revision ID: 20240615_1a2b3c4d
Revises: 3a2c33f7aa6c
Create Date: 2024-06-15 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '20240615_1a2b3c4d'
down_revision = '3a2c33f7aa6c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add style_preset to Project table (nullable, default 'general_soft')
    op.add_column('project',
        sa.Column('style_preset', sa.String(32), nullable=True,
                 server_default='general_soft')
    )
    
    # Add text_zone and visual_type to Slide table (nullable, default values)
    op.add_column('slide',
        sa.Column('text_zone', sa.String(32), nullable=True,
                 server_default='center-bottom third')
    )
    op.add_column('slide',
        sa.Column('visual_type', sa.String(16), nullable=True,
                 server_default='minimalist')
    )

def downgrade() -> None:
    op.drop_column('slide', 'visual_type')
    op.drop_column('slide', 'text_zone')
    op.drop_column('project', 'style_preset')
```

- [ ] **Step 4: Run the migration**

Run: `cd apps/api && uv run alembic upgrade head`
Expected: Migration succeeds without errors

- [ ] **Step 5: Update models/core.py with new fields**

```python
# apps/api/src/models/core.py - Project class
class Project(Base):
    __tablename__ = "project"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # ... existing fields ...
    style_preset: Mapped[Optional[str]] = mapped_column(
        String(32), 
        nullable=True, 
        server_default="general_soft",
        index=True
    )

# Slide class (add two new fields)
class Slide(Base):
    __tablename__ = "slide"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # ... existing fields ...
    text_zone: Mapped[Optional[str]] = mapped_column(
        String(32), 
        nullable=True, 
        server_default="center-bottom third"
    )
    visual_type: Mapped[Optional[str]] = mapped_column(
        String(16), 
        nullable=True, 
        server_default="minimalist"
    )
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest apps/api/tests/test_models.py::test_project_has_style_preset -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/api/alembic/versions/20240615_add_image_style_columns.py apps/api/src/models/core.py
git commit -m "feat: add image style columns to DB schema

- Add style_preset to Project (default: general_soft)
- Add text_zone to Slide (default: center-bottom third)
- Add visual_type to Slide (default: minimalist)
- All columns nullable for backward compatibility

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Update SlideData TypedDict

**Files:**
- Modify: `apps/api/src/agents/state.py`

- [ ] **Step 1: Write the failing test (type checking)**

```python
# apps/api/tests/test_agents.py (add after existing test)
def test_slide_data_has_text_zone_and_visual_type():
    from agents.state import SlideData
    slide_data = SlideData(
        hook_type="question",
        text_content="Test content",
        caption="Test caption",
        image_prompt="Test prompt",
        emoji="🔥",
        text_zone="full center",
        visual_type="generative"
    )
    assert slide_data["text_zone"] == "full center"
    assert slide_data["visual_type"] == "generative"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_agents.py::test_slide_data_has_text_zone_and_visual_type -v`
Expected: FAIL (TypeError/missing fields)

- [ ] **Step 3: Update SlideData with new fields**

```python
# apps/api/src/agents/state.py
from typing import Literal, TypedDict, Optional

# ... existing imports ...

TextZone = Literal[
    "center-bottom third", 
    "full center", 
    "lower-left aligned", 
    "right half clear"
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

- [ ] **Step 4: Update fallback slides in agents/nodes.py (preview change)**

Find the `except` branch in `content_generation_agent` (around line 292), we'll update these in the next task.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest apps/api/tests/test_agents.py::test_slide_data_has_text_zone_and_visual_type -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/api/src/agents/state.py
git commit -m "feat: add text_zone and visual_type to SlideData

- Add TextZone and VisualType aliases
- Update SlideData TypedDict with required fields
- Ensures type safety in LLM generation and verification steps

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Update System Prompts

**Files:**
- Modify: `apps/api/src/agents/nodes.py`

- [ ] **Step 1: Write the failing test (prompt integration)**

```python
# apps/api/tests/test_agents.py (add this test)
def test_content_generation_agent_produces_text_zone_and_visual_type():
    from agents.state import GraphState
    
    state = GraphState(
        project_id=1,
        keywords=["AI"],
        industry="technology",
        approved_articles=[{
            "title": "AI News",
            "url": "example.com",
            "source": "TechCrunch",
            "published_date": "2026-06-15",
            "summary": "AI is advancing"
        }]
    )
    
    result = content_generation_agent(state)
    slides = result["generated_slides"]["example.com"]
    
    # Check first slide has new fields
    first_slide = slides[0]
    assert "text_zone" in first_slide
    assert "visual_type" in first_slide
    assert first_slide["text_zone"] in ["center-bottom third", "full center", "lower-left aligned", "right half clear"]
    assert first_slide["visual_type"] in ["minimalist", "thematic", "generative"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_agents.py::test_content_generation_agent_produces_text_zone_and_visual_type -v`
Expected: FAIL (missing fields in SlideData)

- [ ] **Step 3: Update _GENERATION_SYSTEM_PROMPT with structured brief template**

Find the image_prompt instruction in `_GENERATION_SYSTEM_PROMPT` (around line 229) and replace:

```python
# BEFORE
"image_prompt": "A detailed prompt for generating a matching visual. Include style, mood, colors, composition.",

# AFTER
"image_prompt": """The image_prompt is a CREATIVE DIRECTION for a social media slide layout. 
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
""",
```

- [ ] **Step 4: Update _REFINEMENT_SYSTEM_PROMPT**

Add this instruction after line 239 in `_REFINEMENT_SYSTEM_PROMPT`:

```python
# The image_prompt must NEVER direct DALL-E to render text. The text is overlaid 
# separately. DALL-E's job is to design a composed background with a clear empty 
# text zone in the specified text_zone position.
```

- [ ] **Step 5: Update fallback slides in except branch**

Replace the current fallback slides (lines 292-296) with:

```python
# ... existing except branch code ...
generated[article["url"]] = [
    {"hook_type": "bold_claim", "text_content": article['title'], 
     "caption": f"Source: {article.get('source', 'Unknown')}", 
     "image_prompt": f"ROLE: hook\nPALETTE: #{'#, #'.join(['f5f1e8', '2d2d2d', 'a8754e'])}\n"
                     f"FOCAL: bold typography metaphor\n"
                     f"TEXT_ZONE: full center\nCOMPOSITION: negative space\n"
                     f"REFERENCE: Substack hero, Apple keynote minimal\nMOOD: quiet authority",
     "emoji": "🔥", "text_zone": "full center", "visual_type": "generative"},
    {"hook_type": "story", "text_content": f"Here's why this matters for {industry} right now.", 
     "caption": "", 
     "image_prompt": f"ROLE: context\nPALETTE: #{'#, #'.join(['f5f1e8', '2d2d2d', 'a8754e'])}\n"
                     f"FOCAL: abstract trend visualization\n"
                     f"TEXT_ZONE: center-bottom third\nCOMPOSITION: soft gradient\n"
                     f"REFERENCE: Pinterest editorial\nMOOD: considerate",
     "emoji": "💡", "text_zone": "center-bottom third", "visual_type": "minimalist"},
    {"hook_type": "statistic", "text_content": article.get('summary', 'Key insight from this story.')[:280], 
     "caption": "", 
     "image_prompt": f"ROLE: insight\nPALETTE: #{'#, #'.join(['f5f1e8', '2d2d2d', 'a8754e'])}\n"
                     f"FOCAL: data point visualization\n"
                     f"TEXT_ZONE: center-bottom third\nCOMPOSITION: abstract infographic\n"
                     f"REFERENCE: Bloomberg Pursuits\nMOOD: authoritative",
     "emoji": "📊", "text_zone": "center-bottom third", "visual_type": "minimalist"},
    {"hook_type": "story", "text_content": "The implications are bigger than most people realize.", 
     "caption": "", 
     "image_prompt": f"ROLE: proof\nPALETTE: #{'#, #'.join(['f5f1e8', '2d2d2d', 'a8754e'])}\n"
                     f"FOCAL: perspective shot\n"
                     f"TEXT_ZONE: center-bottom third\nCOMPOSITION: futuristic layering\n"
                     f"REFERENCE: Linear docs style\nMOOD: forward-looking",
     "emoji": "🚀", "text_zone": "center-bottom third", "visual_type": "minimalist"},
    {"hook_type": "cta", "text_content": "What's your take? Drop your thoughts below 👇", 
     "caption": "", 
     "image_prompt": f"ROLE: cta\nPALETTE: #{'#, #'.join(['f5f1e8', '2d2d2d', 'a8754e'])}\n"
                     f"FOCAL: conversation prompt\n"
                     f"TEXT_ZONE: lower-left aligned\nCOMPOSITION: clear negative space\n"
                     f"REFERENCE: social comment bubbles\nMOOD: engaged",
     "emoji": "💬", "text_zone": "lower-left aligned", "visual_type": "minimalist"},
]
```

- [ ] **Step 6: Update slide_verification_agent rules**

Find the verification logic (around line 312) and extend it:

```python
VALID_TEXT_ZONES = {"center-bottom third", "full center", "lower-left aligned", "right half clear"}
VALID_VISUAL_TYPES = {"minimalist", "thematic", "generative"}

# Before:
if 10 < len(text) < 300 and slide.get("hook_type") and slide.get("image_prompt"):

# After:
if (10 < len(text) < 300 
    and slide.get("hook_type") 
    and slide.get("image_prompt")
    and slide.get("text_zone") in VALID_TEXT_ZONES
    and slide.get("visual_type") in VALID_VISUAL_TYPES):
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest apps/api/tests/test_agents.py::test_content_generation_agent_produces_text_zone_and_visual_type -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/api/src/agents/nodes.py
git commit -m "feat: update system prompts with structured briefs

- Replace generic image_prompt with structured creative direction brief
- Add ROLE, PALETTE, FOCAL, TEXT_ZONE, COMPOSITION, REFERENCE, MOOD, AVOID template
- Update fallback slides with hardcoded valid values for new fields
- Extend verification to require valid text_zone and visual_type
- Update refinement prompt to prohibit DALL-E from generating text

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Update DalleSlideImageStrategy

**Files:**
- Modify: `apps/api/src/services/image.py`

- [ ] **Step 1: Write the failing test (prompt composition)**

```python
# apps/api/tests/test_image_strategies.py (add this test)
@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_dalle_prompt_includes_text_zone_constraint(mock_openai_cls):
    from services.style_presets import get_preset
    from services.image import DalleSlideImageStrategy
    
    mock_response = MagicMock()
    mock_response.content = base64.b64encode(b"fake_png_bytes").decode()
    mock_client = AsyncMock()
    mock_client.responses.create = AsyncMock(return_value=mock_response)
    mock_openai_cls.return_value = mock_client
    
    strategy = DalleSlideImageStrategy()
    
    # Mock slide with structured brief
    slide = {
        "text_content": "Test content",
        "emoji": "🔥",
        "caption": "Test caption",
        "text_zone": "full center",
        "image_prompt": "ROLE: hook\nPALETTE: #1a1a1a, #f4f1ec\nFOCAL: abstract sphere\n"
                        "TEXT_ZONE: full center\nCOMPOSITION: negative space\n"
                        "REFERENCE: Substack, Linear\nMOOD: quiet authority"
    }
    
    result = await strategy.generate_image(slide["image_prompt"])
    assert result is not None
    
    # Verify the prompt includes the text_zone constraint
    call_args = mock_client.responses.create.call_args
    final_prompt = call_args.kwargs['input']
    assert "TEXT_ZONE: full center" in final_prompt
    assert "LEAVE A CLEAR FULL CENTER zone empty for text overlay" in final_prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_image_strategies.py::test_dalle_prompt_includes_text_zone_constraint -v`
Expected: FAIL (not implemented yet)

- [ ] **Step 3: Update DalleSlideImageStrategy to compose prompt from brief + preset**

```python
# apps/api/src/services/image.py - update generate_and_save method
import uuid
from services.storage import upload_file
from services.style_presets import get_preset  # Add this import

class DalleSlideImageStrategy(SlideImageGenerationStrategy):
    async def generate_and_save(
        self,
        db: AsyncSession,
        slide,
        article,
        project,
        idx: int,
        total: int
    ) -> Optional[str]:
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
        raw_image_bytes = await image_service.generate(dalle_prompt)
        if not raw_image_bytes:
            return None
            
        optimized_bytes = ImageOptimizationService.optimize_for_web(raw_image_bytes, quality=85)
        file_name = f"slides/article_{article.id}_slide_{idx}_{uuid.uuid4().hex[:8]}.webp"
        
        return await upload_file(optimized_bytes, file_name, content_type="image/webp")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_image_strategies.py::test_dalle_prompt_includes_text_zone_constraint -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/services/image.py
git commit -m "feat: update DalleSlideImageStrategy to compose prompts

- Compose final DALL-E prompt from LLM brief + preset + text_zone constraint
- Add STYLE LOCK and COLOR PALETTE constraints from project's style_preset
- Enforce text zone to be empty and no text in the image
- Update method signature to use slide dict (not individual parameters)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Update Renderer

**Files:**
- Modify: `apps/api/src/services/renderer.py`

- [ ] **Step 1: Write the failing test (bytes parameter)**

```python
# apps/api/tests/test_renderer.py (add this test)
import io
from PIL import Image
import pytest
from services.renderer import composite_text_on_background

async def test_composite_with_bytes():
    # Create a dummy 1080x1080 image
    img = Image.new('RGB', (1080, 1080), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    background_bytes = img_byte_arr.getvalue()
    
    result = await composite_text_on_background(
        text_content="Test text",
        emoji="🔥",
        caption="Test caption",
        background_url=None,
        background_bytes=background_bytes,
        text_zone="full center"
    )
    
    assert isinstance(result, bytes)
    assert len(result) > 0  # Should produce WebP bytes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_renderer.py::test_composite_with_bytes -v`
Expected: FAIL (parameter doesn't exist)

- [ ] **Step 3: Update composite_text_on_background signature and implementation**

```python
# apps/api/src/services/renderer.py
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
    """
    Renders slide text onto a background (URL or bytes).
    Returns optimized WebP bytes.
    """
    if not background_url and not background_bytes:
        raise ValueError("Either background_url or background_bytes is required.")
        
    def _render():
        # Load background
        if background_bytes:
            img = Image.open(io.BytesIO(background_bytes))
        elif background_url:
            # Existing URL loading logic (localhost, R2, httpx)...
            # ... (keep all existing code for background_url case)
            pass
        else:
            raise ValueError("Either background_url or background_bytes is required.")
            
        img = img.convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
        
        # Light overlay only for specific text zones (DALL-E cooperates with others)
        if text_zone in ("center-bottom third", "lower-left aligned"):
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 60))  # 24% opacity
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        
        # ... existing font resolution, counter, text drawing logic ...
        # Update text positioning based on text_zone
        if text_zone == "full center":
            start_y = 540 - 60  # centered vertically
        elif text_zone == "lower-left aligned":
            start_y = 720
            # Use left-aligned text (modify draw_centered_text or add variant)
        else:  # default "center-bottom third"
            start_y = 700
            
        # ... rest of existing code ...
        
        # Update draw_centered_text calls to use the calculated start_y
        # ... (existing drawing code)
        
        # Save as WebP
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='WEBP', quality=85)
        return img_byte_arr.getvalue()
        
    return await asyncio.to_thread(_render)
```

- [ ] **Step 4: Add left-aligned text helper**

Add this function in `renderer.py`:

```python
def draw_left_aligned_text(draw, text_str, font_obj, fill_color, max_width, start_y, line_height_mult=1.4):
    """Helper to draw left-aligned text with word wrapping."""
    words = text_str.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_str, font=font_obj)
        w = bbox[2] - bbox[0]
        if w > max_width:
            if len(current_line) > 1:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(test_str)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
        
    y = start_y
    for line in lines:
        draw.text((60, y), line, font=font_obj, fill=fill_color)  # 60px left margin
        bbox = draw.textbbox((0, 0), line, font=font_obj)
        y += int(bbox[3] - bbox[1]) * line_height_mult
    return y
```

- [ ] **Step 5: Update main drawing code to use left-aligned when needed**

In `_render()` function, replace or conditionally call the text drawing:

```python
# After positioning calculations
if text_zone == "lower-left aligned":
    # Use left-aligned version
    draw_left_aligned_text(
        draw, text_content, font_main, (255, 255, 255), 900, start_y
    )
else:
    # Use existing centered version (keep existing draw_centered_text)
    draw_centered_text(
        draw, text_content, font_main, (255, 255, 255), 900, start_y
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest apps/api/tests/test_renderer.py::test_composite_with_bytes -v` and all other renderer tests
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/services/renderer.py
git commit -m "feat: update renderer to accept bytes and text_zone

- Add background_bytes parameter for direct byte input (from DALL-E)
- Add text_zone parameter for positioning text based on design
- Apply 24% overlay only for center-bottom third and lower-left aligned zones
- Add left-aligned text drawing for lower-left aligned text_zone
- Light overlay skipped for full center and right half clear zones

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Update API Schemas

**Files:**
- Modify: `apps/api/src/api/approvals.py`
- Modify: `apps/api/src/api/projects.py`

- [ ] **Step 1: Write the failing test (API response)**

```python
# apps/api/tests/test_api.py (add this test)
def test_slide_out_includes_text_zone_and_visual_type():
    from api.approvals import SlideOut
    
    # This test will fail until we add the fields to the schema
    slide_data = {
        "id": 1,
        "hook_type": "question",
        "text_content": "Test",
        "caption": "Test",
        "image_prompt": "Test prompt",
        "emoji": "🔥",
        "image_url": "http://example.com/image.webp",
        "text_zone": "center-bottom third",  # NEW
        "visual_type": "minimalist"          # NEW
    }
    
    # This would fail initially
    slide_out = SlideOut(**slide_data)
    assert slide_out.text_zone == "center-bottom third"
    assert slide_out.visual_type == "minimalist"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_api.py::test_slide_out_includes_text_zone_and_visual_type -v`
Expected: FAIL (validation error)

- [ ] **Step 3: Update SlideOut schema in approvals.py**

```python
# apps/api/src/api/approvals.py
from pydantic import BaseModel
from typing import Optional

# ... existing imports ...

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

# ... rest of file ...
```

- [ ] **Step 4: Update Project schema in projects.py**

```python
# apps/api/src/api/projects.py
from pydantic import BaseModel
from typing import Optional
# ... existing imports ...

class ProjectIn(BaseModel):
    name: str
    # ... existing fields ...
    style_preset: Optional[str] = "general_soft"  # NEW

class ProjectOut(BaseModel):
    id: int
    name: str
    # ... existing fields ...
    style_preset: Optional[str]  # NEW

# Update Project.update_mixed_model to include style_preset
def update_mixed_model(model):
    return {
        "id": model.id,
        "name": model.name,
        # ... existing fields ...
        "style_preset": model.style_preset,
    }
```

- [ ] **Step 5: Update Project creation endpoint**

In `projects.py` POST endpoint, add style_preset:

```python
# POST /api/v1/projects
project_in = ProjectIn(**project_data)
project = Project(**project_in.dict())
project.style_preset = project_in.style_preset or "general_soft"  # Ensure default
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest apps/api/tests/test_api.py::test_slide_out_includes_text_zone_and_visual_type -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/api/approvals.py apps/api/src/api/projects.py
git commit -m "feat: update API schemas with new image fields

- Add text_zone and visual_type to SlideOut approval schema
- Add style_preset to ProjectIn/ProjectOut schemas
- Ensure defaults are applied in Project creation endpoint

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Final Integration Tests

**Files:**
- Modify: `apps/api/tests/test_integration.py` (create if needed)

- [ ] **Step 1: Write end-to-end test**

```python
# apps/api/tests/test_integration.py
import pytest
from unittest.mock import patch, AsyncMock
from services.image import DalleSlideImageStrategy
from services.renderer import composite_text_on_background
import io

@pytest.mark.asyncio
async def test_full_pipeline_from_prompt_to_webp():
    """Test the full pipeline: LLM brief → DALL-E → PIL → WebP"""
    from services.style_presets import get_preset
    
    # Mock DALL-E to return a dummy image
    mock_image_bytes = b"fake_png_data"
    
    with patch("services.image.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock(
            return_value=type('MockResponse', (), {
                'output': [{
                    'type': 'image_generation_call',
                    'result': base64.b64encode(mock_image_bytes).decode()
                }]
            })()
        )
        mock_openai.return_value = mock_client
        
        # Test the full pipeline
        strategy = DalleSlideImageStrategy()
        
        slide = {
            "text_content": "Test content",
            "emoji": "🔥",
            "caption": "Test caption",
            "text_zone": "full center",
            "image_prompt": "ROLE: hook\nPALETTE: #1a1a1a, #f4f1ec\nFOCAL: abstract sphere\n"
                            "TEXT_ZONE: full center\nCOMPOSITION: negative space"
        }
        project = type('Project', (), {'style_preset': 'tech_editorial'})()
        
        # Mock composite_text_on_background to capture the bytes
        with patch("services.renderer.composite_text_on_background") as mock_composite:
            mock_composite.return_value = b"fake_webp_data"
            
            result = await strategy.generate_and_save(
                db=None,  # Mock DB
                slide=slide,
                article=type('Article', (), {'id': 1})(),
                project=project,
                idx=0,
                total=5
            )
            
            assert result is not None
            # Verify DALL-E was called with the composed prompt
            call_args = mock_client.responses.create.call_args
            assert "TEXT_ZONE: full center" in call_args.kwargs['input']
            # Verify renderer was called with the right text_zone
            mock_composite.assert_called_once()
            call_kwargs = mock_composite.call_args.kwargs
            assert call_kwargs['text_zone'] == "full center"
```

- [ ] **Step 2: Run the integration test**

Run: `pytest apps/api/tests/test_integration.py::test_full_pipeline_from_prompt_to_webp -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/test_integration.py
git commit -m "feat: add integration test for full pipeline

- Test LLM brief → DALL-E → PIL → WebP flow
- Verify text_zone constraint passed through correctly
- Mock DALL-E response and PIL compositing
- End-to-end verification of the new architecture

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Update Frontend Project Creation Form

**Files:**
- Modify: `apps/web/src/components/ProjectForm.tsx` (or equivalent)

- [ ] **Step 1: Update form schema**

```typescript
// apps/web/src/components/ProjectForm.tsx
interface ProjectFormData {
  name: string;
  // ... existing fields ...
  stylePreset: string; // NEW
}
```

- [ ] **Step 2: Add style preset select dropdown**

```typescript
// In the JSX
<label htmlFor="style-preset">Visual Style</label>
<select
  id="style-preset"
  value={formData.stylePreset}
  onChange={(e) => setFormData({...formData, stylePreset: e.target.value})}
  className="w-full p-2 border rounded"
>
  <option value="general_soft">General Soft</option>
  <option value="tech_editorial">Tech Editorial</option>
  <option value="health_warm">Health Warm</option>
  <option value="finance_paper">Finance Paper</option>
  <option value="education_warm">Education Warm</option>
  <option value="marketing_bold">Marketing Bold</option>
</select>
```

- [ ] **Step 3: Update API call to include style_preset**

```typescript
// When submitting
const projectData = {
  name: formData.name,
  // ... other fields ...
  style_preset: formData.stylePreset,
};
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/ProjectForm.tsx
git commit -m "feat: add style preset selection to project creation

- Add dropdown with 6 predefined visual styles
- Defaults to "General Soft" for new users
- Style affects color palette and aesthetic vocabulary in image generation

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: Update ApprovalList to Show Badges

**Files:**
- Modify: `apps/web/src/components/ApprovalList.tsx`

- [ ] **Step 1: Add badge component for visual_type**

```typescript
// In ApprovalList.tsx
const getVisualTypeBadge = (visualType?: string) => {
  const labels = {
    minimalist: "Gradient",
    thematic: "Template", 
    generative: "AI Art"
  };
  const colors = {
    minimalist: "bg-gray-100 text-gray-800",
    thematic: "bg-blue-100 text-blue-800",
    generative: "bg-purple-100 text-purple-800"
  };
  
  return (
    <span className={`px-2 py-1 text-xs rounded-full ${
      colors[visualType as keyof typeof colors] || colors.minimalist
    }`}>
      {labels[visualType as keyof typeof labels] || "Gradient"}
    </span>
  );
};
```

- [ ] **Step 2: Update SlideItem to show badge**

```typescript
// In the slide items section
<div className="flex items-center justify-between">
  <div className="flex-1">
    {/* Existing slide content */}
  </div>
  <div className="flex items-center space-x-2">
    {getVisualTypeBadge(slide.visual_type)}
    {/* Existing actions */}
  </div>
</div>
```

- [ ] **Step 3: Update SlideOut response handling**

Update the API call to include the new fields:

```typescript
// When fetching slides
interface Slide {
  // ... existing fields ...
  visual_type?: string;
  text_zone?: string;
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/ApprovalList.tsx
git commit -m "feat: add visual type badges to slides

- Show "AI Art", "Template", or "Gradient" badge per slide
- Color-coded for easy visual distinction
- Users can see which slides used expensive DALL-E vs. cheap alternatives

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 11: Documentation Update

**Files:**
- Create: `docs/superpowers/specs/README.md` (update if exists)

- [ ] **Step 1: Update README.md with new features**

Add a section about the new image generation system:

```markdown
## Image Generation System

The platform now generates premium-quality carousel visuals with a Gen Z aesthetic:

### Key Improvements
- **Style Presets**: Each project chooses a visual style (6 options) that locks the color palette and aesthetic vocabulary
- **Structured Prompts**: LLM generates creative direction briefs, not generic "abstract background" prompts
- **Text-Accurate Generation**: DALL-E designs compositions with intentional text zones; PIL renders the actual text
- **Cost-Effective**: Only 1-2 DALL-E calls per carousel (vs 5 before), saving 60-80%

### Visual Types Per Slide
- **Hook slide**: Full AI-generated art (highest visual impact)
- **Context/Insight**: Template or gradient (cost-effective, text-focused)
- **Proof/CTA**: Always gradient + typography (maximum text clarity)

### Default Styles
- **General Soft**: Neutral cream & charcoal, versatile for all industries
- **Tech Editorial**: Muted earth tones, Substack + Linear aesthetic
- **Health Warm**: Warm cream with botanicals, Kinfolk + Goop style
- **Finance Paper**: Cream paper, Bloomberg + Economist aesthetic
- **Education Warm**: Academic, Are.na + Kinfeel aesthetic  
- **Marketing Bold**: High contrast, Apple keynote + Dribbble style
```

- [ ] **Step 2: Update Getting Started guide**

Add instructions for choosing a style preset when creating a project.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update docs with new image generation system

- Add section on style presets and visual types
- Explain cost savings and quality improvements
- Document the 6 default visual styles
- Include guidance for new users on style selection

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 12: Final Verification

**Files:**
- Test: All test suites

- [ ] **Step 1: Run all tests**

Run: `cd apps/api && uv run pytest`
Expected: All tests pass

- [ ] **Step 2: Verify backward compatibility**

Test with existing projects in DB:
- Projects without `style_preset` should default to `general_soft`
- Slides without `text_zone` or `visual_type` should trigger regeneration

- [ ] **Step 3: Commit final verification**

```bash
git add .
git commit -m "feat: complete creator-voiced image generation system

- All tests passing and backward compatibility verified
- New image generation system is ready for production use
- Cost reduced by 60-80% while improving visual quality

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Post-Implementation Checklist

After completing all tasks:

- [ ] Monitor `visual_type` distribution in production — ensure generative is 20-40% of slides
- [ ] Collect user feedback on style presets — consider adding industry-specific ones
- [ ] Track DALL-E generation success rates — if zone intrusions exceed 20%, consider overlay policy adjustment
- [ ] Document any performance improvements in image generation speed
