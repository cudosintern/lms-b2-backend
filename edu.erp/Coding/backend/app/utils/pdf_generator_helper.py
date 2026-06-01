from reportlab.pdfgen import canvas
from io import BytesIO


def generate_pdf_report(report_data, header_data):
    """
    Generate PDF content for the report.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    # Add header details
    pdf.drawString(100, 800, f"Report Header: {header_data}")

    # Add report data
    y = 750
    for row in report_data:
        pdf.drawString(100, y, f"{row}")
        y -= 20

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_header(details):
    """
    Build header string for the report.
    """
    return f"{details['college_name']} - {details['report_name']}"
