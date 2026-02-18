"""
Utility functions for export operations.
"""

from typing import Any, Dict

from django.utils import timezone

from drf_commons.common_conf import settings

SPREADSHEET_DANGEROUS_PREFIXES = ("=", "+", "-", "@")


def get_working_date() -> str:
    """Get the current working date as a formatted string."""
    return str(timezone.localtime().strftime(settings.EXPORTED_DOCS_DATE_FORMAT))


def get_export_context_settings() -> Dict[str, Any]:
    """Get common settings for export templates."""
    return {
        # Margins
        "default_margin": settings.EXPORTED_DOCS_DEFAULT_MARGIN,
        "table_margin": settings.EXPORTED_DOCS_PDF_TABLE_MARGIN,
        # Typography
        "default_font_size": settings.EXPORTED_DOCS_DEFAULT_FONT_SIZE,
        "header_font_size": settings.EXPORTED_DOCS_HEADER_FONT_SIZE,
        "title_font_size": settings.EXPORTED_DOCS_TITLE_FONT_SIZE,
        # Layout
        "row_height": settings.EXPORTED_DOCS_PDF_TABLE_ROW_HEIGHT,
        # Paddings
        "cell_padding": settings.EXPORTED_DOCS_PDF_CELL_PADDING,
        "header_padding_v": settings.EXPORTED_DOCS_PDF_HEADER_PADDING_V,
        "header_padding_h": settings.EXPORTED_DOCS_PDF_HEADER_PADDING_H,
        # Vertical Spacing
        "header_to_title_spacing": settings.EXPORTED_DOCS_PDF_HEADER_TO_TITLE_SPACING,
        "title_to_table_spacing": settings.EXPORTED_DOCS_PDF_TITLE_TO_TABLE_SPACING,
        # Colors
        "header_color": settings.EXPORTED_DOCS_DEFAULT_TABLE_HEADER_COLOR,
        "text_color": settings.EXPORTED_DOCS_DEFAULT_TEXT_COLOR,
        "border_color": settings.EXPORTED_DOCS_DEFAULT_BORDER_COLOR,
        "alternate_row_color": settings.EXPORTED_DOCS_DEFAULT_ALTERNATE_ROW_COLOR,
    }


def extract_nested_value(data: Dict[str, Any], field_path: str) -> Any:
    """
    Extract value from nested data structure using dot notation.

    Args:
        data: The data dictionary
        field_path: Field path like 'latest_registration_data.academic_class'

    Returns:
        The extracted value or None if not found
    """
    if "." not in field_path:
        # Simple field access
        return data.get(field_path)

    # Handle nested field access
    parts = field_path.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None

    # Convert to string if it's a complex object
    if current is not None and not isinstance(
        current, (str, int, float, bool, type(None))
    ):
        return str(current)

    return current


def get_column_label(field_name: str, column_config: Dict[str, Dict]) -> str:
    """
    Get the display label for a column.

    Args:
        field_name: The field name
        column_config: Column configuration dict

    Returns:
        The display label
    """
    field_config = column_config.get(field_name, {})
    return field_config.get("label", field_name.replace("_", " ").title())


def get_column_alignment(field_name: str, column_config: Dict[str, Dict]) -> str:
    """
    Get the alignment for a column.

    Args:
        field_name: The field name
        column_config: Column configuration dict

    Returns:
        The alignment ('left', 'center', 'right')
    """
    field_config = column_config.get(field_name, {})
    align = field_config.get("align", "left")
    return align if align in ["left", "center", "right"] else "left"


def sanitize_spreadsheet_cell(value: Any) -> Any:
    """
    Neutralize spreadsheet formula injection for string values.

    Strings whose first non-whitespace character starts with one of the
    formula-control prefixes (=, +, -, @) are prefixed with a single quote.
    """
    if not isinstance(value, str):
        return value

    stripped = value.lstrip()
    if stripped and stripped[0] in SPREADSHEET_DANGEROUS_PREFIXES:
        return f"'{value}"
    return value
