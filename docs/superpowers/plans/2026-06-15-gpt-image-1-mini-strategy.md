# gpt-image-1-mini Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current `OpenAIImageStrategy` (gpt-5.5 via Responses API) with a new `GptImage1MiniStrategy` (gpt-image-1-mini via Images API), cutting per-article image cost by ~82%.

**Architecture:** Add a new concrete strategy class that implements the existing `ImageGenerationStrategy` interface. Wire it into the factory. The downstream `DalleSlideImageStrategy` and worker code are untouched — they consume the strategy opaquely. Add a nullable `image_model` column to `Slide` for future per-slide model selection.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Alembic, pytest, OpenAI Python SDK (images endpoint), PIL

---

## File Structure

| File | Change |
|------|--------|
| `apps/api/src/services/image.py` | Add `GptImage1MiniStrategy` class; update prompt prefix; swap factory |
| `apps/api/src/models/core.py` | Add `image_model` column to `Slide` model |
| `apps/api/tests/test_image_strategies.py` | Add tests for new strategy |
| `apps/api/alembic/versions/` | New migration file |
| `apps/api/src/api/approvals.py` | Add `image_model` to `SlideOut` schema |

---

## Task 1: Write Failing Tests for GptImage1MiniStrategy

**Files:**
- Modify: `apps/api/tests/test_image_strategies.py`

- [ ] **Step 1: Write the failing tests**

Add these test cases to the end of `tests/test_image_strategies.py`:

```python
import pytest
import base64
from unittest.mock import patch, MagicMock, AsyncMock
from services.image import (
    GptImage1MiniStrategy,
    get_image_generation_service,
)


@pytest.fixture
def mock_gpt_image_response():
    """Build a mock response that mimics openai.types.images_response.ImageResponse."""
    mock_data_item = MagicMock()
    mock_data_item.b64_json = base64.b64encode(b"fake_png_bytes").decode()

    mock_response = MagicMock()
    mock_response.data = [mock_data_item]
    return mock_response


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_happy_path(mock_openai_cls, mock_gpt_image_response):
    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(return_value=mock_gpt_image_response)
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("a blue gradient background")

    assert result == b"fake_png_bytes"
    mock_client.images.generate.assert_called_once_with(
        model="gpt-image-1-mini",
        prompt="a blue gradient background",
        size="1024x1024",
        quality="medium",
        n=1,
        response_format="b64_json",
    )


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_api_error(mock_openai_cls):
    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(side_effect=RuntimeError("API down"))
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("any prompt")

    assert result is None


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_empty_data(mock_openai_cls):
    mock_response = MagicMock()
    mock_response.data = []

    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(return_value=mock_response)
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("any prompt")

    assert result is None


@pytest.mark.asyncio
@patch("services.image.AsyncOpenAI")
async def test_gpt_image_1_mini_strategy_missing_b64_json(mock_openai_cls):
    mock_data_item = MagicMock()
    mock_data_item.b64_json = None

    mock_response = MagicMock()
    mock_response.data = [mock_data_item]

    mock_client = AsyncMock()
    mock_client.images.generate = AsyncMock(return_value=mock_response)
    mock_openai_cls.return_value = mock_client

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image("any prompt")

    assert result is None


def test_factory_returns_gpt_image_1_mini_strategy():
    service = get_image_generation_service()
    assert type(service._strategy).__name__ == "GptImage1MiniStrategy"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd apps/api && uv run pytest tests/test_image_strategies.py -v -k "gpt_image_1_mini or factory_returns"
```
Expected: FAIL — `ImportError: cannot import name 'GptImage1MiniStrategy'` and `FAIL` for the factory test.

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/test_image_strategies.py
git commit -m "test: add failing tests for GptImage1MiniStrategy

Tests happy path, API error, empty data, missing b64_json, and
factory routing. All expected to fail until implementation lands.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Implement GptImage1MiniStrategy

**Files:**
- Modify: `apps/api/src/services/image.py:22-55`

- [ ] **Step 1: Write the implementation**

Add the new strategy class in `apps/api/src/services/image.py`, right after the existing `OpenAIImageStrategy` class (after line 55, before the `OpenRouterImageStrategy` placeholder):

```python
# [SOLID: OCP] - Concrete Strategy for OpenAI gpt-image-1-mini (cost-efficient)
class GptImage1MiniStrategy(ImageGenerationStrategy):
    """Cost-efficient image generation using OpenAI's gpt-image-1-mini model.

    Uses the Images API (not the Responses API) for direct per-image pricing.
    Default: medium quality at 1024x1024 (~$0.011/image).
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

- [ ] **Step 2: Run tests to verify they pass**

Run:
```bash
cd apps/api && uv run pytest tests/test_image_strategies.py -v -k "gpt_image_1_mini or factory_returns"
```
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/api/src/services/image.py
git commit -m "feat: add GptImage1MiniStrategy using OpenAI Images API

Replaces gpt-5.5 Responses API with gpt-image-1-mini via
images.generate. Cuts per-image cost from ~$0.04 to ~$0.011
at medium quality. OpenAIImageStrategy class preserved for
backward compatibility.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Update Prompt Prefix for gpt-image-1-mini

**Files:**
- Modify: `apps/api/src/services/image.py:137`

- [ ] **Step 1: Update the prompt prefix**

In `apps/api/src/services/image.py`, find line 137 inside `DalleSlideImageStrategy.generate_and_save`:

```python
        prompt_source = slide.caption or slide.text_content or article.title
        image_prompt = f"Abstract background for a social media slide. Minimalist, modern, beautiful, subtle. Theme: {prompt_source[:500]}"
```

Replace with:

```python
        prompt_source = slide.caption or slide.text_content or article.title
        image_prompt = (
            f"Soft, even lighting. No text, no people, no objects. "
            f"Clean gradient or abstract pattern. Suitable for white text overlay. "
            f"Modern editorial style. Theme: {prompt_source[:500]}"
        )
```

- [ ] **Step 2: Verify existing tests still pass**

Run:
```bash
cd apps/api && uv run pytest tests/test_image_strategies.py -v
```
Expected: All PASS (existing tests mock `get_image_generation_service`, so the prompt change doesn't affect them).

- [ ] **Step 3: Commit**

```bash
git add apps/api/src/services/image.py
git commit -m "refactor: tune image prompt prefix for gpt-image-1-mini

Replace vague style words (minimalist, modern, beautiful) with
concrete visual cues (soft lighting, no objects, gradient/abstract)
that produce better results with the GPT Image family.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Swap Factory to Use GptImage1MiniStrategy

**Files:**
- Modify: `apps/api/src/services/image.py:79-85`

- [ ] **Step 1: Update the factory**

In `apps/api/src/services/image.py`, find `get_image_generation_service()` at line 79:

```python
def get_image_generation_service() -> ImageGenerationService:
    """
    Factory to resolve the correct strategy. 
    In the future, you can read from `get_settings().IMAGE_PROVIDER` to choose between OpenAI, , etc.
    """
    strategy = OpenAIImageStrategy()
    return ImageGenerationService(strategy)
```

Replace with:

```python
def get_image_generation_service() -> ImageGenerationService:
    """
    Factory to resolve the correct strategy.
    Currently uses gpt-image-1-mini via the Images API for cost efficiency.
    In the future, you can read from `get_settings().IMAGE_PROVIDER` to choose between models.
    """
    strategy = GptImage1MiniStrategy()
    return ImageGenerationService(strategy)
```

- [ ] **Step 2: Verify factory test passes**

Run:
```bash
cd apps/api && uv run pytest tests/test_image_strategies.py::test_factory_returns_gpt_image_1_mini_strategy -v
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/api/src/services/image.py
git commit -m "feat: wire factory to GptImage1MiniStrategy

All image generation now routes through gpt-image-1-mini via
the OpenAI Images API. OpenAIImageStrategy class preserved
in file for backward compatibility.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Add `image_model` Column to Slide Model

**Files:**
- Modify: `apps/api/src/models/core.py`
- Create: `apps/api/alembic/versions/<revision>_add_image_model_to_slide.py`

- [ ] **Step 1: Add column to model**

In `apps/api/src/models/core.py`, find the `Slide` class. Add the new column after `emoji`:

```python
class Slide(Base):
    __tablename__ = "slides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("articles.id"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    hook_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # question | statistic | bold_claim | story | cta
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    image_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    article: Mapped["Article"] = relationship("Article", back_populates="slides")
```

- [ ] **Step 2: Generate Alembic migration**

Run:
```bash
cd apps/api && uv run alembic revision --autogenerate -m "add image_model column to slides"
```
Verify the generated file in `alembic/versions/` contains `op.add_column("slides", sa.Column("image_model", sa.String(50), nullable=True))` and no `drop_column` or data-migration operations.

- [ ] **Step 3: Apply migration**

Run:
```bash
cd apps/api && uv run alembic upgrade head
```
Expected: `INFO  [alembic.runtime.migration] Context impl SQLiteImpl.` (or Postgres) and the new revision is listed as applied.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/models/core.py apps/api/alembic/versions/<revision_id>_add_image_model_to_slide.py
git commit -m "feat: add nullable image_model column to Slide model

Reserved for future per-slide model selection. Nullable with no
default so existing rows are unaffected. Accompanied by
Alembic migration.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Expose `image_model` in SlideOut Schema

**Files:**
- Modify: `apps/api/src/api/approvals.py:11-16`

- [ ] **Step 1: Add field to SlideOut**

In `apps/api/src/api/approvals.py`, find the `SlideOut` Pydantic model:

```python
class SlideOut(BaseModel):
    id: int
    text_content: str
    image_url: str | None = None
    caption: str | None = None
    emoji: str | None = None
```

Add the new field:

```python
class SlideOut(BaseModel):
    id: int
    text_content: str
    image_url: str | None = None
    caption: str | None = None
    emoji: str | None = None
    image_model: str | None = None
```

- [ ] **Step 2: Expose in approval response**

In the `get_pending_approvals` function, find where `SlideOut` is constructed (around line 43):

```python
                slides_out.append(SlideOut(
                    id=slide.id,
                    text_content=slide.text_content,
                    image_url=slide.image_url,
                    caption=slide.caption,
                    emoji=slide.emoji
                ))
```

Add `image_model`:

```python
                slides_out.append(SlideOut(
                    id=slide.id,
                    text_content=slide.text_content,
                    image_url=slide.image_url,
                    caption=slide.caption,
                    emoji=slide.emoji,
                    image_model=slide.image_model,
                ))
```

- [ ] **Step 3: Verify tests pass**

Run:
```bash
cd apps/api && uv run pytest tests/ -v --timeout=30
```
Expected: All existing tests pass.

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/api/approvals.py
git commit -m "feat: expose image_model in SlideOut schema

Additive change — existing clients ignore the new field.
Prepares the API for future per-slide model selection.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Final Integration Test

**Files:**
- Modify: `apps/api/tests/test_image_strategies.py`

- [ ] **Step 1: Add an integration test that exercises the full path**

```python
@pytest.mark.asyncio
async def test_gpt_image_1_mini_full_path_live():
    """Optional: live API test. Only runs when OPENAI_API_KEY is set and LIVE_API_TESTS=1."""
    import os
    if not os.environ.get("OPENAI_API_KEY") or os.environ.get("LIVE_API_TESTS") != "1":
        pytest.skip("Live API test skipped — set OPENAI_API_KEY and LIVE_API_TESTS=1 to run")

    strategy = GptImage1MiniStrategy()
    result = await strategy.generate_image(
        "Soft, even lighting. No text, no people, no objects. "
        "Clean gradient or abstract pattern. Suitable for white text overlay. "
        "Modern editorial style. Theme: artificial intelligence"
    )
    assert result is not None
    assert len(result) > 1000  # should be a real image
```

- [ ] **Step 2: Run only the non-live tests**

Run:
```bash
cd apps/api && uv run pytest tests/test_image_strategies.py -v -k "not live"
```
Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/test_image_strategies.py
git commit -m "test: add optional live API test for gpt-image-1-mini

Gated by LIVE_API_TESTS=1 env var. Provides confidence that
the strategy works end-to-end against the real API.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Run Full Test Suite

**Files:**
- (no files changed — verification only)

- [ ] **Step 1: Run the full test suite**

Run:
```bash
cd apps/api && uv run pytest tests/ -v
```
Expected: All tests pass. If any fail, fix before proceeding.

- [ ] **Step 2: Commit (only if fixes were needed)**

If fixes were needed, commit them. If all green, skip.

---

## Final Review Checklist

Before marking complete, verify:

- [ ] `services/image.py` contains `GptImage1MiniStrategy` class
- [ ] `get_image_generation_service()` returns `GptImage1MiniStrategy`
- [ ] Prompt prefix updated for gpt-image-1-mini compatibility
- [ ] `Slide` model has nullable `image_model` column
- [ ] Alembic migration applied
- [ ] `SlideOut` exposes `image_model`
- [ ] All tests pass (`pytest tests/`)
- [ ] `OpenAIImageStrategy` class preserved in file (not deleted)
- [ ] No changes to `DalleSlideImageStrategy` consumer, workers, or approval UI
