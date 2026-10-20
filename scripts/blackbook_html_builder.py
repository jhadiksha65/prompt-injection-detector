"""
scripts/blackbook_html_builder.py
Generates the comprehensive, highly detailed HTML document (target: 65+ pages in A4 print)
for Symbiosis Institute of Technology B.Tech Project Blackbook.
"""

import os

def generate_master_html():
    cwd = os.path.abspath(os.getcwd())
    logo_path = os.path.join(cwd, "assets/sit_template/image_0.png")
    fig_arch_path = os.path.join(cwd, "figures/pipeline_architecture.png")
    fig_dfd_path = os.path.join(cwd, "figures/report/fig_dfd.png")
    fig_seq_path = os.path.join(cwd, "figures/report/fig_sequence.png")
    fig_er_path = os.path.join(cwd, "figures/report/fig_er.png")
    fig_cm_path = os.path.join(cwd, "figures/report/fig_confusion_matrix.png")
    fig_gantt_path = os.path.join(cwd, "figures/report/fig_gantt.png")
    scr_analyzer = os.path.join(cwd, "figures/report/screenshot_analyzer.png")
    scr_dashboard = os.path.join(cwd, "figures/report/screenshot_dashboard.png")
    scr_deploy = os.path.join(cwd, "figures/report/screenshot_deploy.png")
    scr_ext = os.path.join(cwd, "figures/report/screenshot_external_gateway.png")

    # Let's import the modular chapters generator
    from scripts.chapters.prelims import get_prelims_html
    from scripts.chapters.ch1_intro import get_ch1_html
    from scripts.chapters.ch2_lit_review import get_ch2_html
    from scripts.chapters.ch3_srs import get_ch3_html
    from scripts.chapters.ch4_methodology import get_ch4_html
    from scripts.chapters.ch5_results import get_ch5_html
    from scripts.chapters.ch6_conclusion import get_ch6_html
    from scripts.chapters.references_appendices import get_ref_app_html

    html_head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>B.Tech Project Blackbook - Prompt Security for Organizational LLMs</title>
<style>
@page {{
    size: A4 portrait;
    margin: 1.0in 1.0in 1.0in 1.3in;
    @bottom-center {{
        content: counter(page);
        font-family: 'Times New Roman', serif;
        font-size: 10pt;
    }}
}}

body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #000000;
    text-align: justify;
    margin: 0;
    padding: 0;
}}

.page-break {{
    page-break-after: always;
    break-after: page;
}}

h1.chapter-title {{
    font-size: 16pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    margin-top: 15pt;
    margin-bottom: 20pt;
    line-height: 1.3;
}}

h2.section-title {{
    font-size: 14pt;
    font-weight: bold;
    margin-top: 18pt;
    margin-bottom: 8pt;
    line-height: 1.3;
    text-align: left;
}}

h3.subsection-title {{
    font-size: 12pt;
    font-weight: bold;
    margin-top: 14pt;
    margin-bottom: 6pt;
    line-height: 1.3;
    text-align: left;
}}

h4.subsubsection-title {{
    font-size: 12pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 10pt;
    margin-bottom: 4pt;
    line-height: 1.3;
    text-align: left;
}}

p {{
    margin-top: 0;
    margin-bottom: 8pt;
    text-indent: 0.25in;
}}

p.no-indent {{
    text-indent: 0;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10pt;
    margin-bottom: 12pt;
    font-size: 9.5pt;
    line-height: 1.3;
}}

table, th, td {{
    border: 1px solid #333333;
}}

th {{
    background-color: #F2F4F7;
    font-weight: bold;
    text-align: center;
    padding: 6pt 5pt;
}}

td {{
    padding: 5pt;
    vertical-align: top;
}}

.table-caption {{
    font-weight: bold;
    font-size: 10.5pt;
    text-align: left;
    margin-top: 14pt;
    margin-bottom: 4pt;
    text-indent: 0;
}}

.figure-box {{
    text-align: center;
    margin-top: 14pt;
    margin-bottom: 14pt;
}}

.figure-box img {{
    max-width: 95%;
    height: auto;
    border: 1px solid #DDDDDD;
}}

.figure-caption {{
    font-weight: bold;
    font-size: 10.5pt;
    text-align: center;
    margin-top: 6pt;
    margin-bottom: 12pt;
    text-indent: 0;
}}

.code-block {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 9.0pt;
    background-color: #F8F9FA;
    border: 1px solid #E5E7EB;
    padding: 8pt;
    margin-top: 8pt;
    margin-bottom: 10pt;
    white-space: pre-wrap;
    line-height: 1.25;
}}

.cover-page {{
    text-align: center;
    padding-top: 0.1in;
}}

.cover-title {{
    font-size: 16pt;
    font-weight: bold;
    margin-top: 15pt;
    margin-bottom: 15pt;
    line-height: 1.3;
}}

.cover-sub {{
    font-size: 12pt;
    margin-bottom: 10pt;
    line-height: 1.4;
}}

.cover-degree {{
    font-size: 13pt;
    font-weight: bold;
    margin-top: 15pt;
    margin-bottom: 15pt;
}}

.cover-table {{
    width: 85%;
    margin: 15pt auto;
    border: 1px solid #333;
}}

.cover-table td {{
    padding: 6pt 10pt;
    font-size: 11pt;
}}

.cover-logo {{
    width: 3.8in;
    margin-top: 20pt;
    margin-bottom: 8pt;
}}

.cert-header {{
    text-align: center;
    margin-bottom: 15pt;
}}

.cert-title {{
    font-size: 15pt;
    font-weight: bold;
    text-align: center;
    margin-top: 15pt;
    margin-bottom: 20pt;
    letter-spacing: 1px;
}}

.signature-table {{
    width: 100%;
    border: none;
    margin-top: 50pt;
}}

.signature-table td {{
    border: none;
    text-align: center;
    padding: 10pt;
    font-size: 11pt;
    font-weight: bold;
    vertical-align: bottom;
}}

/* Text-based Table of Contents with Dot Leaders */
.toc-container, .lot-container, .lof-container {{
    width: 100%;
    margin-top: 15pt;
    margin-bottom: 15pt;
    font-family: 'Times New Roman', Times, serif;
}}

.toc-line {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 4pt;
    font-size: 11pt;
    line-height: 1.35;
    page-break-inside: avoid;
}}

.toc-line.chapter {{
    font-weight: bold;
    font-size: 11.5pt;
    margin-top: 9pt;
    margin-bottom: 4pt;
}}

.toc-line.sec {{
    padding-left: 20pt;
    font-size: 10.5pt;
}}

.toc-line.subsec {{
    padding-left: 36pt;
    font-size: 10pt;
}}

.toc-line.prelim {{
    font-weight: bold;
}}

.toc-title {{
    flex-shrink: 1;
    text-align: left;
}}

.toc-dots {{
    flex-grow: 1;
    border-bottom: 1.5px dotted #444444;
    margin: 0 6pt 3pt 6pt;
    min-width: 15pt;
    height: 1px;
}}

.toc-page {{
    flex-shrink: 0;
    min-width: 25pt;
    text-align: right;
    font-weight: normal;
}}

.toc-line.chapter .toc-page, .toc-line.prelim .toc-page {{
    font-weight: bold;
}}
</style>
</head>
<body>
"""

    parts = [
        html_head,
        get_prelims_html(logo_path),
        get_ch1_html(),
        get_ch2_html(),
        get_ch3_html(fig_gantt_path),
        get_ch4_html(fig_arch_path, fig_dfd_path, fig_seq_path, fig_er_path, scr_analyzer, scr_deploy, scr_ext, scr_dashboard),
        get_ch5_html(fig_cm_path),
        get_ch6_html(),
        get_ref_app_html(),
        "</body></html>"
    ]

    return "\n".join(parts)
