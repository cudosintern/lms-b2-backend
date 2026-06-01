from fpdf import FPDF
from io import BytesIO
from fastapi.responses import StreamingResponse


class UsnListCourseWiseTemplate:
    def __init__(self, logo_url, college_name, other_descriptions1):
        self.logo_url = logo_url
        self.college_name = college_name
        self.other_descriptions1 = other_descriptions1
        self.pdf = FPDF()

    def set_header(self):
        # Add header with logo and title
        self.pdf.set_font("Arial", size=12)
        self.pdf.cell(0, 10, txt=self.college_name, ln=True, align='C')
        self.pdf.set_font("Arial", size=10)
        self.pdf.cell(0, 10, txt=self.other_descriptions1, ln=True, align='C')
        self.pdf.line(10, 20, 200, 20)  # Add a horizontal line

    def set_footer(self):
        # Add footer with HOD, Dean, Principal
        self.pdf.set_y(-30)
        self.pdf.set_font("Arial", size=10)
        self.pdf.cell(0, 10, txt="HOD", ln=0, align='L')
        self.pdf.cell(0, 10, txt="Dean(Academic Affairs)", ln=0, align='C')
        self.pdf.cell(0, 10, txt="Principal", ln=0, align='R')

    def get_report(self, report_data, flag1, course):
        self.pdf.add_page()
        self.set_header()
        self.pdf.set_font("Arial", size=12)
        self.pdf.cell(0, 10, txt=f"Eligibility List Report - {course}", ln=True, align='C')

        # Add table headers
        self.pdf.set_font("Arial", style="B", size=10)
        self.pdf.cell(10, 10, txt="SL", border=1, align='C')
        self.pdf.cell(50, 10, txt="USN", border=1, align='C')

        # Conditionally add additional headers based on the presence of eligibility fields
        if 'attendance_eligibility' in report_data[0] and 'cia_eligibility' in report_data[0]:
            self.pdf.cell(50, 10, txt="ATTENDANCE Eligibility", border=1, align='C')
            self.pdf.cell(50, 10, txt="CIA Eligibility", border=1, align='C')

        self.pdf.ln()

        # Add table data
        self.pdf.set_font("Arial", size=10)
        for idx, usn_data in enumerate(report_data, start=1):
            usn = usn_data.get('usno', '')  # Extract the 'usno' value
            attendance_eligibility = usn_data.get('attendance_eligibility', 'N/A')  # Default to 'N/A' if not present
            cia_eligibility = usn_data.get('cia_eligibility', 'N/A')  # Default to 'N/A' if not present

            self.pdf.cell(10, 10, txt=str(idx), border=1, align='C')
            self.pdf.cell(50, 10, txt=usn, border=1, align='L')  # Use the extracted usn

            # Only add eligibility columns if those keys exist in the current row data
            if 'attendance_eligibility' in usn_data and 'cia_eligibility' in usn_data:
                self.pdf.cell(50, 10, txt=attendance_eligibility, border=1, align='C')  # Attendance eligibility
                self.pdf.cell(50, 10, txt=cia_eligibility, border=1, align='C')  # CIA eligibility

            self.pdf.ln()

        # Generate and return PDF
        stream = BytesIO()
        pdf_content = self.pdf.output(dest='S').encode('latin1')  # Output to string buffer
        stream.write(pdf_content)
        stream.seek(0)

        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Eligibility_List_Report.pdf"}
        )