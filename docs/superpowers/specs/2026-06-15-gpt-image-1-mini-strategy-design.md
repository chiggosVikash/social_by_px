# gpt-image-1-mini Image Generation Strategy — Design Spec

**Date:** 2026-06-15
**Status:** Approved
**Author:** Brainstorming session with Vikash Roy

## Problem

The current `DalleSlideImageStrategy` calls `gpt-5.5` via OpenAI's **Responses API** for every slide that needs a generated image (see [services/image.py:22-55](../../apps/api/src/services/image.py#L22-L55)). This runs roughly **$0.20–$0.40 per article** (5 slides × DALL-E 3 standard pricing), and the generated images are mostly abstract minimalist backgrounds — work for which the full model is overkill.

A cheaper image model is available — `gpt-image-1-mini` — and integrating it as the default strategy drops cost by ~82% at the same quality for our use case.

**Goals:**
- Cut image generation cost by ~82% per article.
- Maintain slide quality for the dominant use case (abstract/minimalist backgrounds).
- Keep the existing strategy pattern intact so future model swaps stay cheap.
- Reserve space for per-slide model selection without forcing a future migration.

**Non-goals:**
- Switching LLM providers.
- Changing the user-facing approval workflow.
- Building a model-selection UI.

## Pricing Reference

`gpt-image-1-mini` per-image pricing (1024x1024):

| Quality | Cost per image |
|---------|----------------|
| Low     | $0.005 |
| Medium  | $0.011 |
| High    | $0.036 |

For a 5-slide carousel:
- **All medium** = $0.055 / article
- All low    = $0.025 / article
- All high   = $0.18 / article

**Default choice:** medium. Prompt adherence is solid for our use case (backgrounds with text overlay), and the cost-quality ratio is the sweet spot.

## Solution: Replace `OpenAIImageStrategy` with `GptImage1MiniStrategy`

Add a new concrete strategy that uses the **OpenAI Images API** (`client.images.generate`) with model `gpt-image-1-mini`. Wire it into the existing factory. No downstream code changes — `DalleSlideImageStrategy` consumes the strategy opaquely.

## Architecture

### New Strategy Class

File: [services/image.py](../../apps/api/src/services/image.py). Place next to the existing `OpenAIImageStrategy`.

```python
class GptImage1MiniStrategy(ImageGenerationStrategy):
    """Cost-efficient image generation using OpenAI's gpt-image-1-mini model.

    Uses the Images API (not the Responses API) for direct per-image pricing.
    """

    MODEL_NAME = "gpt-image-1-mini"
    DEFAULT_QUALITY = "medium"
    DEFAULT_SIZE = "1024x1024"

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set.")

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            logger.info(
                f"Calling OpenAI Images API with model {self.MODEL_NAME} "
                f"quality={self.DEFAULT_QUALITY} size={self.DEFAULT_SIZE}"
            )
            response = await client.images.generate(
                model=self.MODEL_NAME,
                prompt=prompt,
                size=self.DEFAULT_SIZE,
                quality=self.DEFAULT_QUALITY,
                n=1,
                response_format="b64_json",
            )
        except Exception as api_e:
            logger.error(f"gpt-image-1-mini call failed: {api_e}")
            return None

        if not response or not response.data:
            return None

        b64 = getattr(response.data[0], "b64_json", None)
        if not b64:
            logger.warning("gpt-image-1-mini returned no b64_json in response")
            return None

        return base64.b64decode(b64)
```

### Factory Swap

In [`get_image_generation_service()`](../../apps/api/src/services/image.py#L79), change the constructed strategy from `OpenAIImageStrategy()` to `GptImage1MiniStrategy()`. The class `OpenAIImageStrategy` remains in the file (not deleted) so any direct callers or future tests can still use it.

### Prompt Prefix Update

The current prefix in [services/image.py:137](../../apps/api/src/services/image.py#L137) reads:

```
"Abstract background for a social media slide. Minimalist, modern, beautiful, subtle. Theme: {prompt_source[:500]}"
```

`gpt-image-1-mini` is more literal than DALL-E 3 — vague style words produce flat results. The prefix is updated to include concrete visual cues that perform well on the GPT Image family:

```
"Soft, even lighting. No text, no people, no objects. Clean gradient or abstract pattern. "
"Suitable for white text overlay. Modern editorial style. Theme: {prompt_source[:500]}"
```

This is a one-line string change with no API surface impact.

### Schema: `image_model` Column (Reserved)

Add to the `Slide` model in [models/core.py](../../apps/api/src/models/core.py):

```python
image_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
```

**Nullable, no default.** The factory and strategies **ignore it for now**. When we later introduce per-slide model selection, we won't need a destructive migration — the column is already there.

Generate an Alembic migration that adds the nullable column. No backfill needed (existing rows are NULL, which means "use default" once we wire it up later).

### API Surface (Optional, Additive)

Extend `SlideOut` in [api/approvals.py](../../apps/api/src/api/approvals.py) to expose `image_model: str | None = None`. This is purely additive — existing clients keep working.

## Data Flow

**No changes** from the current flow:

1. LLM generates slide text + `image_prompt` ([agents/nodes.py:253](../../apps/api/src/agents/nodes.py#L253)).
2. Image worker calls `DalleSlideImageStrategy.generate_and_save(...)` ([workers/tasks.py:291](../../apps/api/src/workers/tasks.py#L291)).
3. Internally calls `get_image_generation_service().generate(prompt)` — which now resolves to `GptImage1MiniStrategy`.
4. Result is optimized to WebP and uploaded to R2.

The strategy pattern means **no changes** to the worker, the API, or the approval UI are required for the cost win. The `image_model` column is purely additive.

## Error Handling

- **Missing `OPENAI_API_KEY`:** raise `RuntimeError` at call time, same as current.
- **API error / timeout / 4xx / 5xx:** catch + log + return `None`. Same as current.
- **Empty `data` list:** return `None`; log at WARNING.
- **Missing `b64_json` in first data item:** return `None`; log at WARNING.
- **No retry logic:** preserved from current behavior. Adding retries later is a separate concern.

The worker at [workers/tasks.py:351](../../apps/api/src/workers/tasks.py#L351) already handles a `None` return by logging a warning and continuing — no change needed.

## Testing

Extend [tests/test_image_strategies.py](../../apps/api/tests/test_image_strategies.py) with a new test module or section:

1. **`GptImage1MiniStrategy` happy path** — mock `client.images.generate` to return a response with a valid b64 image. Assert decoded bytes are returned.
2. **API error path** — mock `client.images.generate` to raise. Assert returns `None` (does not raise).
3. **Empty data list** — mock returns `data=[]`. Assert returns `None`.
4. **Missing b64_json field** — mock returns a data item with `b64_json=None`. Assert returns `None`.
5. **Factory returns new strategy** — call `get_image_generation_service()` and assert `_strategy` is a `GptImage1MiniStrategy`.

The existing `DalleSlideImageStrategy` test (which mocks `get_image_generation_service`) **keeps working unchanged** — this is the strategy pattern earning its keep.

If a `test_gemini_integration.py`-style live-API test exists, add an opt-in live test (gated by env var) that calls the real API and asserts bytes come back. This is purely for confidence — the unit tests are the contract.

## Rollout

Single contained change:

1. Add `GptImage1MiniStrategy` class to `services/image.py`.
2. Update prompt prefix in `DalleSlideImageStrategy`.
3. Swap factory to use the new strategy.
4. Add `image_model` column to `Slide` model + alembic migration.
5. Add tests.
6. (Optional) Expose `image_model` in `SlideOut` schema.

Backward compatibility:
- `OpenAIImageStrategy` class is preserved in the file but not wired in.
- `DalleSlideImageStrategy` and worker code paths are untouched.
- The `image_model` column is nullable; existing rows are NULL, which is a safe default.
- The Responses API key still works (the new strategy uses the same `OPENAI_API_KEY`).

## Open Risks

- **Visual quality at medium:** Should be equivalent to DALL-E 3 standard for backgrounds. If it isn't, the cost-quality ratio could shift toward "low" + more aggressive PIL fallback. Mitigation: ship to staging first and eyeball 20 generated carousels before merging to main.
- **Rate limits:** gpt-image-1-mini has higher rate limits than gpt-image-1 (5 IPM at Tier 1, scaling up). At our volume, not a concern. If we ever burst above that, the worker already processes slides sequentially.
- **Cost creep via `high` quality:** If someone bumps the default to `high` later, the cost advantage shrinks dramatically. Mitigation: keep `DEFAULT_QUALITY = "medium"` as a class constant, and reference it from one place.

## Cost Projection (Recap)

| Approach | 5-slide cost | Savings vs current |
|----------|--------------|-------------------|
| Current (gpt-5.5 via Responses) | ~$0.30 | — |
| **gpt-image-1-mini @ medium (default)** | **~$0.055** | **~82%** |
| gpt-image-1-mini @ low | ~$0.025 | ~92% |
| gpt-image-1-mini @ high | ~$0.18 | ~40% |

*Note: the prior $0.20–$0.40 estimate assumed DALL-E 3 standard pricing for the current `gpt-5.5` Responses API path. The exact baseline depends on OpenAI's current pricing for that endpoint; the new absolute cost of $0.055 per article is fixed regardless.*
