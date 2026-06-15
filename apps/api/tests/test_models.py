# apps/api/tests/test_models.py
"""Direct model class tests (no DB required)."""
from models.core import Project, Slide


def test_project_has_style_preset():
    """Project model should have a style_preset column."""
    # Use the column metadata to verify the field exists on the mapper
    assert hasattr(Project, "style_preset"), "Project model missing style_preset"
    # The column should be a mapped attribute
    from sqlalchemy import inspect
    mapper = inspect(Project)
    assert "style_preset" in mapper.columns, "style_preset not a mapped column"


def test_slide_has_text_zone():
    """Slide model should have a text_zone column."""
    assert hasattr(Slide, "text_zone"), "Slide model missing text_zone"
    from sqlalchemy import inspect
    mapper = inspect(Slide)
    assert "text_zone" in mapper.columns, "text_zone not a mapped column"


def test_slide_has_visual_type():
    """Slide model should have a visual_type column."""
    assert hasattr(Slide, "visual_type"), "Slide model missing visual_type"
    from sqlalchemy import inspect
    mapper = inspect(Slide)
    assert "visual_type" in mapper.columns, "visual_type not a mapped column"


def test_slide_text_zone_column_length():
    """text_zone column should be String(32)."""
    from sqlalchemy import inspect
    mapper = inspect(Slide)
    col = mapper.columns["text_zone"]
    assert col.type.length == 32, f"text_zone should be String(32), got {col.type.length}"


def test_slide_visual_type_column_length():
    """visual_type column should be String(16)."""
    from sqlalchemy import inspect
    mapper = inspect(Slide)
    col = mapper.columns["visual_type"]
    assert col.type.length == 16, f"visual_type should be String(16), got {col.type.length}"


def test_project_style_preset_column_length():
    """style_preset column should be String(32)."""
    from sqlalchemy import inspect
    mapper = inspect(Project)
    col = mapper.columns["style_preset"]
    assert col.type.length == 32, f"style_preset should be String(32), got {col.type.length}"
