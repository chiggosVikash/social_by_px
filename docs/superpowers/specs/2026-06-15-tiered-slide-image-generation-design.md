# Tiered Slide Image Generation — Design Spec

**Date:** 2026-06-15
**Status:** Approved
**Author:** Brainstorming session with Vikash Roy

## Problem

The current slide image generation pipeline calls OpenAI's image generation model (gpt-5.5) for **every single slide** (5 calls per article). At current pricing, this runs $0.30–$0.40 per article. The generated images are typically "abstract minimalist backgrounds" — work that a template or PIL-generated gradient could do at zero cost.

**Goals:**
- Cut image generation cost by 60–70% per article.
- Maintain or improve perceived slide quality.
- Add per-slide flexibility so the AI can pick the cheapest acceptable strategy.

**Non-goals:**
- Switching to a different LLM (we already have a Gemini/Gemma strategy).
- Building a full visual editor for the frontend.
- Adding multi-modal generation pipelines (e.g., animated carousels).

## Solution: Tiered Per-Slide Strategy Pattern

Extend the existing strategy pattern (see [services/image.py](../../apps/api/src/services/image.py)) to a **3-tier ladder**. The LLM tags each slide with a `visual_type` and the factory routes to the cheapest strategy that fits.

| Strategy | Cost | Speed | Visual Source | When to use |
|----------|------|-------|---------------|-------------|
| `ProgrammaticPILStrategy` (new) | FREE | <1s | PIL gradient from theme library | Text-heavy slides — the words are the visual |
| `TemplateCompositingSlideImageStrategy` (existing) | FREE | <1s | Project-uploaded `background_image_url` | Branded look on top of an uploaded template |
| `DalleSlideImageStrategy` (existing) | PAID | ~5s | OpenAI image gen | Fully custom, content-specific visuals |

## Architecture

### Slide Data Model

Add a `visual_type` field to `SlideData` in [agents/state.py](../../apps/api/src/agents/state.py):

```python
from typing import Literal

class SlideData(TypedDict):
    hook_type: str
    text_content: str
    caption: Optional[str]
    image_prompt: str
    emoji: str
    visual_type: Literal["minimalist", "thematic", "generative"]
```

The `Slide` SQLAlchemy model also needs a column. Add `visual_type: Mapped[Optional[str]]` to [models/core.py](../../apps/api/src/models/core.py) (alembic migration required).

### New Strategy: `ProgrammaticPILStrategy`

Lives in [services/image.py](../../apps/api/src/services/image.py) alongside the existing strategies.

- Renders a 1080x1080 PIL image from a **pre-designed theme gradient**.
- Themes are picked from a `ThemeLibrary` keyed by `industry` (`technology`, `health`, `finance`, etc.).
- Reuses the text-overlay logic from `composite_text_on_background`. To avoid duplication, extract a shared `draw_slide_text(img: Image.Image, slide, slide_index: int, total_slides: int) -> None` helper into [services/renderer.py](../../apps/api/src/services/renderer.py). Both `TemplateCompositingSlideImageStrategy` and `ProgrammaticPILStrategy` will call this helper to draw emoji, text, caption, and counter onto an already-prepared background image.
- Uploads the rendered WebP via existing `upload_file()`.

### New Module: Theme Library

New file: [services/themes.py](../../apps/api/src/services/themes.py). Each theme is a small data structure describing a gradient (start color, end color, optional accent) plus an optional decorative SVG/pattern overlay.

Initial themes ship for 5 industries:
- `technology` — cool blue → deep purple
- `health` — mint → soft white
- `finance` — charcoal → navy
- `education` — warm yellow → cream
- `marketing` — coral → magenta

Default theme: a neutral slate gradient used when the industry is unrecognized.

### Updated Strategy Factory

Rewrite the `get_strategy()` dispatch in [services/image.py](../../apps/api/src/services/image.py) to take a per-slide `visual_type` (not just a project-level flag):

```python
class SlideImageStrategyFactory:
    _ROUTES = {
        "minimalist": ProgrammaticPILStrategy,
        "thematic":   TemplateCompositingSlideImageStrategy,
        "generative": DalleSlideImageStrategy,
    }

    @classmethod
    def get_strategy(cls, visual_type: str) -> SlideImageGenerationStrategy:
        impl = cls._ROUTES.get(visual_type)
        if impl is None:
            raise ValueError(f"Unknown visual_type: {visual_type!r}")
        return impl()
```

### LLM Prompt Update

In [agents/nodes.py](../../apps/api/src/agents/nodes.py), update `_GENERATION_SYSTEM_PROMPT` and the fallback to include the new field and a **cost-aware selection guide**:

```
VISUAL TYPE — pick the cheapest option that still serves the slide:
- "minimalist": The text IS the visual. Use for bold claims, stats, CTAs, quotes.
- "thematic": Use a project template as backdrop. Use for industry-specific framing.
- "generative": Only when the slide depends on imagery (e.g., a product or scene).

Aim for a mix: 2–3 minimalist, 1–2 thematic, 0–1 generative per carousel.
```

The fallback slide list in the `except` branch also needs a `visual_type` for each hard-coded slide (use `minimalist` for the safe defaults).

### Slide Verification

In [`slide_verification_agent`](../../apps/api/src/agents/nodes.py), the existing rule `if 10 < len(text) < 300 and slide.get("hook_type") and slide.get("image_prompt")` is extended to also require `slide.get("visual_type") in {"minimalist", "thematic", "generative"}`. Missing or invalid `visual_type` causes the slide to fail validation and the agent to fall back.

### Worker Wiring

In [workers/tasks.py](../../apps/api/src/workers/tasks.py), the loops in `_render_slides_for_article` and `_run_image_generation_async` change from:

```python
strategy = SlideImageStrategyFactory.get_strategy(project)  # one strategy for all
```

to:

```python
strategy = SlideImageStrategyFactory.get_strategy(slide.visual_type)  # per slide
```

The `strategy.generate_and_save(...)` signature is unchanged, so the rest of the loop is untouched.

The branch at [workers/tasks.py:171](../../apps/api/src/workers/tasks.py#L171) that auto-renders after the workflow needs no change: it still iterates all pending articles and calls `_render_slides_for_article`.

### API Surface

[`/api/v1/approvals/{article_id}/generate-images`](../../apps/api/src/api/approvals.py#L196) and the `SlideOut` schema in [api/approvals.py](../../apps/api/src/api/approvals.py) both need `visual_type: Optional[str]` added so the frontend can show a small badge per slide ("AI", "Template", "Gradient"). The endpoint signature is unchanged — only the response model grows.

## Data Flow

1. **`content_generation_agent`** produces 5 slides per article, each with a `visual_type` tag.
2. **`slide_verification_agent`** confirms the tag is valid.
3. **Repository saves** slides to DB (new column).
4. **Image worker** iterates slides and dispatches per-slide to the correct strategy.
5. **`DalleSlideImageStrategy`** calls OpenAI for `generative` slides only.
6. **`ProgrammaticPILStrategy`** and **`TemplateCompositingSlideImageStrategy`** render locally and upload to R2.
7. **Approval UI** surfaces the strategy used per slide (transparency for cost/quality trade-offs).

## Error Handling

- **`visual_type` missing or invalid in DB:** factory raises `ValueError`; worker logs and continues with next slide; article ends in `failed` if any slide fails. Existing behavior preserved.
- **DALL-E call fails:** already handled — return `None`, slide ends up without an `image_url`, and the user can hit "Regenerate" in the UI. **No change.**
- **Theme library lookup fails (unknown industry):** falls back to default slate gradient. Logged at `INFO`, never raises.
- **R2 upload fails:** bubbles up to the worker, article goes to `failed`. **No change.**

## Testing

Extend [tests/test_image_strategies.py](../../apps/api/tests/test_image_strategies.py):

- `ProgrammaticPILStrategy` produces a valid 1080x1080 WebP given a theme name.
- `SlideImageStrategyFactory.get_strategy("minimalist" | "thematic" | "generative")` returns the right concrete class.
- `get_strategy("unknown")` raises `ValueError`.

Extend [tests/test_agents.py](../../apps/api/tests/test_agents.py):

- `content_generation_agent` produces slides with valid `visual_type` for both happy path and fallback.
- `slide_verification_agent` rejects slides missing `visual_type`.

Extend [tests/test_renderer.py](../../apps/api/tests/test_renderer.py):

- The extracted `draw_slide_text()` helper produces identical output to the inlined version (snapshot test for one known input).

## Rollout

This is a single integrated change, so the implementation is one phase:

1. Schema migration (add `visual_type` column).
2. Implement `ThemeLibrary` and `ProgrammaticPILStrategy`.
3. Extract `draw_slide_text()` helper in renderer.
4. Update LLM prompts and verification.
5. Update factory to take `visual_type`.
6. Update workers to pass `slide.visual_type`.
7. Update API schema.
8. Tests.

Because the `DalleSlideImageStrategy` route is preserved as-is, the change is **backward compatible**: any article currently in the DB without `visual_type` will fail strategy lookup, which is correct — re-running the workflow regenerates the slides with the new tag.

## Open Risks

- **LLM may overuse `generative`** if the cost-awareness prompt isn't strong enough. Mitigation: ship with telemetry on the visual_type distribution; tighten prompt if generative > 30% of slides on average.
- **Theme quality perception.** The PIL gradients need to look "expensive" not "PowerPoint 2003." Mitigation: keep themes visually minimal and brand-neutral; expose them in the UI so users can give feedback.
- **Alembic migration timing.** Adding a non-nullable column to an existing table with rows requires either a default or a two-step migration. Mitigation: column is `nullable=True`; strategy factory raises on `None` so old rows fail loudly and force re-generation rather than silently producing the wrong output.
