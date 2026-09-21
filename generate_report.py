import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Custom canvas to draw page numbers at bottom-center on all pages."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 11)
        # Margins: Left = 90pt, Right = 72pt. Total Width = 595.27pt.
        # Center of printable area = (90 + (595.27 - 72)) / 2 = 306.6pt
        page_num_str = f"{self._pageNumber}"
        self.drawCentredString(306.6, 45, page_num_str)
        self.restoreState()


def create_pdf(output_path):
    # Margins: top/bottom/right = 1 inch (72pt), left = 1.25 inch (90pt for binding)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.25 * inch,
        rightMargin=1.0 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch
    )

    styles = getSampleStyleSheet()

    # Base styling matching Formatting Guide
    body_style = ParagraphStyle(
        'CustomBody',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,           # 1.5 line spacing for 12pt
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    chapter_title_style = ParagraphStyle(
        'CustomChapterTitle',
        fontName='Times-Bold',
        fontSize=16,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=14
    )

    chapter_title_center = ParagraphStyle(
        'CustomChapterTitleCenter',
        fontName='Times-Bold',
        fontSize=16,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=14
    )

    section_heading_style = ParagraphStyle(
        'CustomSectionHeading',
        fontName='Times-Bold',
        fontSize=14,
        leading=20,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=6
    )

    center_14_bold = ParagraphStyle(
        'Center14Bold',
        fontName='Times-Bold',
        fontSize=14,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    center_12_regular = ParagraphStyle(
        'Center12Regular',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=4
    )

    center_12_bold = ParagraphStyle(
        'Center12Bold',
        fontName='Times-Bold',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        leftIndent=24,
        spaceAfter=6
    )

    toc_entry_style = ParagraphStyle(
        'TOCEntry',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=4
    )

    story = []

    # ==========================================
    # PAGE 1: TITLE / COVER PAGE
    # ==========================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("KAMARAJ COLLEGE OF ENGINEERING AND TECHNOLOGY", chapter_title_center))
    story.append(Spacer(1, 40))
    story.append(Paragraph("DEPARTMENT OF ADS", center_14_bold))
    story.append(Spacer(1, 40))
    story.append(Paragraph("MINI PROJECT REPORT", chapter_title_center))
    story.append(Spacer(1, 15))
    story.append(Paragraph("PLA-Based Rule Engine Designer", center_14_bold))
    story.append(Spacer(1, 55))

    story.append(Paragraph("Submitted by", center_12_regular))
    story.append(Spacer(1, 4))
    story.append(Paragraph("T THATCHINA MOORTHY", center_12_bold))
    story.append(Paragraph("920425243109", center_12_bold))
    story.append(Paragraph("Section B", center_12_bold))
    story.append(Spacer(1, 60))

    story.append(Paragraph("EC2201 & EC2202 – Digital System Design and Microprocessor", center_12_regular))
    story.append(Paragraph("October 2026", center_12_regular))
    story.append(Spacer(1, 50))

    # Evaluation table at bottom right
    eval_data = [
        [Paragraph("<font name='Times-Roman' size=11>Submission of Time (5)</font>", styles['Normal']), ""],
        [Paragraph("<font name='Times-Roman' size=11>Preparation (10)</font>", styles['Normal']), ""],
        [Paragraph("<font name='Times-Roman' size=11>Presentation (10)</font>", styles['Normal']), ""],
        [Paragraph("<font name='Times-Roman' size=11>Total</font>", styles['Normal']), ""]
    ]
    eval_table = Table(eval_data, colWidths=[150, 50], hAlign='RIGHT')
    eval_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(eval_table)
    story.append(PageBreak())

    # ==========================================
    # PAGE 2: FORMATTING GUIDE
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("Formatting Guide (delete this page before final submission)", chapter_title_style))
    story.append(Spacer(1, 12))

    bullets_p2 = [
        "Font: Times New Roman throughout the document.",
        "Body text size: 12 pt. Chapter titles: 16 pt bold. Section headings: 14 pt bold.",
        "Line spacing: 1.5 lines throughout.",
        "Paragraph spacing: 6 pt space after every paragraph.",
        "Margins: 1 inch on top/bottom/right, 1.25 inch on the left (for binding).",
        "Body text alignment: Justified.",
        "Page numbers: bottom-center, already set up in this template's footer.",
        "Do not change these settings — they match the evaluation checklist."
    ]
    for b in bullets_p2:
        story.append(Paragraph(f"●&nbsp;&nbsp;&nbsp;&nbsp;{b}", bullet_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 3: ABSTRACT
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("Abstract", chapter_title_style))
    story.append(Spacer(1, 12))

    abstract_text = (
        "Programmable Logic Arrays (PLAs) are foundational reconfigurable devices in digital systems, "
        "enabling flexible implementation of combinational logic in Sum-of-Products (SOP) form. This project presents "
        "the 'PLA-Based Rule Engine Designer', a modern CAD and simulation platform developed for the EC2201 "
        "Digital System Design curriculum. The platform allows engineers and students to define Boolean rules over four "
        "variables (A, B, C, D), automatically extracts unique product terms, configures fusible link crosspoints across "
        "inverted and non-inverted rails, and applies Quine-McCluskey tabular minimization to compute minimal prime "
        "implicants. In addition, an exhaustive 16-row truth table generator, an automated rule conflict and absorption "
        "redundancy scanner, and an interactive real-time digital hardware simulator with animated current flow and LED "
        "indicators are provided. A verification suite of 10 normal operational test cases and 5 edge/fault vectors achieves "
        "a 100% pass rate. The platform bridges the gap between switching theory and physical PLD circuit implementation, "
        "offering an end-to-end environment for digital logic synthesis, verification, and academic coursework demonstration."
    )
    story.append(Paragraph(abstract_text, body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 4: TABLE OF CONTENTS
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("Table of Contents", chapter_title_style))
    story.append(Spacer(1, 14))

    # Dot leader table for TOC
    toc_data = [
        ["Formatting Guide (delete this page before final submission)", "2"],
        ["Abstract", "3"],
        ["Table of Contents", "4"],
        ["1. Introduction", "5"],
        ["    1.1 Real-World Problem / Use Case", "5"],
        ["2. Problem Statement", "5"],
        ["3. Implementation", "5"],
        ["    3.1 Tools and Technologies Used", "5"],
        ["    3.2 Implementation Steps", "5"],
        ["    3.3 System Design / Architecture", "5"],
        ["4. Output / Screenshots", "5"],
        ["5. Conclusion and Future Scope", "6"],
        ["6. References", "6"],
        ["Submission Checklist", "7"]
    ]

    toc_table_data = []
    for title, page_str in toc_data:
        p_title = Paragraph(f"<font name='Times-Roman' size=12>{title}</font>", styles['Normal'])
        p_page = Paragraph(f"<font name='Times-Roman' size=12>{page_str}</font>", styles['Normal'])
        toc_table_data.append([p_title, p_page])

    toc_table = Table(toc_table_data, colWidths=[380, 50], hAlign='LEFT')
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # Page 5 styles
    p5_chapter_style = ParagraphStyle(
        'P5Chapter',
        fontName='Times-Bold',
        fontSize=15,
        leading=18,
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=3
    )

    p5_section_style = ParagraphStyle(
        'P5Section',
        fontName='Times-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=5,
        spaceAfter=2
    )

    p5_body_style = ParagraphStyle(
        'P5Body',
        fontName='Times-Roman',
        fontSize=11,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=3
    )

    p5_bullet_style = ParagraphStyle(
        'P5Bullet',
        fontName='Times-Roman',
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        leftIndent=18,
        spaceAfter=2
    )

    # ==========================================
    # PAGE 5: MAIN CONTENT (Sections 1 to 4)
    # ==========================================
    story.append(Paragraph("1. Introduction", p5_chapter_style))
    intro_text = (
        "Digital systems rely on Programmable Logic Devices (PLDs) to implement flexible combinational logic functions with "
        "compact silicon area. Unlike PROMs or PALs, Programmable Logic Arrays (PLAs) offer dual programmability in both AND "
        "and OR planes with product term sharing. The objective of this project is to develop a responsive, web-based PLA Rule "
        "Engine Designer that models, synthesizes, minimizes, and verifies digital logic circuits in real-time."
    )
    story.append(Paragraph(intro_text, p5_body_style))

    story.append(Paragraph("1.1 Real-World Problem / Use Case", p5_section_style))
    use_case_text = (
        "Designing digital logic control units, instruction decoders, and safety interlocks often suffers from rule conflicts, "
        "redundant terms, and excessive silicon footprint. This project addresses automated logic conflict detection, "
        "crosspoint matrix generation, and hardware simulation."
    )
    story.append(Paragraph(use_case_text, p5_body_style))

    story.append(Paragraph("2. Problem Statement", p5_chapter_style))
    ps_text = (
        "The project sets out to build an interactive PLA workbench that parses Boolean rules for variables A, B, C, D, "
        "compiles programmable AND/OR matrices, executes Quine-McCluskey minimization, detects rule conflicts, and validates "
        "circuits under active-high logic and static hazard immunity constraints."
    )
    story.append(Paragraph(ps_text, p5_body_style))

    story.append(Paragraph("3. Implementation", p5_chapter_style))
    story.append(Paragraph("3.1 Tools and Technologies Used", p5_section_style))
    tools_text = (
        "Frontend: HTML5, CSS3, JavaScript, Tailwind CSS, Chart.js, HTML5 Canvas API.<br/>"
        "Backend: Python 3.12, Flask, SQLite3, NumPy."
    )
    story.append(Paragraph(tools_text, p5_body_style))

    story.append(Paragraph("3.2 Implementation Steps", p5_section_style))
    steps = [
        "Step 1 — Logic Engine & Boolean Parser: AST parsing of inputs A, B, C, D with operators AND, OR, NOT, XOR.",
        "Step 2 — Matrix Compilation & Minimization: Synthesized AND/OR arrays with Quine-McCluskey tabular reduction.",
        "Step 3 — Simulator & Verification: Live rocker switches, Canvas current-flow animations, truth table, and test suite."
    ]
    for s in steps:
        story.append(Paragraph(f"●&nbsp;&nbsp;&nbsp;&nbsp;{s}", p5_bullet_style))

    story.append(Paragraph("3.3 System Design / Architecture", p5_section_style))
    arch_text = (
        "The system employs a 3-tier architecture: presentation layer (Canvas visualizer & UI), logic processing layer "
        "(Flask REST API, Quine-McCluskey engine), and persistence layer (SQLite database storing rules and test datasets)."
    )
    story.append(Paragraph(arch_text, p5_body_style))

    story.append(Paragraph("4. Output / Screenshots", p5_chapter_style))
    screenshots = [
        "Figure 4.1: Interactive PLA Hardware Simulator showing real-time switches, animated signal bus current flow, and LED indicators.",
        "Figure 4.2: Exhaustive 16-row Truth Table with active product term tracking and single-click CSV export.",
        "Figure 4.3: Automated Conflict Detection Scanner highlighting duplicate product terms and logic health score."
    ]
    for sc in screenshots:
        story.append(Paragraph(f"●&nbsp;&nbsp;&nbsp;&nbsp;{sc}", p5_bullet_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 6: CONCLUSION & REFERENCES
    # ==========================================
    story.append(Paragraph("5. Conclusion and Future Scope", chapter_title_style))
    conclusion_text = (
        "The PLA-Based Rule Engine Designer successfully models programmable logic arrays with high fidelity, verified by a 100% "
        "pass rate across 15 standard and edge test cases. The platform effectively demonstrates Quine-McCluskey minimization and "
        "rule conflict detection. Current constraints include a 4-variable input domain. Future extensions include multi-level logic "
        "synthesis using the Espresso heuristic algorithm, VHDL/Verilog RTL code generation, and automated FPGA bitstream export."
    )
    story.append(Paragraph(conclusion_text, body_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("6. References", chapter_title_style))
    references = [
        "[1] M. Morris Mano and Michael D. Ciletti, \"Digital Design: With an Introduction to the Verilog HDL,\" 5th Edition, Pearson Education, 2013.",
        "[2] Thomas L. Floyd, \"Digital Fundamentals,\" 11th Edition, Pearson Education, 2015.",
        "[3] Anna University, \"EC2201 & EC2202: Digital System Design and Microprocessor Syllabus,\" Anna University Regulation, 2021.",
        "[4] IEEE Computer Society, \"IEEE Standard VHDL Language Reference Manual,\" IEEE Std 1076-2008, 2009."
    ]
    for r in references:
        story.append(Paragraph(f"●&nbsp;&nbsp;&nbsp;&nbsp;{r}", bullet_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 7: SUBMISSION CHECKLIST
    # ==========================================
    story.append(Paragraph("Submission Checklist", chapter_title_style))
    story.append(Spacer(1, 14))

    checklist_items = [
        "PDF report uploaded on the Project Portal (Submit Work page)",
        "YouTube demo video link added (Unlisted visibility)",
        "GitHub repository link added, with README.md (https://github.com/thatchina2007-commits/PLA-Rule-Engine.git)",
        "Hardcopy of the report submitted to the department, if required"
    ]
    for item in checklist_items:
        story.append(Paragraph(f"●&nbsp;&nbsp;&nbsp;&nbsp;{item}", bullet_style))

    # Build PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")

if __name__ == '__main__':
    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "PLA_Rule_Engine_Mini_Project_Report.pdf"))
    create_pdf(out_file)
