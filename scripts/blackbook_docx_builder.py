"""
scripts/blackbook_docx_builder.py
Constructs the complete, submission-ready B.Tech Project Blackbook (.docx)
matching Symbiosis Institute of Technology guidelines and the sample PDF.
"""

import os
import sys
import re

# Ensure current directory is on python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

import lxml.html
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

NS_W = nsdecls("w")

def sanitize_xml(s):
    """Strips characters that are invalid in XML 1.0 (such as bell 0x07, backspace 0x08, form-feed 0x0C)."""
    if not s:
        return ""
    # Map common regex escape artifacts if present
    s = s.replace('\x08', r'\b').replace('\x0c', r'\f').replace('\x07', r'\a')
    # Filter remaining control characters
    return re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', s)

def set_cell_shading(cell, color_hex):
    shading_xml = f'<w:shd {NS_W} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_table_borders(table, border_color="333333"):
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(f'''
        <w:tblBorders {NS_W}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>
            <w:left w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders_xml)

def set_cell_margins(cell, top=70, bottom=70, left=90, right=90):
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

def add_runs_from_element(p, element, default_font="Times New Roman", default_size=12, default_bold=False, default_italic=False, default_color=None):
    """Recursively processes child tags (strong, em, code, text) and appends runs."""
    def process_node(node, is_bold=False, is_italic=False, is_code=False):
        # Text before children
        if node.text:
            text = node.text
            if not is_code:
                text = re.sub(r'\s+', ' ', text)
            clean_text = sanitize_xml(text)
            if clean_text:
                run = p.add_run(clean_text)
                run.font.name = 'Courier New' if is_code else default_font
                run.font.size = Pt(default_size - 1.5 if is_code else default_size)
                run.bold = is_bold or default_bold
                run.italic = is_italic or default_italic
                if default_color:
                    run.font.color.rgb = default_color

        for child in node:
            tag = child.tag
            if not isinstance(tag, str):
                continue
            c_bold = is_bold or (tag in ['strong', 'b'])
            c_italic = is_italic or (tag in ['em', 'i'])
            c_code = is_code or (tag in ['code', 'tt'])
            process_node(child, c_bold, c_italic, c_code)

            # Tail text after child tag
            if child.tail:
                tail = child.tail
                if not is_code:
                    tail = re.sub(r'\s+', ' ', tail)
                clean_tail = sanitize_xml(tail)
                if clean_tail:
                    run = p.add_run(clean_tail)
                    run.font.name = 'Courier New' if is_code else default_font
                    run.font.size = Pt(default_size - 1.5 if is_code else default_size)
                    run.bold = is_bold or default_bold
                    run.italic = is_italic or default_italic
                    if default_color:
                        run.font.color.rgb = default_color

    process_node(element, default_bold, default_italic, element.tag in ['code', 'pre'])

def generate_master_docx(docx_out_path):
    print("Building complete Master DOCX Blackbook...")
    from scripts.blackbook_html_builder import generate_master_html
    html_content = generate_master_html()

    tree = lxml.html.fromstring(html_content)
    body = tree.body

    doc = Document()

    # Configure A4 Paper: 8.27" x 11.69"
    # Margins: Left = 1.3" (binding), Top = 1.0", Right = 1.0", Bottom = 1.0"
    for s in doc.sections:
        s.page_width = Inches(8.27)
        s.page_height = Inches(11.69)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.3)
        s.right_margin = Inches(1.0)

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)

    def handle_p(p_elem):
        cls = p_elem.get('class', '')
        style_str = p_elem.get('style', '')
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        
        # Alignment
        if 'text-align: center' in style_str:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif 'text-align: right' in style_str:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # Indent
        if 'no-indent' in cls or 'text-indent: 0' in style_str:
            p.paragraph_format.first_line_indent = Inches(0)
        elif 'text-indent: -0.25in' in style_str:
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.first_line_indent = Inches(-0.25)
        else:
            p.paragraph_format.first_line_indent = Inches(0.25)

        add_runs_from_element(p, p_elem, default_size=12)

    def handle_table(table_elem):
        # Extract rows and cells
        rows_data = []
        for tr in table_elem.xpath('.//tr'):
            cell_nodes = tr.xpath('./th | ./td')
            row_items = []
            for cell_node in cell_nodes:
                is_header = (cell_node.tag == 'th')
                colspan = int(cell_node.get('colspan', 1))
                style = cell_node.get('style', '')
                align = WD_ALIGN_PARAGRAPH.CENTER if is_header or 'text-align: center' in style else (
                    WD_ALIGN_PARAGRAPH.RIGHT if 'text-align: right' in style else WD_ALIGN_PARAGRAPH.LEFT
                )
                row_items.append({
                    'node': cell_node,
                    'is_header': is_header,
                    'colspan': colspan,
                    'align': align,
                    'style': style
                })
            if row_items:
                rows_data.append(row_items)

        if not rows_data:
            return

        # Determine column count
        col_count = max(sum(c['colspan'] for c in r) for r in rows_data)
        table = doc.add_table(rows=len(rows_data), cols=col_count)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table)

        for row_idx, r_items in enumerate(rows_data):
            col_idx = 0
            for item in r_items:
                if col_idx >= col_count:
                    break
                cell = table.cell(row_idx, col_idx)
                # Cell padding
                set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

                # Background shading
                if item['is_header'] or 'background-color' in item['style']:
                    if '#1B4F72' in item['style']:
                        set_cell_shading(cell, "1B4F72")
                    elif '#EAFAF1' in item['style']:
                        set_cell_shading(cell, "EAFAF1")
                    else:
                        set_cell_shading(cell, "F2F4F7")

                p = cell.paragraphs[0]
                p.alignment = item['align']
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.first_line_indent = Inches(0)

                # Text color if white header
                txt_color = RGBColor(255, 255, 255) if '#1B4F72' in item['style'] else None
                add_runs_from_element(p, item['node'], default_size=9.5, default_bold=item['is_header'], default_color=txt_color)

                col_idx += item['colspan']

        # Add space after table
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(0)
        p_after.paragraph_format.space_after = Pt(6)
        p_after.paragraph_format.line_spacing = 1.0

    def handle_figure_box(fig_elem):
        imgs = fig_elem.xpath('.//img')
        captions = fig_elem.xpath('.//div[contains(@class, "figure-caption")]')
        
        for img in imgs:
            src = img.get('src', '')
            if os.path.exists(src):
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(10)
                p_img.paragraph_format.space_after = Pt(4)
                p_img.paragraph_format.first_line_indent = Inches(0)
                # Scale appropriately to fit 5.8 inches width
                p_img.add_run().add_picture(src, width=Inches(5.7))

        for cap in captions:
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(4)
            p_cap.paragraph_format.space_after = Pt(12)
            p_cap.paragraph_format.first_line_indent = Inches(0)
            clean_cap = sanitize_xml(cap.text_content().strip())
            run = p_cap.add_run(clean_cap)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10.5)

    def handle_code_block(code_elem):
        text = code_elem.text_content()
        clean_text = sanitize_xml(text)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.first_line_indent = Inches(0)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(clean_text)
        run.font.name = 'Courier New'
        run.font.size = Pt(9.0)

    def handle_toc_line(toc_elem):
        cls = toc_elem.get('class', '')
        title_nodes = toc_elem.xpath('.//span[contains(@class, "toc-title")]')
        page_nodes = toc_elem.xpath('.//span[contains(@class, "toc-page")]')
        
        title_text = sanitize_xml(title_nodes[0].text_content().strip()) if title_nodes else ""
        page_text = sanitize_xml(page_nodes[0].text_content().strip()) if page_nodes else ""
        
        if not title_text and not page_text:
            return

        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Inches(0)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(5.95), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        
        is_chapter = 'chapter' in cls
        is_prelim = 'prelim' in cls
        is_sec = 'sec' in cls
        is_subsec = 'subsec' in cls
        
        if is_chapter:
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0)
            p.paragraph_format.line_spacing = 1.15
            run_t = p.add_run(title_text)
            run_t.bold = True
            run_t.font.name = 'Times New Roman'
            run_t.font.size = Pt(11)
            
            run_p = p.add_run(f"\t{page_text}")
            run_p.bold = True
            run_p.font.name = 'Times New Roman'
            run_p.font.size = Pt(11)
        elif is_sec:
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.line_spacing = 1.15
            run_t = p.add_run(title_text)
            run_t.bold = False
            run_t.font.name = 'Times New Roman'
            run_t.font.size = Pt(10.5)
            
            run_p = p.add_run(f"\t{page_text}")
            run_p.bold = False
            run_p.font.name = 'Times New Roman'
            run_p.font.size = Pt(10.5)
        elif is_subsec:
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.left_indent = Inches(0.45)
            p.paragraph_format.line_spacing = 1.15
            run_t = p.add_run(title_text)
            run_t.bold = False
            run_t.font.name = 'Times New Roman'
            run_t.font.size = Pt(10)
            
            run_p = p.add_run(f"\t{page_text}")
            run_p.bold = False
            run_p.font.name = 'Times New Roman'
            run_p.font.size = Pt(10)
        elif is_prelim:
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0)
            p.paragraph_format.line_spacing = 1.15
            run_t = p.add_run(title_text)
            run_t.bold = True
            run_t.font.name = 'Times New Roman'
            run_t.font.size = Pt(10.5)
            
            run_p = p.add_run(f"\t{page_text}")
            run_p.bold = True
            run_p.font.name = 'Times New Roman'
            run_p.font.size = Pt(10.5)
        else:
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0)
            p.paragraph_format.line_spacing = 1.15
            run_t = p.add_run(title_text)
            run_t.bold = False
            run_t.font.name = 'Times New Roman'
            run_t.font.size = Pt(10.5)
            
            run_p = p.add_run(f"\t{page_text}")
            run_p.bold = False
            run_p.font.name = 'Times New Roman'
            run_p.font.size = Pt(10.5)

    # Process all children of body
    for child in body:
        tag = child.tag
        cls = child.get('class', '')

        if not isinstance(tag, str):
            continue

        if 'page-break' in cls:
            doc.add_page_break()
            continue

        if 'toc-line' in cls:
            handle_toc_line(child)
            continue

        if tag == 'div' and any(c in cls for c in ['toc-container', 'lot-container', 'lof-container']):
            for line in child.xpath('.//div[contains(@class, "toc-line")]'):
                handle_toc_line(line)
            continue

        if tag == 'h1':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(18)
            p.paragraph_format.first_line_indent = Inches(0)
            clean_title = sanitize_xml(child.text_content().strip())
            run = p.add_run(clean_title)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(16)
            continue

        if tag == 'h2':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.first_line_indent = Inches(0)
            clean_sec = sanitize_xml(child.text_content().strip())
            run = p.add_run(clean_sec)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            continue

        if tag == 'h3':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.first_line_indent = Inches(0)
            clean_subsec = sanitize_xml(child.text_content().strip())
            run = p.add_run(clean_subsec)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            continue

        if tag == 'h4':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.first_line_indent = Inches(0)
            clean_h4 = sanitize_xml(child.text_content().strip())
            run = p.add_run(clean_h4)
            run.bold = True
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)
            continue

        if tag == 'div' and 'table-caption' in cls:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.first_line_indent = Inches(0)
            clean_cap = sanitize_xml(child.text_content().strip())
            run = p.add_run(clean_cap)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10.5)
            continue

        if tag == 'div' and 'figure-box' in cls:
            handle_figure_box(child)
            continue

        if tag == 'div' and 'code-block' in cls:
            handle_code_block(child)
            continue

        if tag == 'table':
            handle_table(child)
            continue

        if tag == 'p':
            handle_p(child)
            continue

        if tag == 'ul':
            for li in child.xpath('.//li'):
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.line_spacing = 1.3
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.first_line_indent = Inches(-0.2)
                p.paragraph_format.left_indent = Inches(0.4)
                add_runs_from_element(p, li, default_size=11)
            continue

        if tag == 'div':
            # Could be preliminary wrappers (cover-page, cert-header, cert-title)
            if 'cert-title' in cls:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(20)
                p.paragraph_format.space_after = Pt(16)
                p.paragraph_format.first_line_indent = Inches(0)
                clean_title = sanitize_xml(child.text_content().strip())
                run = p.add_run(clean_title)
                run.bold = True
                run.font.name = 'Times New Roman'
                run.font.size = Pt(15)
                continue

            # Nested elements traversal for generic divs
            for sub in child:
                sub_cls = sub.get('class', '')
                if 'toc-line' in sub_cls:
                    handle_toc_line(sub)
                elif sub.tag == 'p':
                    handle_p(sub)
                elif sub.tag == 'table':
                    handle_table(sub)
                elif sub.tag == 'div' and 'figure-box' in sub_cls:
                    handle_figure_box(sub)
                elif sub.tag == 'div' and 'code-block' in sub_cls:
                    handle_code_block(sub)
                elif sub.tag == 'div' and 'cert-title' in sub_cls:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(20)
                    p.paragraph_format.space_after = Pt(16)
                    p.paragraph_format.first_line_indent = Inches(0)
                    clean_sub = sanitize_xml(sub.text_content().strip())
                    run = p.add_run(clean_sub)
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(15)
                elif sub.tag == 'h1':
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(18)
                    p.paragraph_format.space_after = Pt(18)
                    p.paragraph_format.first_line_indent = Inches(0)
                    clean_h = sanitize_xml(sub.text_content().strip())
                    run = p.add_run(clean_h)
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(16)
                elif sub.tag == 'h2':
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.space_before = Pt(16)
                    p.paragraph_format.space_after = Pt(6)
                    p.paragraph_format.first_line_indent = Inches(0)
                    clean_h = sanitize_xml(sub.text_content().strip())
                    run = p.add_run(clean_h)
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                else:
                    txt = sub.text_content().strip()
                    if txt:
                        p = doc.add_paragraph()
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if 'center' in sub.get('style', '') else WD_ALIGN_PARAGRAPH.JUSTIFY
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.line_spacing = 1.3
                        p.paragraph_format.first_line_indent = Inches(0)
                        add_runs_from_element(p, sub, default_size=11)
            continue

    # Save document
    doc.save(docx_out_path)
    print(f"Successfully generated Master Word Document (.docx): {docx_out_path} ({os.path.getsize(docx_out_path):,} bytes)")

if __name__ == "__main__":
    out = "paper/BTech_Project_Report_Blackbook.docx"
    generate_master_docx(out)
