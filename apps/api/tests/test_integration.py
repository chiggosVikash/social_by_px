import base64
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_full_pipeline_from_prompt_to_webp():
    """Test the full pipeline: LLM brief -> DALL-E -> PIL -> WebP."""
    from services.image import DalleSlideImageStrategy
    from services.style_presets import get_preset

    # Mock the image generation service to return a dummy image
    mock_image_bytes = b"fake_png_data"

    class FakeSlide:
        text_content = "Test content"
        emoji = "🔥"
        caption = "Test caption"
        text_zone = "full center"
        image_prompt = (
            "ROLE: hook\n"
            "PALETTE: #1a1a1a, #f4f1ec\n"
            "FOCAL: abstract sphere\n"
            "TEXT_ZONE: full center\n"
            "COMPOSITION: negative space"
        )

    class FakeArticle:
        id = 1

    project = type("Project", (), {"style_preset": "tech_editorial"})()

    # Mock the image service, renderer, storage, and optimization
    with patch("services.image.get_image_generation_service") as mock_get_service, \
         patch("services.renderer.composite_text_on_background") as mock_composite, \
         patch("services.storage.upload_file") as mock_upload, \
         patch("services.image.ImageOptimizationService.optimize_for_web") as mock_optimize:
        mock_image_service = AsyncMock()
        mock_image_service.generate.return_value = mock_image_bytes
        mock_get_service.return_value = mock_image_service
        mock_composite.return_value = b"fake_rendered_bytes"
        mock_upload.return_value = "https://storage.example.com/slide.webp"
        mock_optimize.return_value = b"fake_webp_data"

        strategy = DalleSlideImageStrategy()

        result = await strategy.generate_and_save(
            db=None,  # Mock DB
            slide=FakeSlide(),
            article=FakeArticle(),
            project=project,
            idx=0,
            total=5,
        )

        assert result == "https://storage.example.com/slide.webp"

        # Verify the image service was called with the composed prompt containing text_zone constraint
        call_args = mock_image_service.generate.call_args
        dalle_input = call_args[0][0]
        assert "TEXT_ZONE: full center" in dalle_input.upper() or "FULL CENTER" in dalle_input.upper(), (
            f"DALL-E prompt missing text_zone constraint. Got: {dalle_input}"
        )
        assert "STYLE LOCK" in dalle_input, "DALL-E prompt missing style lock"
        assert "COLOR PALETTE" in dalle_input, "DALL-E prompt missing color palette"

        # Verify renderer was called with the right text_zone
        mock_composite.assert_called_once()
        call_kwargs = mock_composite.call_args.kwargs
        assert call_kwargs["text_zone"] == "full center", (
            f"Renderer called with wrong text_zone: {call_kwargs.get('text_zone')}"
        )
        assert call_kwargs["background_bytes"] == mock_image_bytes, (
            "Renderer should be called with DALL-E output bytes"
        )


@pytest.mark.asyncio
async def test_style_preset_loaded_in_prompt_composition():
    """Style preset's palette and style lock should appear in the composed DALL-E prompt."""
    from services.image import DalleSlideImageStrategy
    from services.style_presets import get_preset

    preset = get_preset("tech_editorial")
    assert preset.style  # has a style description
    assert len(preset.palette) >= 2  # has colors

    project = type("Project", (), {"style_preset": "tech_editorial"})()

    class FakeSlide:
        text_content = "x"
        emoji = None
        caption = None
        text_zone = "center-bottom third"
        image_prompt = "ROLE: hook"

    class FakeArticle:
        id = 1

    with patch("services.image.get_image_generation_service") as mock_get_service, \
         patch("services.renderer.composite_text_on_background") as mc, \
         patch("services.storage.upload_file") as mu, \
         patch("services.image.ImageOptimizationService.optimize_for_web") as mo:
        mock_service = AsyncMock()
        mock_service.generate.return_value = b"fake"
        mock_get_service.return_value = mock_service
        mc.return_value = b"x"
        mu.return_value = "https://x/y.webp"
        mo.return_value = b"x"

        strategy = DalleSlideImageStrategy()
        await strategy.generate_and_save(
            db=None,
            slide=FakeSlide(),
            article=FakeArticle(),
            project=project,
            idx=0,
            total=1,
        )

        dalle_input = mock_service.generate.call_args[0][0]
        # Style lock should contain the preset's style description
        assert preset.style in dalle_input, (
            f"Style lock missing preset's style. Style was: {preset.style!r}, prompt was: {dalle_input}"
        )
        # Palette colors should be in the prompt
        for color in preset.palette[:2]:  # check first 2 colors
            assert color in dalle_input, f"Color {color} not in prompt"


@pytest.mark.asyncio
async def test_pipeline_dispatches_to_correct_strategy():
    """Strategy factory should return the right strategy class per visual_type."""
    from services.image import SlideImageStrategyFactory

    for vt, expected in [
        ("generative", "DalleSlideImageStrategy"),
        ("thematic", "TemplateCompositingSlideImageStrategy"),
        ("minimalist", "ProgrammaticPILStrategy"),
    ]:
        strategy = SlideImageStrategyFactory.get_strategy(vt)
        assert strategy.__class__.__name__ == expected, (
            f"Wrong strategy for {vt}: got {strategy.__class__.__name__}, expected {expected}"
        )


@pytest.mark.asyncio
async def test_dalle_strategy_passes_all_text_zones_to_renderer():
    """Each valid text_zone should be forwarded to the renderer unchanged."""
    from services.image import DalleSlideImageStrategy

    zones = ["center-bottom third", "full center", "lower-left aligned", "right half clear"]

    for zone in zones:
        with patch("services.image.get_image_generation_service") as mock_get_service, \
             patch("services.renderer.composite_text_on_background") as mock_composite, \
             patch("services.storage.upload_file") as mock_upload, \
             patch("services.image.ImageOptimizationService.optimize_for_web") as mock_optimize:
            mock_service = AsyncMock()
            mock_service.generate.return_value = b"fake"
            mock_get_service.return_value = mock_service
            mock_composite.return_value = b"rendered"
            mock_upload.return_value = "https://x/y.webp"
            mock_optimize.return_value = b"webp"

            class FakeSlide:
                text_content = "x"
                emoji = None
                caption = None
                text_zone = zone
                image_prompt = "ROLE: hook"

            class FakeArticle:
                id = 1

            project = type("Project", (), {"style_preset": "general_soft"})()
            strategy = DalleSlideImageStrategy()
            await strategy.generate_and_save(
                db=None,
                slide=FakeSlide(),
                article=FakeArticle(),
                project=project,
                idx=0,
                total=1,
            )

            mock_composite.assert_called_once()
            call_kwargs = mock_composite.call_args.kwargs
            assert call_kwargs["text_zone"] == zone, (
                f"Zone {zone!r} not forwarded: renderer got {call_kwargs.get('text_zone')!r}"
            )


@pytest.mark.asyncio
async def test_dalle_strategy_default_zone_when_missing():
    """If slide has no text_zone, renderer should get the default."""
    from services.image import DalleSlideImageStrategy

    with patch("services.image.get_image_generation_service") as mock_get_service, \
         patch("services.renderer.composite_text_on_background") as mock_composite, \
         patch("services.storage.upload_file") as mock_upload, \
         patch("services.image.ImageOptimizationService.optimize_for_web") as mock_optimize:
        mock_service = AsyncMock()
        mock_service.generate.return_value = b"fake"
        mock_get_service.return_value = mock_service
        mock_composite.return_value = b"rendered"
        mock_upload.return_value = "https://x/y.webp"
        mock_optimize.return_value = b"webp"

        class FakeSlide:
            text_content = "x"
            emoji = None
            caption = None
            text_zone = None  # missing
            image_prompt = "ROLE: hook"

        class FakeArticle:
            id = 1

        project = type("Project", (), {"style_preset": "general_soft"})()
        strategy = DalleSlideImageStrategy()
        await strategy.generate_and_save(
            db=None,
            slide=FakeSlide(),
            article=FakeArticle(),
            project=project,
            idx=0,
            total=1,
        )

        mock_composite.assert_called_once()
        call_kwargs = mock_composite.call_args.kwargs
        # Should default to the canonical zone
        assert call_kwargs["text_zone"] in (None, "center-bottom third"), (
            f"Unexpected default zone: {call_kwargs.get('text_zone')!r}"
        )


@pytest.mark.asyncio
async def test_minimalist_strategy_uses_pil_not_dalle():
    """ProgrammaticPILStrategy should NEVER call the image generation service."""
    from services.image import SlideImageStrategyFactory

    strategy = SlideImageStrategyFactory.get_strategy("minimalist")

    with patch("services.image.get_image_generation_service") as mock_get_service, \
         patch("services.renderer.composite_text_on_background") as mock_composite, \
         patch("services.storage.upload_file") as mock_upload, \
         patch("services.image.ImageOptimizationService.optimize_for_web") as mock_optimize:
        mock_service = AsyncMock()
        mock_service.generate.return_value = b"fake"
        mock_get_service.return_value = mock_service
        mock_composite.return_value = b"rendered"
        mock_upload.return_value = "https://x/y.webp"
        mock_optimize.return_value = b"webp"

        class FakeSlide:
            text_content = "x"
            emoji = None
            caption = None
            text_zone = "center-bottom third"
            image_prompt = "ROLE: hook"

        class FakeArticle:
            id = 1

        project = type("Project", (), {"style_preset": "general_soft"})()
        result = await strategy.generate_and_save(
            db=None,
            slide=FakeSlide(),
            article=FakeArticle(),
            project=project,
            idx=0,
            total=1,
        )

        assert result == "https://x/y.webp"
        # PIL strategy must NOT call DALL-E
        mock_service.generate.assert_not_called()  # ProgrammaticPILStrategy should not call the image generation service
        # But it should still call the renderer
        mock_composite.assert_called_once()


@pytest.mark.asyncio
async def test_thematic_strategy_uses_template():
    """TemplateCompositingSlideImageStrategy should not call DALL-E (uses template)."""
    from services.image import SlideImageStrategyFactory

    strategy = SlideImageStrategyFactory.get_strategy("thematic")

    with patch("services.image.get_image_generation_service") as mock_get_service, \
         patch("services.renderer.composite_text_on_background") as mock_composite, \
         patch("services.storage.upload_file") as mock_upload, \
         patch("services.image.ImageOptimizationService.optimize_for_web") as mock_optimize:
        mock_service = AsyncMock()
        mock_service.generate.return_value = b"fake"
        mock_get_service.return_value = mock_service
        mock_composite.return_value = b"rendered"
        mock_upload.return_value = "https://x/y.webp"
        mock_optimize.return_value = b"webp"

        class FakeSlide:
            text_content = "x"
            emoji = None
            caption = None
            text_zone = "center-bottom third"
            image_prompt = "ROLE: hook"

        class FakeArticle:
            id = 1

        # Provide a background URL for the template strategy
        project = type("Project", (), {
            "style_preset": "general_soft",
            "background_image_url": "https://example.com/template.webp",
        })()
        result = await strategy.generate_and_save(
            db=None,
            slide=FakeSlide(),
            article=FakeArticle(),
            project=project,
            idx=0,
            total=1,
        )

        assert result == "https://x/y.webp"
        # Template strategy must NOT call DALL-E
        mock_service.generate.assert_not_called()  # TemplateCompositingSlideImageStrategy should not call the image generation service
        mock_composite.assert_called_once()


def test_all_presets_have_required_fields():
    """Every style preset should have a non-empty style, palette, and ID."""
    from services.style_presets import get_preset, PRESETS

    assert len(PRESETS) >= 6, f"Expected at least 6 presets, got {len(PRESETS)}"

    preset_ids = set(PRESETS.keys())
    expected_ids = {
        "general_soft",
        "tech_editorial",
        "health_warm",
        "finance_paper",
        "education_warm",
        "marketing_bold",
    }
    missing = expected_ids - preset_ids
    assert not missing, f"Missing preset IDs: {missing}"

    for preset_id, preset in PRESETS.items():
        assert preset.name == preset_id, (
            f"Preset key/ID mismatch: key={preset_id!r}, name={preset.name!r}"
        )
        assert preset.style, f"Preset {preset_id} missing style description"
        assert len(preset.palette) >= 2, (
            f"Preset {preset_id} has fewer than 2 palette colors: {preset.palette}"
        )
        # get_preset should return the same preset
        assert get_preset(preset_id) is preset, (
            f"get_preset({preset_id!r}) did not return the registered preset"
        )
