"""
scripts/build_btech_blackbook.py
Generates the complete, submission-ready B.Tech Project Blackbook Report (60+ pages)
for Symbiosis Institute of Technology (SIT), Pune, Department of Computer Science & Engineering.

Title: PROMPT SECURITY FOR ORGANIZATIONAL LARGE LANGUAGE MODELS: A DUAL-LAYER PROMPT INJECTION DETECTION AND RESPONSE SECURITY FRAMEWORK
Academic Year: AY 2026-27

Outputs:
- paper/BTech_Project_Report_Blackbook.docx
- paper/BTech_Project_Report_Blackbook.pdf
- /Users/omikashrestha/Desktop/BTech_Project_Report_Blackbook.docx
- /Users/omikashrestha/Desktop/BTech_Project_Report_Blackbook.pdf
"""

import os
import sys
import shutil
import subprocess
import pypdf
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

NS_W = nsdecls("w")

def set_cell_shading(cell, color_hex):
    shading_xml = f'<w:shd {NS_W} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_table_borders(table, rule_color="2C3E50"):
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(f'''
        <w:tblBorders {NS_W}>
            <w:top w:val="single" w:sz="10" w:space="0" w:color="{rule_color}"/>
            <w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            <w:bottom w:val="single" w:sz="10" w:space="0" w:color="{rule_color}"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="DDDDDD"/>
            <w:insideV w:val="single" w:sz="4" w:space="0" w:color="EEEEEE"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders_xml)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {NS_W}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_table_header(table, col_widths, headers, bg_hex="1B4F72", text_color=(255, 255, 255)):
    row = table.rows[0]
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {NS_W}/>'))
    for i, title in enumerate(headers):
        cell = row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_shading(cell, bg_hex)
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(title)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(*text_color)

def add_table_row(table, col_widths, values, is_even=False, aligns=None, font_size=9.0):
    row = table.add_row()
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {NS_W}/>'))
    bg_hex = "F8F9FA" if is_even else "FFFFFF"
    for i, val in enumerate(values):
        cell = row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_shading(cell, bg_hex)
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        align = aligns[i] if aligns and i < len(aligns) else WD_ALIGN_PARAGRAPH.LEFT
        p.alignment = align
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        lines = str(val).split("\n")
        for j, line in enumerate(lines):
            if j > 0:
                p = cell.add_paragraph()
                p.alignment = align
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(1)
            if "**" in line:
                parts = line.split("**")
                for k, part in enumerate(parts):
                    run = p.add_run(part)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(font_size)
                    if k % 2 == 1:
                        run.bold = True
            else:
                run = p.add_run(line)
                run.font.name = "Times New Roman"
                run.font.size = Pt(font_size)

def configure_btech_margins(section):
    # A4 Size: 8.27 x 11.69 inches
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    # Binding margin Left = 1.3 in, Right = 1.0 in, Top = 1.0 in, Bottom = 1.0 in
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.3)
    section.right_margin = Inches(1.0)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)

print("Report generator framework initialized.")
