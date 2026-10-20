"""
scripts/build_full_blackbook.py
Master builder script for the 65+ page B.Tech Project Blackbook Report.
Symbiosis Institute of Technology (SIT), Pune.
Department of Computer Science & Engineering.
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
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

NS_W = nsdecls("w")

def main():
    print("=================================================================")
    print("STARTING COMPLETE B.TECH PROJECT BLACKBOOK BUILDER (TARGET: 65+ PAGES)")
    print("=================================================================")
    
    os.makedirs("paper", exist_ok=True)
    os.makedirs("/Users/omikashrestha/Desktop", exist_ok=True)
    
    from scripts.blackbook_html_builder import generate_master_html
    from scripts.blackbook_docx_builder import generate_master_docx
    
    html_str = generate_master_html()
    html_path = "paper/BTech_Project_Report_Blackbook.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    print(f"Master HTML written: {html_path} ({len(html_str):,} bytes)")
    
    # Render PDF using Google Chrome Headless
    pdf_path = "paper/BTech_Project_Report_Blackbook.pdf"
    desktop_pdf = "/Users/omikashrestha/Desktop/BTech_Project_Report_Blackbook.pdf"
    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    cmd = [
        chrome_bin,
        "--headless",
        f"--print-to-pdf={pdf_path}",
        "--no-pdf-header-footer",
        html_path
    ]
    print("Rendering PDF via Google Chrome Headless...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Chrome error:", res.stderr)
    else:
        print(f"Successfully generated PDF: {pdf_path}")
        shutil.copy2(pdf_path, desktop_pdf)
        print(f"Copied PDF to Desktop: {desktop_pdf}")
        
        # Verify page count
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        print("-----------------------------------------------------------------")
        print(f"VERIFIED TOTAL PDF PAGE COUNT: {total_pages} PAGES")
        print("-----------------------------------------------------------------")
        if total_pages >= 60:
            print(f"SUCCESS: Page count {total_pages} meets and exceeds the minimum 60 pages requirement!")
        else:
            print(f"WARNING: Page count {total_pages} is below 60 pages! Need expansion.")
            
    # Generate Word Document (.docx)
    docx_path = "paper/BTech_Project_Report_Blackbook.docx"
    desktop_docx = "/Users/omikashrestha/Desktop/BTech_Project_Report_Blackbook.docx"
    print("Generating editable Word DOCX document...")
    generate_master_docx(docx_path)
    shutil.copy2(docx_path, desktop_docx)
    print(f"Copied DOCX to Desktop: {desktop_docx}")

if __name__ == "__main__":
    main()
