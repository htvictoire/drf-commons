"""
Data processing utilities for export operations.
"""

from typing import Any, Dict, List, Tuple

from .utils import extract_nested_value


def extract_common_values_and_filter_columns(
    data: List[Dict], includes: List[str], column_config: Dict[str, Dict]
) -> Tuple[Dict[str, str], List[str]]:
    """
    Extract common values for fields marked with can_be_common=True and filter out those columns.

    Args:
        data: List of data dictionaries
        includes: List of field names to include
        column_config: Column configuration with labels and can_be_common flags

    Returns:
        Tuple of (common_values_dict, remaining_field_names)
    """
    common_values = {}
    remaining_includes = []

    for field_name in includes:
        field_config = column_config.get(field_name, {})

        # Check if this field can be common
        if field_config.get("can_be_common", False):
            # Check if all values are the same for this field and not null/empty
            values = [row.get(field_name) for row in data]
            non_empty_values = [
                v for v in values if v is not None and str(v).strip() != ""
            ]
            unique_values = set(
                str(v) for v in non_empty_values
            )  # Convert to string for comparison

            # If all non-empty values are the same, we have at least one value, and all records have this value
            if (
                len(unique_values) == 1
                and len(non_empty_values) > 0
                and len(non_empty_values) == len(data)
            ):
                field_label = field_config.get(
                    "label", field_name.replace("_", " ").title()
                )
                common_values[field_label] = list(unique_values)[0]
                # Don't include this field in the table
                continue

        # Include this field in the table
        remaining_includes.append(field_name)

    return common_values, remaining_includes


def prepare_export_headers(common_values: Dict[str, str]) -> List[str]:
    """
    Prepare export headers combining docs header and common values only.

    Args:
        common_values: Dict of field labels and their common values

    Returns:
        List of header lines for top-left of document
    """
    headers = []

    # Add docs header from settings
    try:
        from constance import config as constance_settings

        docs_header_str = getattr(constance_settings, "DEFAULT_DOCS_HEADER", "")
    except (ImportError, RuntimeError):
        docs_header_str = ""

    docs_header = (
        [line.strip() for line in docs_header_str.split(",")]
        if docs_header_str
        else []
    )
    headers.extend(docs_header)

    # Add empty line after docs header if we have docs header
    if docs_header and common_values:
        headers.append("")

    # Add common values as "Label: Value"
    for label, value in common_values.items():
        headers.append(f"{label}: {value}")

    return headers


def prepare_document_titles(file_titles: List[str]) -> List[str]:
    """
    Prepare document titles to be centered above the table.

    Args:
        file_titles: List of custom file titles

    Returns:
        List of title lines to be centered
    """
    titles = []
    for title in file_titles:
        if title.strip():
            titles.append(title.strip())
    return titles


def process_export_data(
    provided_data: List[Dict],
    includes: List[str],
    column_config: Dict[str, Dict],
    file_titles: List[str] = None,
) -> Dict[str, Any]:
    """
    Process export data and prepare it for different formats.

    Args:
        provided_data: Raw data to export
        includes: List of field names to include
        column_config: Column configuration dict
        file_titles: Optional list of titles

    Returns:
        Dict containing processed data and metadata
    """
    if file_titles is None:
        file_titles = []

    # Filter data to only include requested fields with their labels
    filtered_data = []
    for row in provided_data:
        filtered_row = {}
        for field_name in includes:
            value = extract_nested_value(row, field_name)
            filtered_row[field_name] = value
        filtered_data.append(filtered_row)

    # Extract common values for header and get remaining columns for table
    common_values, remaining_includes = extract_common_values_and_filter_columns(
        filtered_data, includes, column_config
    )

    # Filter data to only include non-common columns
    table_data = []
    for row in filtered_data:
        table_row = {}
        for field_name in remaining_includes:
            table_row[field_name] = row.get(field_name)
        table_data.append(table_row)

    # Prepare export headers (docs header + common values only)
    export_headers = prepare_export_headers(common_values)

    # Prepare document titles (centered above table)
    document_titles = prepare_document_titles(file_titles)

    return {
        "table_data": table_data,
        "remaining_includes": remaining_includes,
        "export_headers": export_headers,
        "document_titles": document_titles,
    }
