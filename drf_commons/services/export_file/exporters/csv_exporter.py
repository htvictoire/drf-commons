"""
CSV export implementation.
"""

import csv
from typing import Dict, List

from django.http import HttpResponse

from ..utils import (
    get_column_label,
    get_working_date,
    sanitize_spreadsheet_cell,
)


class CSVExporter:
    """Handles CSV export operations."""

    def export(
        self,
        data_rows: List[Dict],
        includes: List[str],
        column_config: Dict[str, Dict],
        filename: str,
        export_headers: List[str],
        document_titles: List[str],
    ) -> HttpResponse:
        """Export data as CSV file."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        if not data_rows:
            return response

        writer = csv.writer(response)

        # Write document headers (top left)
        for header_line in export_headers:
            if header_line.strip():
                writer.writerow([sanitize_spreadsheet_cell(str(header_line))])

        # Add spacing after headers if we have them
        if export_headers:
            writer.writerow([""])

        # Write document titles (centered above table)
        for title in document_titles:
            if title.strip():
                writer.writerow([sanitize_spreadsheet_cell(str(title))])

        # Add spacing after titles if we have them
        if document_titles:
            writer.writerow([""])

        # Write column headers
        headers = [
            sanitize_spreadsheet_cell(str(get_column_label(field, column_config)))
            for field in includes
        ]
        writer.writerow(headers)

        # Write data
        for row in data_rows:
            csv_row = []
            for field_name in includes:
                value = row.get(field_name, "")
                # Handle None values and convert to string
                cell_value = str(value) if value is not None else ""
                csv_row.append(sanitize_spreadsheet_cell(cell_value))
            writer.writerow(csv_row)

        # Write footer with working date
        writer.writerow([""])  # Empty row before footer
        writer.writerow([f"Date: {get_working_date()}"])

        return response
