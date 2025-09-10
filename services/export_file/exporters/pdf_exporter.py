"""
PDF export implementation.
"""

from typing import Dict, List
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from ..utils import get_column_label, get_column_alignment, get_working_date, get_export_context_settings
from ... import settings


class PDFExporter:
    """Handles PDF export operations."""
    
    def _determine_orientation(self, data_rows: List[Dict], includes: List[str], 
                              column_config: Dict[str, Dict]) -> str:
        """
        Determine PDF orientation based on row content width analysis.
        
        Args:
            data_rows: List of data dictionaries
            includes: List of field names to include  
            column_config: Column configuration dict
            
        Returns:
            str: 'portrait' or 'landscape'
        """
        if not settings.EXPORTED_DOCS_PDF_AUTO_ORIENTATION:
            return 'portrait'
            
        if not data_rows:
            return 'portrait'
        
        # Get settings
        avg_char_width = settings.EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH
        row_threshold_pct = settings.EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE
        
        # Estimate available width for portrait (A4 portrait minus margins)
        # A4 = 595pt width, minus margins = ~535pt available
        portrait_available_width = 535
        
        # Analyze each row's total content width
        problematic_rows = 0
        total_rows = len(data_rows)
        
        for row in data_rows:
            # Calculate total character length for this row
            row_total_chars = 0
            
            # Include header lengths in calculation
            for field_name in includes:
                header = get_column_label(field_name, column_config)
                value = row.get(field_name, '')
                
                # Use the longer of header or value for each column
                header_length = len(str(header))
                value_length = len(str(value) if value is not None else '')
                max_length = max(header_length, value_length)
                
                row_total_chars += max_length

            # Convert to points
            row_width_points = row_total_chars * avg_char_width

            # Check if row width is 130% greater than available width
            if row_width_points > (portrait_available_width * 1.3):
                problematic_rows += 1
        
        # Calculate percentage of problematic rows
        if total_rows > 0:
            problematic_percentage = (problematic_rows / total_rows) * 100
        else:
            problematic_percentage = 0

        # Decision: switch to landscape if problematic percentage exceeds threshold
        return 'landscape' if problematic_percentage >= row_threshold_pct else 'portrait'
    
    def export(self, data_rows: List[Dict], includes: List[str], 
               column_config: Dict[str, Dict], filename: str, 
               export_headers: List[str], document_titles: List[str]) -> HttpResponse:
        """Export data as PDF file using HTML/CSS template with WeasyPrint."""
        
        # Determine orientation based on content analysis
        orientation = self._determine_orientation(data_rows, includes, column_config)
        
        # Prepare column labels and alignments
        column_labels = {}
        column_alignments = {}
        for field_name in includes:
            column_labels[field_name] = get_column_label(field_name, column_config)
            column_alignments[field_name] = get_column_alignment(field_name, column_config)
        
        # Prepare template context
        context = {
            'orientation': orientation,
            'data_rows': data_rows,
            'includes': includes,
            'column_labels': column_labels,
            'column_alignments': column_alignments,
            'export_headers': export_headers,
            'document_titles': document_titles,
            'working_date': get_working_date(),
            **get_export_context_settings()  # Add all settings
        }
        
        # Render HTML template
        html_string = render_to_string('exports/pdf_template.html', context)
        
        # Generate PDF using WeasyPrint
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()
        
        # Create response
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response