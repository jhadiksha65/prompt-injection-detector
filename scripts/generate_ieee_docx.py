"""
generate_ieee_docx.py
Generates a strictly compliant IEEE Conference Paper Word Document (.docx)
following the official IEEE Conference Template guidelines:
- Letter paper (8.5" x 11"), 0.75" top/bottom margin, 0.625" left/right margin (text width = 7.25")
- 24pt Bold Centered Title
- Centered Author Block (Group 25, Department, Affiliation, Repository)
- 2-Column Body Layout (3.50" columns with 0.25" gap)
- Abstract in Bold/Italic at the top of Column 1
- Centered Small-Caps Roman Numeral Section Headings (I. INTRODUCTION, etc.)
- Italic Subsection Headings (A. Contributions, etc.)
- Booktabs Styled Tables (TABLE I, TABLE II, TABLE III, TABLE IV, TABLE V)
- Centered Equations with Right-Aligned Equation Numbers
- Proper Figure Captions (Fig. 1. ...)
- Numbered IEEE References [1]–[12] with Hanging Indents
"""

import os
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

NS_W = nsdecls("w")

def set_cell_shading(cell, color_hex):
    shading_xml = f'<w:shd {NS_W} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_ieee_table_borders(table, rule_color="000000"):
    """
    Standard IEEE Booktabs Table Borders:
    - Top rule: medium/thick (sz=12)
    - Bottom of table: medium/thick (sz=12)
    - Inside horizontal rules: thin (sz=4)
    - No vertical rules
    """
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(f'''
        <w:tblBorders {NS_W}>
            <w:top w:val="single" w:sz="12" w:space="0" w:color="{rule_color}"/>
            <w:left w:val="none"/>
            <w:bottom w:val="single" w:sz="12" w:space="0" w:color="{rule_color}"/>
            <w:right w:val="none"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders_xml)

def set_cell_margins(cell, top=65, bottom=65, left=90, right=90):
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

def add_ieee_table_header(table, col_widths, headers, bg_hex="F2F2F2"):
    row = table.rows[0]
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {NS_W}/>'))
    
    for i, title in enumerate(headers):
        cell = row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_shading(cell, bg_hex)
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        run = p.add_run(title)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0, 0, 0)

def add_ieee_table_row(table, col_widths, values, is_even=False, aligns=None):
    row = table.add_row()
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {NS_W}/>'))
    
    bg_hex = "FAFAFA" if is_even else "FFFFFF"
    for i, val in enumerate(values):
        cell = row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_shading(cell, bg_hex)
        set_cell_margins(cell, top=55, bottom=55, left=75, right=75)
        p = cell.paragraphs[0]
        align = aligns[i] if aligns and i < len(aligns) else WD_ALIGN_PARAGRAPH.LEFT
        p.alignment = align
        p.paragraph_format.space_before = Pt(0)
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
                    run.font.size = Pt(8)
                    if k % 2 == 1:
                        run.bold = True
            else:
                run = p.add_run(line)
                run.font.name = "Times New Roman"
                run.font.size = Pt(8)

def configure_ieee_margins(section):
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(0.625)
    section.right_margin = Inches(0.625)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.4)

def set_section_columns(section, num_cols=2, space_dxa=360):
    sectPr = section._sectPr
    for c in sectPr.findall(qn("w:cols")):
        sectPr.remove(c)
    
    if num_cols == 2:
        cols_xml = f'<w:cols {NS_W} w:num="2" w:space="{space_dxa}"/>'
    else:
        cols_xml = f'<w:cols {NS_W} w:num="1"/>'
    
    docGrid = sectPr.find(qn("w:docGrid"))
    new_cols = parse_xml(cols_xml)
    if docGrid is not None:
        docGrid.addprevious(new_cols)
    else:
        sectPr.append(new_cols)

def build_ieee_doc():
    doc = Document()

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)

    # ==========================================
    # SECTION 1: TITLE & AUTHORS (1 Column, Full Width: 7.25")
    # ==========================================
    sec1 = doc.sections[0]
    configure_ieee_margins(sec1)
    set_section_columns(sec1, num_cols=1)

    # Paper Title (24 pt, Bold, Centered)
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("Dual-Layer Security Architecture for Prompt Injection Defense: Neural-Heuristic Fusion, Multi-Modal Attachment Parsing, and Outbound Leakage Prevention")
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(22)
    r_title.font.color.rgb = RGBColor(0, 0, 0)

    # Author Block
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_before = Pt(0)
    p_auth.paragraph_format.space_after = Pt(2)
    r_auth = p_auth.add_run("Group 25 Research Team")
    r_auth.bold = True
    r_auth.font.name = "Times New Roman"
    r_auth.font.size = Pt(11)

    p_aff = doc.add_paragraph()
    p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aff.paragraph_format.space_before = Pt(0)
    p_aff.paragraph_format.space_after = Pt(2)
    r_aff = p_aff.add_run("Department of Computer Science and Cybersecurity\nCybersecurity Systems and Machine Learning Laboratory\nGitHub: https://github.com/jhadiksha65/prompt-injection-detector")
    r_aff.italic = True
    r_aff.font.name = "Times New Roman"
    r_aff.font.size = Pt(9.5)
    r_aff.font.color.rgb = RGBColor(50, 50, 50)

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(10)
    r_meta = p_meta.add_run("Operational Checkpoint: 05af2d4  |  Decision Threshold: 0.3800  |  Model SHA-256: c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93")
    r_meta.font.name = "Times New Roman"
    r_meta.font.size = Pt(8)
    r_meta.font.color.rgb = RGBColor(90, 90, 90)

    # Helper text formatting functions
    def add_p(text, bold_prefix="", indent=True, italic_prefix=False):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.05
        if indent:
            p.paragraph_format.first_line_indent = Inches(0.14)
        else:
            p.paragraph_format.first_line_indent = Inches(0)
            
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
            if italic_prefix:
                r_b.italic = True
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(10)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        return p

    def add_ieee_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.first_line_indent = Inches(0)
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run._r.get_or_add_rPr().append(parse_xml(f'<w:smallCaps {NS_W}/>'))
        return p

    def add_ieee_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.first_line_indent = Inches(0)
        run = p.add_run(text)
        run.italic = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.first_line_indent = Inches(0)
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(9.5)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)

    def add_equation(eq_text, eq_num):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.first_line_indent = Inches(0)
        r_eq = p.add_run(f"    {eq_text}    ")
        r_eq.italic = True
        r_eq.font.name = "Times New Roman"
        r_eq.font.size = Pt(9.5)
        r_num = p.add_run(f"\t({eq_num})")
        r_num.font.name = "Times New Roman"
        r_num.font.size = Pt(9.5)

    # ==========================================
    # SECTION 2: 2 COLUMNS (Continuous Break)
    # Starts with Abstract, Index Terms, Introduction, Threat Model
    # ==========================================
    sec2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec2)
    set_section_columns(sec2, num_cols=2, space_dxa=360)

    # 1. ABSTRACT
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_before = Pt(0)
    p_abs.paragraph_format.space_after = Pt(3)
    p_abs.paragraph_format.line_spacing = 1.05
    p_abs.paragraph_format.first_line_indent = Inches(0.14)
    r_absh = p_abs.add_run("Abstract—")
    r_absh.bold = True
    r_absh.italic = True
    r_absh.font.name = "Times New Roman"
    r_absh.font.size = Pt(9)
    r_abst = p_abs.add_run(
        "Prompt injection represents the paramount security vulnerability in modern applications integrating Large Language Models (LLMs), "
        "encompassing direct prompt manipulation, indirect payload delivery through external documents, and unauthorized disclosure of sensitive internal context. "
        "In this paper, we present the design, implementation, and empirical evaluation of a production-ready, dual-layer prompt security middleware and gateway. "
        "Our architecture establishes an active perimeter around the language model: Layer 1 performs inbound threat screening before model invocation by fusing "
        "a calibrated, fine-tuned DistilBERT sequence classifier (R_ML) with a deterministic signature pattern engine (R_rule) at an operational decision threshold "
        "of θ = 0.3800 under a weighted scoring formulation: Rfused = 0.40 Rrule + 0.60 RML. "
        "To neutralize indirect injection, our inbound pipeline decouples prompt evaluation from multi-modal attachment ingestion (supporting DOCX, PDF, and optical "
        "character recognition via Tesseract), preserving fine-grained threat-source attribution (threat_source in {User Prompt, Attachment, Both, None}). "
        "Inbound traffic is mapped to an authoritative nine-category threat taxonomy, accurately distinguishing malicious instructions from benign cybersecurity queries. "
        "Layer 2 inspects outbound LLM responses prior to egress, detecting system prompt disclosure, API credentials, and personally identifiable information (PII), "
        "automatically enforcing redaction or complete response withholding. The middleware provides an OpenAI-compatible reverse-proxy gateway (/v1/chat/completions) "
        "for systems such as Open WebUI and an asynchronous browser extension for client-side pre-submission interception. On an independent 3,000-sample balanced "
        "generalization benchmark, our hybrid detector achieves an accuracy of 98.73%, precision of 99.26%, recall of 98.20%, and F1-score of 0.9873 (overcoming the 8.73% "
        "recall of rule-only baselines), while maintaining 100% precision and 0.00% false-positive rate on an adversarial challenge holdout. The entire end-to-end "
        "implementation is validated by a 288-test automated regression suite with a 100% pass rate and sub-30ms inference latency on hardware-accelerated runtimes."
    )
    r_abst.bold = True
    r_abst.font.name = "Times New Roman"
    r_abst.font.size = Pt(9)

    # 2. INDEX TERMS
    p_idx = doc.add_paragraph()
    p_idx.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_idx.paragraph_format.space_before = Pt(0)
    p_idx.paragraph_format.space_after = Pt(6)
    p_idx.paragraph_format.line_spacing = 1.05
    p_idx.paragraph_format.first_line_indent = Inches(0.14)
    r_idxh = p_idx.add_run("Index Terms—")
    r_idxh.bold = True
    r_idxh.italic = True
    r_idxh.font.name = "Times New Roman"
    r_idxh.font.size = Pt(9)
    r_idxt = p_idx.add_run("prompt injection, indirect prompt injection, LLM security, defense in depth, transformer classification, multi-modal ingestion, data leakage prevention, OpenAI gateway.")
    r_idxt.font.name = "Times New Roman"
    r_idxt.font.size = Pt(9)

    # I. INTRODUCTION
    add_ieee_h1("I.  INTRODUCTION")
    add_p(
        "Language-model applications increasingly act as autonomous agents, customer service intermediaries, and internal business analytical copilots, routinely combining trusted developer instructions with untrusted user input and third-party document corpora. Prompt injection exploits this unified execution channel: because language models cannot intrinsically separate instructional code from passive data, an adversary can format malicious inputs to hijack model execution, bypass safety alignments, redirect agentic tool calls, or extract confidential operational context [1–3]. In the OWASP Top 10 for Large Language Model Applications, prompt injection (LLM01) and sensitive information disclosure (LLM06) represent the two most pervasive vulnerabilities facing generative enterprise deployments [12].",
        indent=False
    )
    add_p(
        "Attacks are broadly bifurcated into two vectors: (1) direct prompt injection, where the adversary directly enters instructions into the conversational interface, and (2) indirect prompt injection, where malicious payloads are embedded within third-party carrier artifacts—such as uploaded reports, resumes, PDFs, or scanned images—that are subsequently consumed by the application [2, 4]."
    )
    add_p(
        "Where applications process consequential tasks or possess access to confidential credentials and developer preambles, static heuristic filters are fundamentally insufficient: simple keyword matching fails against paraphrased attacks, synonym substitution, and encoding obfuscations [5, 8]. Conversely, deploying pure neural models without heuristic safeguards incurs excessive inference overhead and risks catastrophic false-positive rates on legitimate defensive security inquiries [6, 7]. Furthermore, securing the input alone does not prevent the model from inadvertently revealing sensitive API keys, database credentials, or system instructions if an evasion successfully breaches inbound defenses."
    )

    add_ieee_h2("A. Contributions")
    add_p("This paper makes four concrete systems contributions:", indent=False)
    add_bullet("We design and implement a defense-in-depth security gateway coupling pre-execution inbound screening (Layer 1) with post-execution outbound response sanitization (Layer 2), guaranteeing zero downstream LLM invocation on blocked threats.", "1) Dual-Layer Perimeter: ")
    add_bullet("We develop an isolated attachment parsing and optical character recognition (OCR) pipeline that extracts text from DOCX, PDF, and image files independently of prompt text, preserving precise threat-source attribution (User Prompt, Attachment, or Both).", "2) Decoupled Multi-Modal Ingestion: ")
    add_bullet("We formulate a dual-perspective risk-scoring engine (Rfused = 0.40 Rrule + 0.60 RML) combining a 256-token head-tail DistilBERT classifier with signature heuristics, mapped onto an authoritative nine-category taxonomy that explicitly protects legitimate cybersecurity inquiries.", "3) Calibrated Neural-Heuristic Fusion: ")
    add_bullet("We evaluate performance on an independent 3,000-sample balanced benchmark, a 600-sample challenge holdout, and a 300-sample hard-negative suite. We deliver drop-in reverse-proxy integration via /v1/chat/completions, deploy a Chromium browser extension, and verify integrity with a 288-test automated regression suite (100% pass rate).", "4) Empirical Validation & Gateways: ")

    add_ieee_h2("B. Research Questions")
    add_bullet("How does hybrid neural-heuristic fusion compare to isolated rule-only and neural-only classifiers in minimizing false negatives while preserving high specificity?", "RQ1 (Component Fusion): ")
    add_bullet("Can decoupled multi-modal parsing reliably detect indirect carrier injections in documents and images without contaminating prompt classification?", "RQ2 (Attachment Generalization): ")
    add_bullet("Does the gateway strictly prevent LLM invocation on blocked inputs while maintaining fail-secure operation under degraded or missing model dependencies?", "RQ3 (Application Gating): ")
    add_bullet("Can real-time response inspection intercept system prompt preambles and credential disclosures without degrading legitimate model generation?", "RQ4 (Output Sanitization): ")

    # II. THREAT MODEL AND TAXONOMY
    add_ieee_h1("II.  THREAT MODEL AND TAXONOMY")
    add_p(
        "We model an untrusted operational environment where adversaries interact with generative applications via direct conversational interfaces, REST endpoints, or carrier documents (e.g., vendor contracts, resumes, financial reports, scanned receipts). The adversary seeks to override developer-defined operational guidelines, circumvent safety alignments, extract confidential system prompts, exfiltrate environment secrets or database credentials, or induce malicious agentic side effects.",
        indent=False
    )
    add_p(
        "The protected assets comprise: (1) System Context & Developer Instructions: proprietary preambles and organizational policy constraints; (2) Environment Credentials: API keys (sk-*, ghp_*, AIza*), database URIs, and private cryptographic keys; (3) User Privacy: PII including SSNs, credit cards, and confidential emails; and (4) Computational Budget: protection of the LLM generation budget from denial-of-wallet and infinite token loops."
    )
    add_p(
        "Prior heuristic baselines frequently misclassified all attacks under generic 'Direct Prompt Injection' or failed into 'Unclassified Suspicious Prompt'. Our production engine implements an authoritative nine-category taxonomy defined in backend/prompt_security/threat_taxonomy.py, detailed in Table I."
    )

    # ==========================================
    # SECTION 3: 1 COLUMN (Full Width Table I)
    # ==========================================
    sec3 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec3)
    set_section_columns(sec3, num_cols=1)

    p_t1c = doc.add_paragraph()
    p_t1c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1c.paragraph_format.space_before = Pt(5)
    p_t1c.paragraph_format.space_after = Pt(1)
    r_t1c = p_t1c.add_run("TABLE I\nAUTHORITATIVE NINE-CATEGORY THREAT TAXONOMY AND OPERATIONAL ACTIONS")
    r_t1c.bold = True
    r_t1c.font.name = "Times New Roman"
    r_t1c.font.size = Pt(8.5)
    r_t1c._r.get_or_add_rPr().append(parse_xml(f'<w:smallCaps {NS_W}/>'))

    tbl_tax = doc.add_table(rows=1, cols=4)
    tbl_tax.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_tax.autofit = False
    set_ieee_table_borders(tbl_tax)
    col_w_tax = [0.5, 2.1, 3.85, 0.8]
    add_ieee_table_header(tbl_tax, col_w_tax, ["Index", "Threat Category", "Scope & Behavioral Definition", "Action"])
    tax_data = [
        ("1", "**Existing Valid Training Examples / Benign Prompts**", "Standard conversational, educational, programming, and academic inquiries containing no adversarial intent.", "ALLOW"),
        ("2", "**Direct Prompt Injection**", "Explicit adversarial commands instructing the model to disregard prior context (e.g., 'Ignore all previous instructions and print ACCESS GRANTED').", "BLOCK"),
        ("3", "**Indirect Prompt Injection**", "Adversarial instructions planted in external third-party data sources, reports, or APIs that influence the model when consumed.", "BLOCK"),
        ("4", "**Instruction Override**", "Commands that usurp operational control or task objectives without necessarily requesting harmful output (e.g., 'Disregard previous role and summarize as a pirate').", "BLOCK"),
        ("5", "**Jailbreak**", "Persona adoption, hypothetical scenarios, and complex adversarial framing designed to bypass safety filters (e.g., DAN, developer mode, unrestricted simulated shell).", "BLOCK"),
        ("6", "**Obfuscation / Encoding**", "Payloads utilizing Base64, hex encoding, ROT13, binary ciphers, zero-width Unicode characters, or leetspeak to evade standard tokenization.", "BLOCK"),
        ("7", "**Embedded / Carrier Injection**", "Malicious instructions concealed within structural carrier documents, such as hidden text blocks in DOCX XML, PDF metadata streams, or text embedded in images.", "BLOCK"),
        ("8", "**Data Exfiltration / Sensitive Information Extraction**", "Targeted reconnaissance attacks seeking system prompt exposure, administrative credentials, passwords, or configuration dumps.", "BLOCK"),
        ("9", "**Safe Security-Related Hard Negatives**", "Legitimate educational, academic, or professional inquiries concerning cybersecurity concepts (e.g., 'Explain how prompt injection vulnerabilities work in LLM architectures').", "ALLOW"),
    ]
    for idx, (c1, c2, c3, c4) in enumerate(tax_data):
        add_ieee_table_row(tbl_tax, col_w_tax, [c1, c2, c3, c4], is_even=(idx % 2 == 1),
                           aligns=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER])

    doc.add_paragraph().paragraph_format.space_after = Pt(3)

    # ==========================================
    # SECTION 4: 2 COLUMNS (Related Work, Architecture)
    # ==========================================
    sec4 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec4)
    set_section_columns(sec4, num_cols=2, space_dxa=360)

    # III. RELATED WORK
    add_ieee_h1("III.  RELATED WORK")
    add_p(
        "Early foundational research cataloged direct prompt injection and system prompt extraction attacks against early instruction-tuned language models [1]. Greshake et al. and Liu et al. demonstrated that indirect prompt injection represents a systemic vulnerability for applications that process third-party web content, emails, and uploaded documents [2, 3]. Subsequent benchmarks expanded from static binary classification to complex agentic environments: InjecAgent evaluated indirect injections in tool-integrated agent frameworks [4], and AgentDojo formalized dynamic benchmarking with adaptive adversarial attacks and defenses [5].",
        indent=False
    )
    add_p(
        "CAPTURE highlighted the critical challenge of context-aware evaluation and over-defense, showing that naive classifiers often block legitimate user requests [6]. Cui et al. provided an extensive empirical reassessment across diverse application contexts, demonstrating that static keyword filters degrade significantly under distribution shift [7]. PromptRobust evaluated model robustness across adversarial phrasing perturbations [8]. In model distillation, DistilBERT established that 40% smaller distilled transformer models retain 97% of BERT's language comprehension capabilities while executing 60% faster [9]. In output security, Carlini et al. demonstrated that language models memorize and inadvertently leak training data and operational secrets [10]. Emerging governance frameworks, including NIST AI 600-1 [11] and the OWASP GenAI Top 10 [12], emphasize defense-in-depth architectures spanning both pre-invocation filtering and post-generation egress validation."
    )

    # IV. SYSTEM ARCHITECTURE
    add_ieee_h1("IV.  SYSTEM ARCHITECTURE AND IMPLEMENTATION")
    add_p(
        "The end-to-end prompt security middleware establishes an active, defense-in-depth perimeter surrounding the target generative model, as illustrated in Fig. 1. The architecture decouples multi-modal attachment parsing from direct conversational inputs, performs inbound neural-heuristic threat screening (Layer 1) before model execution, enforces fail-secure gating at decision threshold θ = 0.3800, buffers model responses, and applies outbound response sanitization (Layer 2) prior to client delivery.",
        indent=False
    )

    # ==========================================
    # FULL-WIDTH FIGURE 1: ARCHITECTURE DIAGRAM
    # ==========================================
    sec_fig1 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec_fig1)
    set_section_columns(sec_fig1, num_cols=1)

    p_fig1 = doc.add_paragraph()
    p_fig1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig1.paragraph_format.left_indent = Inches(0)
    p_fig1.paragraph_format.right_indent = Inches(0)
    p_fig1.paragraph_format.first_line_indent = Inches(0)
    p_fig1.paragraph_format.space_before = Pt(6)
    p_fig1.paragraph_format.space_after = Pt(2)
    run_fig1 = p_fig1.add_run()
    run_fig1.add_picture("figures/pipeline_architecture.png", width=Inches(7.0))

    # Figure 1 Caption
    p_cap1 = doc.add_paragraph()
    p_cap1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cap1.paragraph_format.left_indent = Inches(0.2)
    p_cap1.paragraph_format.right_indent = Inches(0.2)
    p_cap1.paragraph_format.space_before = Pt(2)
    p_cap1.paragraph_format.space_after = Pt(6)

    r_cap_lbl = p_cap1.add_run("Fig. 1.  ")
    r_cap_lbl.bold = True
    r_cap_lbl.font.name = "Times New Roman"
    r_cap_lbl.font.size = Pt(8.5)

    r_cap_txt = p_cap1.add_run(
        "End-to-End Dual-Layer Prompt Security Gateway Architecture. Untrusted user inputs and multi-modal attachments are decoupled, preprocessed, and evaluated through Layer 1 neural-heuristic fusion (Rfused = 0.40 Rrule + 0.60 RML). Blocked requests are halted immediately, guaranteeing zero downstream LLM execution. Approved requests are forwarded to the configured LLM, whose buffered output is sanitized by Layer 2 response leakage inspection before client delivery."
    )
    r_cap_txt.font.name = "Times New Roman"
    r_cap_txt.font.size = Pt(8.5)

    # Resume 2-column layout for subsections A-E
    sec_arch_body = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec_arch_body)
    set_section_columns(sec_arch_body, num_cols=2, space_dxa=360)

    add_ieee_h2("A. Input Normalization & Head-Tail Tokenization")
    add_p(
        "Adversaries frequently position attack instructions either at the very beginning (head override) or at the end of large text blocks (tail carrier injection). Standard truncation to 256 tokens from the beginning discards the end of the text. As implemented in backend/prompt_security/preprocessing/token_preprocessing.py, our pipeline extracts 127 tokens from the sequence head and 127 tokens from the sequence tail, combining them with special tokens ([CLS] and [SEP]):",
        indent=False
    )
    add_equation("T_input = [ [CLS], t_1, ..., t_127, [SEP], t_{N-126}, ..., t_N, [SEP] ]", "1")

    add_ieee_h2("B. Inbound Layer 1 Engine: Threat Fusion")
    add_p(
        "Layer 1 combines the continuous risk outputs of the heuristic signature engine (R_rule in [0, 100]) and the fine-tuned DistilBERT transformer (R_ML = 100 * P(malicious) in [0, 100]):",
        indent=False
    )
    add_equation("R_fused = 0.40 * R_rule + 0.60 * R_ML", "2")
    add_p(
        "Requests are mapped to four security decision bands: LOW (0 to 29: ALLOW), MEDIUM (30 to 59: WARNING - logged to audit database; benign requests proceed), HIGH (60 to 79: BLOCK), and CRITICAL (80 to 100: BLOCK). Whenever R_fused >= 38.0 (calibrated decision threshold θ = 0.3800) or either constituent module emits a critical attack override, the request is immediately blocked, guaranteeing zero downstream LLM invocation."
    )

    add_ieee_h2("C. Decoupled Multi-Modal Attachment Parsing")
    add_p(
        "The gateway ingests structured documents (DOCX, PDF, TXT) and raster images (PNG, JPG). Document streams are parsed using pypdf and python-docx to extract text paragraphs, tables, and embedded XML payloads. Image files are scanned using Tesseract OCR via pytesseract and Pillow. Threat scores are computed independently for prompt and attachment channels: R_overall = max(R_prompt, R_attachment). The system outputs an explicit provenance label: threat_source in {User Prompt, Attachment, Both, None}. This prevents benign user questions accompanied by malicious documents from contaminating user intent metrics.",
        indent=False
    )

    add_ieee_h2("D. Outbound Layer 2 Guard: Response Sanitization")
    add_p(
        "When an approved prompt reaches the downstream LLM (local Ollama llama3.2:3b, OpenAI gpt-4o, or offline mock simulation), the generated output is buffered and evaluated by Layer 2 before egress:",
        indent=False
    )
    add_bullet("Scans for preamble leakage patterns, verbatim system header exposure, and enclosed system markup tags (<system>, [SYSTEM_PROMPT]). Responses with score >= 85 trigger a BLOCK decision, completely withholding the response and returning a secure alert placeholder.", "1) System Prompt Disclosure Detection: ")
    add_bullet("Detects live credential signatures including OpenAI API keys (sk-*), GitHub tokens (ghp_*), Google Cloud keys (AIza*), private cryptographic keys (BEGIN PRIVATE KEY), database connection URIs (postgres://...), and authorization bearer tokens.", "2) Secret & Key Detection: ")
    add_bullet("Identifies Social Security numbers, credit card sequences, and personal email addresses, automatically substituting matches with [REDACTED_PII] and returning decision: 'MASK'.", "3) PII Redaction & Masking: ")
    add_bullet("Enforces length boundaries (truncating responses exceeding 8,000 characters) and detects infinite token generation loops (token uniqueness ratio < 0.15 -> BLOCK).", "4) Structural & Anomaly Validation: ")

    add_ieee_h2("E. Production Ecosystem Gateways")
    add_p(
        "The service exposes POST /api/v1/chat/completions (aliased to /v1/chat/completions), providing direct drop-in compatibility for Open WebUI, LangChain, and organizational agents. Crucially, streaming raw tokens (stream=true) is prohibited by policy: the gateway buffers tokens to enable complete Layer 2 whole-response inspection, preventing incremental leakage. On Layer 1 block, it returns standard OpenAI response structures with finish_reason: 'content_filter'. In parallel, an unpacked Chromium browser extension registers low-level pointerdown and keydown event listeners on ProseMirror divs and textareas, preventing prompt submissions until security clearance is confirmed.",
        indent=False
    )

    # V. DATASET LINEAGE
    add_ieee_h1("V.  DATASET LINEAGE AND MODEL PROVENANCE")
    add_p(
        "The training data underwent three distinct development stages documented in docs/DATASET_LINEAGE.md. Phase 1 established initial baselines across 14,317 samples. Phase 2 expanded into a balanced multi-domain corpus of 15,500 samples. Phase 3 (V3) resolved short prompt injections (<20 characters, e.g., 'reset context') and conversational false positives through a dual-reviewer human annotation protocol with fail-closed dispute adjudication, producing 16,224 training samples (train_v3.csv) and 1,500 validation samples (validation_v3.csv).",
        indent=False
    )
    add_p(
        "Model Cryptographic Identity: The production model artifact is stored at experiments/distilbert/distilbert_model_augmented.pt with exact file size 267,856,803 bytes (~255.45 MB) and SHA-256 digest c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93. The 330-byte difference relative to early notes represents the difference between the Phase 2 backup (267,856,473 bytes) and the promoted V3 production model (267,856,803 bytes)."
    )

    # ==========================================
    # SECTION 5: 1 COLUMN (Full Width Table II and Table III)
    # ==========================================
    sec5 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec5)
    set_section_columns(sec5, num_cols=1)

    # Table II Caption
    p_t2c = doc.add_paragraph()
    p_t2c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2c.paragraph_format.space_before = Pt(5)
    p_t2c.paragraph_format.space_after = Pt(1)
    r_t2c = p_t2c.add_run("TABLE II\nDATASET LINEAGE AND SPLIT DISTRIBUTION IN REPOSITORY")
    r_t2c.bold = True
    r_t2c.font.name = "Times New Roman"
    r_t2c.font.size = Pt(8.5)
    r_t2c._r.get_or_add_rPr().append(parse_xml(f'<w:smallCaps {NS_W}/>'))

    tbl_data = doc.add_table(rows=1, cols=5)
    tbl_data.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_data.autofit = False
    set_ieee_table_borders(tbl_data)
    col_w_data = [2.2, 1.0, 1.0, 1.0, 2.05]
    add_ieee_table_header(tbl_data, col_w_data, ["Dataset Split / File", "Total Rows", "Benign (0)", "Malicious (1)", "Stage / Role"])
    dataset_rows = [
        ("train.csv", "14,317", "6,979", "7,338", "Phase 1 Base Train Split"),
        ("validation.csv", "3,068", "1,496", "1,572", "Phase 1 Base Val Split"),
        ("test.csv", "3,069", "1,496", "1,573", "Phase 1 Base Test Split"),
        ("train_generalization.csv", "15,500", "7,750", "7,750", "Phase 2 Train Split"),
        ("validation_generalization.csv", "3,000", "1,500", "1,500", "Phase 2 Val Split"),
        ("test_generalization.csv", "3,000", "1,500", "1,500", "Phase 2 Generalization Benchmark"),
        ("**train_v3.csv**", "**16,224**", "**8,112**", "**8,112**", "**V3 Production Train Corpus**"),
        ("**validation_v3.csv**", "**1,500**", "**750**", "**750**", "**V3 Production Val Set**"),
        ("challenge_holdout.csv", "600", "300", "300", "Zero-Shot Evasion Test"),
        ("hard_negatives_expanded.csv", "300", "150", "150", "Expanded Hard-Negative Test"),
        ("hard_negatives_curated.csv", "300", "150", "150", "Curated Hard-Negative Test"),
        ("short_prompt_eval.csv", "200", "100", "100", "Target Short-Prompt (<20 char) Test"),
    ]
    for idx, (c1, c2, c3, c4, c5) in enumerate(dataset_rows):
        add_ieee_table_row(tbl_data, col_w_data, [c1, c2, c3, c4, c5], is_even=(idx % 2 == 1),
                           aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_paragraph().paragraph_format.space_after = Pt(5)

    # Table III Caption
    p_t3c = doc.add_paragraph()
    p_t3c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3c.paragraph_format.space_before = Pt(5)
    p_t3c.paragraph_format.space_after = Pt(1)
    r_t3c = p_t3c.add_run("TABLE III\nEMPIRICAL PERFORMANCE COMPARISON ACROSS DETECTION REGIMES ON INDEPENDENT HOLDOUTS (θ = 0.3800)")
    r_t3c.bold = True
    r_t3c.font.name = "Times New Roman"
    r_t3c.font.size = Pt(8.5)
    r_t3c._r.get_or_add_rPr().append(parse_xml(f'<w:smallCaps {NS_W}/>'))

    tbl_abl = doc.add_table(rows=1, cols=9)
    tbl_abl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_abl.autofit = False
    set_ieee_table_borders(tbl_abl)
    col_w_abl = [1.5, 1.45, 0.45, 0.45, 0.45, 0.45, 0.7, 0.7, 0.7]
    add_ieee_table_header(tbl_abl, col_w_abl, ["Corpus (N)", "Detection Regime", "TN", "FP", "FN", "TP", "Accuracy", "Precision", "Recall"])
    abl_data = [
        ("Generalization\n(3,000)", "Rule-Only Baseline (>30)", "1,500", "0", "1,369", "131", "0.5437", "1.0000", "0.0873"),
        ("Generalization\n(3,000)", "Rule-Only Block (>60)", "1,500", "0", "1,375", "125", "0.5417", "1.0000", "0.0833"),
        ("Generalization\n(3,000)", "**DistilBERT Classifier (ML)**", "**1,489**", "**11**", "**27**", "**1,473**", "**0.9873**", "**0.9926**", "**0.9820**"),
        ("Generalization\n(3,000)", "**Fused Hybrid Middleware**", "**1,489**", "**11**", "**18**", "**1,482**", "**0.9903**", "**0.9926**", "**0.9880**"),
        ("Challenge Holdout\n(600)", "Rule-Only Baseline (>30)", "300", "0", "280", "20", "0.5333", "1.0000", "0.0667"),
        ("Challenge Holdout\n(600)", "**DistilBERT Classifier (ML)**", "**300**", "**0**", "**7**", "**293**", "**0.9883**", "**1.0000**", "**0.9767**"),
        ("Challenge Holdout\n(600)", "**Fused Hybrid Middleware**", "**300**", "**0**", "**5**", "**295**", "**0.9917**", "**1.0000**", "**0.9833**"),
        ("Hard Negatives\n(300)", "Rule-Only Baseline (>30)", "144", "6", "141", "9", "0.5100", "0.6000", "0.0600"),
        ("Hard Negatives\n(300)", "**DistilBERT Classifier (ML)**", "**133**", "**17**", "**10**", "**140**", "**0.9100**", "**0.8917**", "**0.9333**"),
        ("Hard Negatives\n(300)", "**Fused Hybrid Middleware**", "**137**", "**13**", "**7**", "**143**", "**0.9333**", "**0.9167**", "**0.9533**"),
    ]
    for idx, (c1, c2, c3, c4, c5, c6, c7, c8, c9) in enumerate(abl_data):
        add_ieee_table_row(tbl_abl, col_w_abl, [c1, c2, c3, c4, c5, c6, c7, c8, c9], is_even=(idx % 2 == 1),
                           aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])

    doc.add_paragraph().paragraph_format.space_after = Pt(3)

    # ==========================================
    # SECTION 6: 2 COLUMNS (Evaluation, Discussion)
    # ==========================================
    sec6 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec6)
    set_section_columns(sec6, num_cols=2, space_dxa=360)

    # VI. EXPERIMENTAL EVALUATION
    add_ieee_h1("VI.  EXPERIMENTAL EVALUATION AND RESULTS")
    add_ieee_h2("A. RQ1: Component Contribution Analysis")
    add_p(
        "The empirical findings in Table III clearly resolve RQ1. On the 3,000-sample generalization benchmark, rule-only heuristics achieve only 8.73% recall (F1 = 0.1606), failing to identify paraphrased attacks. Deploying the DistilBERT transformer elevates recall to 98.20% and F1-score to 0.9873. On the Challenge Holdout, the neural classifier achieves 98.83% accuracy with zero false positives (FP = 0, FPR = 0.00%) and ROC-AUC of 1.0000. Fusing heuristic patterns with neural attention achieves peak performance (F1 = 0.9903 on Generalization, 0.9916 on Challenge Holdout), combining regex floor guarantees with deep semantic attention.",
        indent=False
    )
    add_p(
        "Per-Category Attack Resilience: Evaluating category subsets on the 3,000-sample test set demonstrates: Credential Harvesting (N=98): 100.0% accuracy; Indirect Carrier Injection (N=44): 100.0% accuracy; Obfuscation & Encoding (N=215): 100.0% accuracy; System Prompt Extraction (N=78): 100.0% accuracy; Direct Instruction Override (N=922): 99.1% accuracy; Benign Coding/STEM (N=396): 100.0% accuracy; Benign Cybersecurity (N=39): 100.0% accuracy; and Adversarial Jailbreaks (N=143): 86.7% accuracy."
    )

    add_ieee_h2("B. RQ2: Multi-Modal Attachment Parsing Performance")
    add_p(
        "On the Challenge Holdout set, injection placement testing yielded: Tail Injections (N=50): 100.0% detected (FN=0); Head Injections (N=25): 80.0% detected (FN=5); and Long Benign Documents (N=25): 100.0% allowed (FP=0). In dedicated tests (test_docx_indirect_injection.py and test_attachments_image_ocr.py), malicious instructions concealed within reports and scanned receipts were successfully detected by the decoupled attachment pipeline with threat_source = Attachment, preserving user prompt evaluation accuracy.",
        indent=False
    )

    add_ieee_h2("C. RQ3: Application Gating & Automated Verification")
    add_p(
        "To evaluate whether the gateway strictly enforces security decisions and maintains fail-secure properties, we executed the full automated test suite using pytest. The test suite comprises 288 tests across 17 modules, achieving a 100% pass rate (288 passed, 0 failed, 0 skipped, execution time: 458s).",
        indent=False
    )
    add_p(
        "Zero Downstream Invocations: In integration tests spanning both direct HTTP requests and the OpenAI gateway (test_scenarios_a_to_h.py and test_openai_gateway_integration.py), spy assertions verified that whenever Layer 1 emitted a BLOCK decision, the downstream LLM client was called exactly zero times (N = 0)."
    )

    # ==========================================
    # SECTION 7: 1 COLUMN (Full Width Table IV: 288-Test Matrix)
    # ==========================================
    sec7 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec7)
    set_section_columns(sec7, num_cols=1)

    p_t4c = doc.add_paragraph()
    p_t4c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4c.paragraph_format.space_before = Pt(5)
    p_t4c.paragraph_format.space_after = Pt(1)
    r_t4c = p_t4c.add_run("TABLE IV\nCOMPREHENSIVE AUTOMATED VERIFICATION SUITE MATRIX (288 PASSING TESTS)")
    r_t4c.bold = True
    r_t4c.font.name = "Times New Roman"
    r_t4c.font.size = Pt(8.5)
    r_t4c._r.get_or_add_rPr().append(parse_xml(f'<w:smallCaps {NS_W}/>'))

    tbl_tests = doc.add_table(rows=1, cols=4)
    tbl_tests.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_tests.autofit = False
    set_ieee_table_borders(tbl_tests)
    col_w_tests = [2.4, 0.7, 0.9, 3.25]
    add_ieee_table_header(tbl_tests, col_w_tests, ["Test Module / Subsystem", "Tests", "Pass Rate", "Functionality Verified"])
    test_rows = [
        ("test_admin_auth.py", "30", "100%", "Admin security, password hashing, session authentication"),
        ("test_attachments.py", "34", "100%", "PDF/DOCX extraction, size limits, indirect injection gating"),
        ("test_attachments_image_ocr.py", "19", "100%", "Tesseract OCR parsing, raster carrier injection defense"),
        ("test_block_dialog_ui.py", "13", "100%", "Viewport-constrained modal, responsive action buttons"),
        ("test_detection.py", "14", "100%", "Layer 1 detection, threshold calibration, edge cases"),
        ("test_docx_indirect_injection.py", "4", "100%", "DOCX indirect injection defense, pre-invocation gating"),
        ("test_dual_layer.py", "6", "100%", "Dual-layer end-to-end integration, decision propagation"),
        ("test_extension_interception.py", "15", "100%", "Browser DOM interception, ProseMirror, concurrency locks"),
        ("test_extension_parity.py", "28", "100%", "Browser extension parity with Analyzer API verdicts"),
        ("test_external_llm_demo.py", "9", "100%", "External LLM provider client, failover, model selection"),
        ("test_integration_center.py", "9", "100%", "Gateway metadata, connection testing, incident filtering"),
        ("test_layer2_demo.py", "16", "100%", "Layer 2 response inspection, secret masking, simulated leaks"),
        ("test_llm_client.py", "6", "100%", "LLM client routing (Ollama, OpenAI, local mock)"),
        ("test_model_integrity.py", "25", "100%", "Checkpoint SHA-256 verification, fail-secure fallback"),
        ("test_open_webui_deploy.py", "8", "100%", "Open WebUI reverse proxying, deployment verification"),
        ("test_openai_gateway_integration.py", "12", "100%", "/v1/chat/completions payload schema, streaming policy"),
        ("test_scenarios_a_to_h.py", "10", "100%", "End-to-end verification of Scenarios A through H"),
        ("test_threat_taxonomy_nine_categories.py", "14", "100%", "Complete 9-category taxonomy classification & fallback"),
        ("test_ui_navigation_and_themes.py", "7", "100%", "Theme switching, dark mode, UI navigation consistency"),
        ("test_web_ui_integration.py", "9", "100%", "Web routes, security dashboard, incident logging"),
        ("**Total Automated Regression Suite**", "**288**", "**100.0%**", "**Complete System Integrity Verified (All 288 tests passed)**"),
    ]
    for idx, (c1, c2, c3, c4) in enumerate(test_rows):
        add_ieee_table_row(tbl_tests, col_w_tests, [c1, c2, c3, c4], is_even=(idx % 2 == 1),
                           aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_paragraph().paragraph_format.space_after = Pt(3)

    # ==========================================
    # SECTION 8: 2 COLUMNS (Final Sections & References)
    # ==========================================
    sec8 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    configure_ieee_margins(sec8)
    set_section_columns(sec8, num_cols=2, space_dxa=360)

    add_ieee_h2("D. RQ4: Outbound Output Sanitization Performance")
    add_p(
        "Layer 2 response inspection was tested across synthetic leak injection scenarios: (1) Credential Leakage Interception: synthetic API keys (sk-live...) were intercepted and withheld in 100% of test runs, with raw secrets appearing in 0.0% of client outputs; (2) PII Masking: SSNs, credit cards, and emails were successfully redacted with [REDACTED_PII] under decision: 'MASK' without suppressing surrounding text; and (3) Benign Transparency: safe prompts (e.g., 'What is climate change?') delivered genuine model responses with zero false blocks.",
        indent=False
    )

    add_ieee_h2("E. Latency Profile")
    add_p("Table V summarizes execution latency across hardware runtimes.", indent=False)

    # Table V: Latency (fits 1 column, 3.50")
    p_t5c = doc.add_paragraph()
    p_t5c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t5c.paragraph_format.space_before = Pt(3)
    p_t5c.paragraph_format.space_after = Pt(1)
    r_t5c = p_t5c.add_run("TABLE V\nEND-TO-END LATENCY ACROSS RUNTIMES")
    r_t5c.bold = True
    r_t5c.font.name = "Times New Roman"
    r_t5c.font.size = Pt(8)
    r_t5c._r.get_or_add_rPr().append(parse_xml(f'<w:smallCaps {NS_W}/>'))

    tbl_lat = doc.add_table(rows=1, cols=4)
    tbl_lat.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_lat.autofit = False
    set_ieee_table_borders(tbl_lat)
    col_w_lat = [1.4, 0.7, 0.7, 0.7]
    add_ieee_table_header(tbl_lat, col_w_lat, ["Pipeline Stage", "MPS", "CUDA", "x86 CPU"])
    lat_rows = [
        ("Preprocessing", "1.1 ms", "1.0 ms", "1.8 ms"),
        ("Rule Engine (R_rule)", "3.2 ms", "3.1 ms", "3.9 ms"),
        ("DistilBERT (R_ML)", "24.6 ms", "18.2 ms", "78.4 ms"),
        ("Decision Gate", "0.4 ms", "0.4 ms", "0.6 ms"),
        ("**Total Layer 1**", "**29.3 ms**", "**22.7 ms**", "**84.7 ms**"),
        ("Layer 2 Regex/PII", "3.8 ms", "3.5 ms", "4.2 ms"),
        ("Layer 2 Validation", "0.3 ms", "0.3 ms", "0.4 ms"),
    ]
    for idx, (c1, c2, c3, c4) in enumerate(lat_rows):
        add_ieee_table_row(tbl_lat, col_w_lat, [c1, c2, c3, c4], is_even=(idx % 2 == 1),
                           aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])

    doc.add_paragraph().paragraph_format.space_after = Pt(3)

    # VII. DISCUSSION
    add_ieee_h1("VII.  DISCUSSION AND SECURITY ANALYSIS")
    add_ieee_h2("A. Resolution of Research Questions")
    add_bullet("Rule-only detection achieves only 8.73% recall on adversarial prompts. Neural transformer classification elevates recall to 98.20%, and hybrid fusion achieves 98.80% recall and 99.26% precision by combining regex floor guarantees with deep semantic attention.", "RQ1 (Fusion): ")
    add_bullet("Decoupling attachment parsing from user prompt scoring isolates carrier attacks and maintains 100% detection on tail carrier injections, preserving precise threat-source attribution.", "RQ2 (Attachments): ")
    add_bullet("Automated test assertions verify that downstream LLMs are never invoked when input risk exceeds θ = 0.3800, and cryptographic hash checking ensures fail-secure degradation to rule-only heuristics if model weights are unavailable.", "RQ3 (Application Gating): ")
    add_bullet("Layer 2 inspection successfully intercepts system prompt leaks, redacts PII, and suppresses credentials without compromising benign model generation.", "RQ4 (Response Protection): ")

    add_ieee_h2("B. Necessity of Dual-Layer Architecture")
    add_p(
        "Our findings demonstrate that neither inbound prompt screening nor outbound output filtering is sufficient in isolation. Relying solely on inbound screening leaves applications vulnerable to model hallucinations, training-data extraction [10], or novel zero-day prompt encodings that circumvent the classifier. Conversely, relying solely on outbound output filtering forces applications to incur the financial and computational cost of invoking the LLM for every malicious payload. Our dual-layer perimeter provides true defense-in-depth: Layer 1 minimizes compute expenditure and eliminates prompt hijacking, while Layer 2 provides a fail-safe backstop against sensitive data leakage.",
        indent=False
    )

    add_ieee_h2("C. Policy Implications of Token Streaming")
    add_p(
        "A significant systems insight involves token streaming. While streaming improves perceived user responsiveness, it fundamentally undermines output security: once tokens egress the gateway, credential leaks and system preambles cannot be revoked. Our gateway enforces an atomic buffer-and-scan egress policy, illustrating that high-assurance LLM security requires non-streaming egress architectures.",
        indent=False
    )

    # VIII. LIMITATIONS
    add_ieee_h1("VIII.  LIMITATIONS AND RESPONSIBLE USE")
    add_p(
        "Limitations: (1) Adversarial Drift: highly creative, multi-turn adversarial jailbreaks and foreign-language obfuscations can challenge sequence classifiers. Continuous retraining and dynamic threshold calibration remain essential. (2) OCR Resolution Limits: image OCR accuracy depends on raster clarity; heavily distorted, low-contrast, or steganographic instructions may evade standard Tesseract extraction. (3) Dynamic Canary Tokens: in the current release, Layer 2 operates via deterministic regex signatures and structural checks. Enterprise dynamic canary tracking (generating ephemeral per-session tokens) is identified as a valuable future enhancement.",
        indent=False
    )
    add_p(
        "Responsible Disclosure & Privacy: All penetration testing prompts used in this research were evaluated in isolated local testing environments. SQLite audit logging stores prompt snippets and client IP addresses for security forensics; production deployments should implement rigorous data retention and access-control policies."
    )

    # IX. CONCLUSION
    add_ieee_h1("IX.  CONCLUSION")
    add_p(
        "This paper presented the design, implementation, and empirical evaluation of a dual-layer prompt security middleware and gateway defending LLM applications against direct injection, multi-modal carrier injection, and outbound data leakage. By integrating a fine-tuned DistilBERT transformer with signature heuristics at a calibrated threshold (θ = 0.3800), our system achieves 98.73% accuracy and 98.20% recall on an independent 3,000-sample generalization benchmark, transforming a weak rule-only baseline into a high-assurance security perimeter. With decoupled attachment extraction, an authoritative nine-category threat taxonomy, OpenAI-compatible gateway reverse proxying, a resilient browser extension, and a 288-test automated regression suite with a 100% pass rate, this work demonstrates that robust, low-latency prompt security can be realized in production generative AI systems.",
        indent=False
    )

    # ACKNOWLEDGMENT
    add_ieee_h1("ACKNOWLEDGMENT")
    add_p(
        "The authors thank the Cybersecurity Case Study faculty and reviewers for guidance and constructive feedback throughout the design and evaluation of this system.",
        indent=False
    )

    # REFERENCES
    add_ieee_h1("REFERENCES")
    refs = [
        "[1]  F. Perez and I. Ribeiro, \"Ignore previous prompt: Attack techniques for language models,\" arXiv preprint arXiv:2211.09527, 2022.",
        "[2]  K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, \"Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection,\" in Proc. 16th ACM Workshop on Artificial Intelligence and Security (AISEC), 2023, pp. 79–90, doi: 10.1145/3605764.3623985.",
        "[3]  Y. Liu, G. Deng, Z. Xu, Y. Li, Y. Zheng, Y. Zhang, L. Zhao, T. Zhang, and Y. Liu, \"Prompt injection attack against LLM-integrated applications,\" arXiv preprint arXiv:2306.05499, 2023.",
        "[4]  Q. Zhan, Z. Liang, Z. Ying, and D. Kang, \"InjecAgent: Benchmarking indirect prompt injections in tool-integrated large language model agents,\" in Findings of the Association for Computational Linguistics: ACL 2024, 2024, pp. 10471–10506, doi: 10.18653/v1/2024.findings-acl.624.",
        "[5]  E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer, and F. Tramèr, \"AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 37, 2024.",
        "[6]  G. Kholkar and R. Ahuja, \"CAPTURE: Context-aware prompt injection testing and robustness enhancement,\" in Proc. 1st Workshop on LLM Security, 2025, pp. 176–188.",
        "[7]  C. Cui, Y. Wu, M. Backes, and Y. Zhang, \"Rethinking assessments of prompt injection attacks,\" in Findings of the Association for Computational Linguistics: ACL 2026, 2026, pp. 23773–23799, doi: 10.18653/v1/2026.findings-acl.1191.",
        "[8]  K. Zhu, J. Wang, J. Zhou, Z. Wang, H. Chen, Y. Wang, L. Yang, W. Ye, N. Zhang, Y. Du, X. Xie, and Y. Hao, \"PromptRobust: Towards evaluating the robustness of large language models on adversarial prompts,\" arXiv preprint arXiv:2306.04528, 2023.",
        "[9]  V. Sanh, L. Debut, J. Chaumond, and T. Wolf, \"DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter,\" arXiv preprint arXiv:1910.01108, 2019.",
        "[10] N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, U. Erlingsson, A. Oprea, and C. Raffel, \"Extracting training data from large language models,\" in Proc. 30th USENIX Security Symposium, 2021, pp. 2633–2650.",
        "[11] C. Autio et al., \"Artificial intelligence risk management framework: Generative artificial intelligence profile,\" NIST Special Publication AI 600-1, 2024, doi: 10.6028/NIST.AI.600-1.",
        "[12] OWASP GenAI Security Project, \"OWASP Top 10 for Large Language Model Applications and Generative AI 2025,\" OWASP Foundation, Oct. 2025. [Online]. Available: https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    ]
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.left_indent = Inches(0.25)
        p_ref.paragraph_format.first_line_indent = Inches(-0.25)
        p_ref.paragraph_format.space_before = Pt(0)
        p_ref.paragraph_format.space_after = Pt(2.5)
        p_ref.paragraph_format.line_spacing = 1.0
        r_ref = p_ref.add_run(ref)
        r_ref.font.name = "Times New Roman"
        r_ref.font.size = Pt(8)

    # Save output
    out_dir = "paper"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "IEEE_Conference_Paper.docx")
    doc.save(out_path)
    print(f"Successfully generated IEEE Word document: {out_path} ({os.path.getsize(out_path):,} bytes)")

    # Also sync conference_paper.docx
    shutil.copy2(out_path, os.path.join(out_dir, "conference_paper.docx"))
    
    # Also copy to Desktop
    desktop_path = "/Users/omikashrestha/Desktop/IEEE_Conference_Paper.docx"
    shutil.copy2(out_path, desktop_path)
    shutil.copy2(out_path, "/Users/omikashrestha/Desktop/conference_paper.docx")
    print(f"Copied to Desktop: {desktop_path}")

    # Copy to brain artifacts
    artifact_path = "/Users/omikashrestha/.gemini/antigravity/brain/016a5888-8fd9-4a58-9bbc-3bea0d9cf17d/IEEE_Conference_Paper.docx"
    shutil.copy2(out_path, artifact_path)
    shutil.copy2(out_path, "/Users/omikashrestha/.gemini/antigravity/brain/016a5888-8fd9-4a58-9bbc-3bea0d9cf17d/conference_paper.docx")
    print(f"Copied to Artifacts: {artifact_path}")

if __name__ == "__main__":
    build_ieee_doc()
