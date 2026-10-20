"""
generate_docx_paper.py
Generates a professional, publication-grade academic conference paper Word document (.docx)
from the completed Group 25 Dual-Layer Security Architecture research paper.
"""

import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def create_element(name):
    return OxmlElement(name)

def set_cell_shading(cell, color_hex):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_table_borders(table, top_color="2D3748", inside_color="CBD5E0"):
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="12" w:space="0" w:color="{top_color}"/>
            <w:left w:val="none"/>
            <w:bottom w:val="single" w:sz="12" w:space="0" w:color="{top_color}"/>
            <w:right w:val="none"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{inside_color}"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders_xml)

def set_callout_borders(table, border_color="3182CE"):
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders_xml)

def set_code_borders(table, border_color="E2E8F0"):
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:left w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>
            <w:insideH w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders_xml)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_header_row(table, col_widths, headers, bg_hex="1A365D", text_color=RGBColor(255, 255, 255)):
    row = table.rows[0]
    # repeat header row across pages
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    
    for i, title in enumerate(headers):
        cell = row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_shading(cell, bg_hex)
        set_cell_margins(cell, top=140, bottom=140, left=150, right=150)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(title)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = text_color

def add_data_row(table, col_widths, values, is_even=False, aligns=None):
    row = table.add_row()
    # cantSplit to avoid row split across pages
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
    
    bg_hex = "F7FAFC" if is_even else "FFFFFF"
    for i, val in enumerate(values):
        cell = row.cells[i]
        cell.width = Inches(col_widths[i])
        set_cell_shading(cell, bg_hex)
        set_cell_margins(cell, top=90, bottom=90, left=140, right=140)
        p = cell.paragraphs[0]
        align = aligns[i] if aligns and i < len(aligns) else WD_ALIGN_PARAGRAPH.LEFT
        p.alignment = align
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        
        # Check if value has bold formatting or multi-line
        lines = str(val).split("\n")
        for j, line in enumerate(lines):
            if j > 0:
                p = cell.add_paragraph()
                p.alignment = align
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(1)
            
            # Simple bold parsing e.g. **text**
            if "**" in line:
                parts = line.split("**")
                for k, part in enumerate(parts):
                    run = p.add_run(part)
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(9)
                    if k % 2 == 1:
                        run.bold = True
            else:
                run = p.add_run(line)
                run.font.name = "Times New Roman"
                run.font.size = Pt(9)

def main():
    doc = Document()

    # 1. Page Margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)

    # Base styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(26, 32, 44)

    # ==========================================
    # Title & Metadata
    # ==========================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run("Dual-Layer Security Architecture for Prompt Injection Defense: Neural-Heuristic Fusion, Multi-Modal Attachment Parsing, and Outbound Leakage Prevention")
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(17)
    r_title.font.color.rgb = RGBColor(26, 54, 93)

    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_before = Pt(0)
    p_auth.paragraph_format.space_after = Pt(2)
    r_auth = p_auth.add_run("Group 25 — Cybersecurity Case Study Implementation")
    r_auth.bold = True
    r_auth.font.name = "Times New Roman"
    r_auth.font.size = Pt(11)

    p_aff = doc.add_paragraph()
    p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aff.paragraph_format.space_before = Pt(0)
    p_aff.paragraph_format.space_after = Pt(2)
    r_aff = p_aff.add_run("Department of Computer Science and Cybersecurity | Cybersecurity Systems and ML Laboratory\nProject Repository: https://github.com/jhadiksha65/prompt-injection-detector")
    r_aff.italic = True
    r_aff.font.name = "Times New Roman"
    r_aff.font.size = Pt(9.5)
    r_aff.font.color.rgb = RGBColor(74, 85, 104)

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(14)
    r_meta = p_meta.add_run("Production Checkpoint: 05af2d4  |  Model SHA-256: c15a14cad0bdc9fa909a...  |  Decision Threshold: 0.3800")
    r_meta.font.name = "Times New Roman"
    r_meta.font.size = Pt(8.5)
    r_meta.font.color.rgb = RGBColor(113, 128, 150)

    # ==========================================
    # Abstract Callout Box
    # ==========================================
    tbl_abs = doc.add_table(rows=1, cols=1)
    tbl_abs.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_abs.autofit = False
    set_callout_borders(tbl_abs, "1A365D")
    c_abs = tbl_abs.cell(0, 0)
    c_abs.width = Inches(6.5)
    set_cell_shading(c_abs, "F7FAFC")
    set_cell_margins(c_abs, top=140, bottom=140, left=180, right=180)

    p_abs = c_abs.paragraphs[0]
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_before = Pt(0)
    p_abs.paragraph_format.space_after = Pt(4)
    r_absh = p_abs.add_run("Abstract—")
    r_absh.bold = True
    r_absh.font.name = "Times New Roman"
    r_absh.font.size = Pt(10)
    
    r_abst = p_abs.add_run(
        "Prompt injection represents the paramount security vulnerability in modern applications integrating Large Language Models (LLMs), "
        "encompassing direct prompt manipulation, indirect payload delivery through external documents, and unauthorized disclosure of sensitive internal context. "
        "In this paper, we present the design, implementation, and empirical evaluation of a production-ready, dual-layer prompt security middleware and gateway. "
        "Our architecture establishes an active perimeter around the language model: Layer 1 performs inbound threat screening before model invocation by fusing "
        "a calibrated, fine-tuned DistilBERT sequence classifier (R_ML) with a deterministic signature pattern engine (R_rule) at an operational decision threshold "
        "of θ = 0.3800 under a weighted scoring formulation: Rfused = 0.40 Rrule + 0.60 RML. "
        "To neutralize indirect injection, our inbound pipeline decouples prompt evaluation from multi-modal attachment ingestion (supporting DOCX, PDF, and optical "
        "character recognition via Tesseract), preserving fine-grained threat-source attribution (threat_source ∈ {User Prompt, Attachment, Both, None}). "
        "Inbound traffic is mapped to an authoritative nine-category threat taxonomy, accurately distinguishing malicious instructions from benign cybersecurity queries. "
        "Layer 2 inspects outbound LLM responses prior to egress, detecting system prompt disclosure, API credentials, and personally identifiable information (PII), "
        "automatically enforcing redaction or complete response withholding. The middleware provides an OpenAI-compatible reverse-proxy gateway (/v1/chat/completions) "
        "for systems such as Open WebUI and an asynchronous browser extension for client-side pre-submission interception. On an independent 3,000-sample balanced "
        "generalization benchmark, our hybrid detector achieves an accuracy of 98.73%, precision of 99.26%, recall of 98.20%, and F1-score of 0.9873 (overcoming the 8.73% "
        "recall of rule-only baselines), while maintaining 100% precision and 0.00% false-positive rate on an adversarial challenge holdout. The entire end-to-end "
        "implementation is validated by a 288-test automated regression suite with a 100% pass rate and sub-30ms inference latency on hardware-accelerated runtimes."
    )
    r_abst.font.name = "Times New Roman"
    r_abst.font.size = Pt(9.5)

    p_idx = c_abs.add_paragraph()
    p_idx.paragraph_format.space_before = Pt(3)
    p_idx.paragraph_format.space_after = Pt(0)
    r_idxh = p_idx.add_run("Index Terms—")
    r_idxh.bold = True
    r_idxh.font.name = "Times New Roman"
    r_idxh.font.size = Pt(9.5)
    r_idxt = p_idx.add_run("prompt injection, indirect prompt injection, LLM security, defense in depth, transformer classification, multi-modal ingestion, data leakage prevention, OpenAI gateway.")
    r_idxt.italic = True
    r_idxt.font.name = "Times New Roman"
    r_idxt.font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_sec_heading(title, number=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        full_title = f"{number} {title}".strip()
        run = p.add_run(full_title)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(26, 54, 93)

    def add_subsec_heading(title, letter=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        full_title = f"{letter} {title}".strip()
        run = p.add_run(full_title)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(45, 55, 72)

    def add_p(text, bold_prefix="", italic=False):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(10.5)
        r = p.add_run(text)
        r.italic = italic
        r.font.name = "Times New Roman"
        r.font.size = Pt(10.5)
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(10)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

    def add_numbered(num, text, bold_prefix=""):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        r_n = p.add_run(f"{num}. ")
        r_n.bold = True
        r_n.font.name = "Times New Roman"
        r_n.font.size = Pt(10)
        if bold_prefix:
            r_b = p.add_run(bold_prefix)
            r_b.bold = True
            r_b.font.name = "Times New Roman"
            r_b.font.size = Pt(10)
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        set_code_borders(tbl, "CBD5E0")
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_shading(cell, "F8FAFC")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        r = p.add_run(code_text)
        r.font.name = "Courier New"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(45, 55, 72)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ==========================================
    # Section 1: Introduction
    # ==========================================
    add_sec_heading("INTRODUCTION", "I.")
    add_p(
        "Language-model applications increasingly act as autonomous agents, customer service intermediaries, and internal business analytical copilots, routinely combining trusted developer instructions with untrusted user input and third-party document corpora. Prompt injection exploits this unified execution channel: because language models cannot intrinsically separate instructional code from passive data, an adversary can format malicious inputs to hijack model execution, bypass safety alignments, redirect agentic tool calls, or extract confidential operational context [1–3]. In the OWASP Top 10 for Large Language Model Applications, prompt injection (LLM01) and sensitive information disclosure (LLM06) represent the two most pervasive vulnerabilities facing generative enterprise deployments [12]."
    )
    add_p(
        "Attacks are broadly bifurcated into two vectors: (1) direct prompt injection, where the adversary directly enters instructions into the conversational interface, and (2) indirect prompt injection, where malicious payloads are embedded within third-party carrier artifacts—such as uploaded reports, resumes, PDFs, or scanned images—that are subsequently consumed by the application [2, 4]."
    )
    add_p(
        "Where applications process consequential tasks or possess access to confidential credentials and developer preambles, static heuristic filters are fundamentally insufficient: simple keyword matching fails against paraphrased attacks, synonym substitution, and encoding obfuscations [5, 8]. Conversely, deploying pure neural models without heuristic safeguards incurs excessive inference overhead and risks catastrophic false-positive rates on legitimate defensive security inquiries [6, 7]. Furthermore, securing the input alone does not prevent the model from inadvertently revealing sensitive API keys, database credentials, or system instructions if an evasion successfully breaches inbound defenses."
    )

    add_subsec_heading("Dual-Layer Defense Pipeline Architecture", "A.")
    add_code_block(
"""User Input & Optional Multi-Modal Document Attachment (PDF/DOCX/TXT/Image)
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Inbound Input Security Gateway                                │
│  ─────────────────────────────────────────────────────────────────────  │
│  • Input Preprocessing (Unicode normalization, zero-width, leetspeak)   │
│  • Decoupled Multi-Modal Parsing (PDF, DOCX, Tesseract OCR for images)  │
│  • Signature Pattern Engine (Heuristic Regex / Context Dampening)       │
│  • Fine-Tuned DistilBERT Transformer Classifier (256-token Head-Tail)   │
│  • Dual-Perspective Threat Fusion: Rfused = 0.40 Rrule + 0.60 RML       │
│  • Enforced Production Threshold: θ = 0.3800                            │
│  • 9-Category Threat Taxonomy Classification                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                      Safe (Rfused < 0.3800)?
                                     │
                     ┌───────────────┴───────────────┐
                    YES                              NO
                     │                               │
                     ▼                               ▼
     ┌──────────────────────────────┐ ┌───────────────────────────────────┐
     │ Downstream LLM Execution     │ │ Request Blocked Immediately       │
     │ (Ollama / OpenAI / Mock)     │ │ HTTP 200 (finish_reason: filter)  │
     │                              │ │ LLM is NEVER called (0 calls)     │
     └──────────────┬───────────────┘ └───────────────────────────────────┘
                    │
                    ▼ Raw AI Generated Output (Buffered)
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: Outbound Response Inspection & Leakage Guard                  │
│  ─────────────────────────────────────────────────────────────────────  │
│  • System Prompt Leakage & Preamble Disclosure Detection (Regex & tags) │
│  • Secret & Key Detection (sk-*, ghp_*, AIza*, DB URIs, Private Keys)   │
│  • Sensitive PII Pattern Scanning (SSN, Credit Cards, Email)            │
│  • Structural & Anomaly Validation (Empty check, repetition, truncation)│
│  • Automated Masking ([REDACTED_PII]) or Complete Response Withholding │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼ Delivered Response
                               End User / Client UI"""
    )

    add_subsec_heading("Key Research Contributions", "B.")
    add_numbered(1, "We design and implement a defense-in-depth security gateway coupling pre-execution inbound screening (Layer 1) with post-execution outbound response sanitization (Layer 2), guaranteeing that downstream LLMs are never invoked when an inbound threat is detected.", "Dual-Layer Perimeter Architecture: ")
    add_numbered(2, "We develop an isolated attachment parsing and optical character recognition (OCR) pipeline that extracts text from DOCX, PDF, and image files independently of user prompt text, preserving precise threat-source attribution (User Prompt, Attachment, or Both).", "Decoupled Multi-Modal Ingestion: ")
    add_numbered(3, "We formulate a dual-perspective risk-scoring engine (Rfused = 0.40 Rrule + 0.60 RML) that combines a 256-token head-tail DistilBERT sequence classifier with an extensive signature pattern bank, mapped onto an authoritative nine-category threat taxonomy that explicitly protects legitimate cybersecurity inquiries from over-defense.", "Calibrated Neural-Heuristic Fusion: ")
    add_numbered(4, "We conduct rigorous evaluations on an independent 3,000-sample balanced generalization benchmark, a 600-sample challenge holdout, and a 300-sample hard-negative suite. We demonstrate drop-in reverse-proxy integration via an OpenAI-compatible API (/v1/chat/completions), deploy a high-resilience browser extension with low-level DOM interception, and verify system integrity with a 288-test automated regression suite achieving a 100% pass rate.", "Empirical Systems Validation & Ecosystem Gateways: ")

    add_subsec_heading("Research Questions Formulation", "C.")
    add_bullet("How does hybrid neural-heuristic fusion compare to isolated rule-only and neural-only classifiers in minimizing false negatives while preserving high specificity?", "RQ1 (Component Fusion & Ablation): ")
    add_bullet("Can decoupled multi-modal parsing reliably detect indirect carrier injections in documents and images without contaminating prompt classification?", "RQ2 (Attachment & Carrier Generalization): ")
    add_bullet("Does the gateway strictly prevent LLM invocation on blocked inputs while maintaining fail-secure operation under degraded or missing model dependencies?", "RQ3 (Application Gating & Fail-Secure Invariants): ")
    add_bullet("Can real-time response inspection intercept system prompt preambles and credential disclosures without degrading legitimate model generation?", "RQ4 (Outbound Output Sanitization & Leakage Defense): ")

    # ==========================================
    # Section 2: Threat Model and Taxonomy
    # ==========================================
    add_sec_heading("THREAT MODEL AND THREAT TAXONOMY", "II.")
    add_subsec_heading("Adversary Capabilities and Protected Assets", "A.")
    add_p(
        "We model an untrusted operational environment where adversaries interact with generative applications via direct conversational interfaces, REST endpoints, or carrier documents (e.g., vendor contracts, resumes, financial reports, scanned image receipts). The adversary seeks to override developer-defined operational guidelines, circumvent safety alignments, extract confidential system prompts, exfiltrate environment secrets or database credentials, or induce malicious agentic side effects."
    )
    add_p(
        "The protected assets comprise: (1) System Context & Developer Instructions: proprietary preambles and organizational policy constraints; (2) Environment Credentials: API keys (sk-*, ghp_*, AIza*), database URIs, and private cryptographic keys; (3) User Privacy: PII including SSNs, credit cards, and confidential emails; and (4) Computational Budget: protection of the LLM generation budget from denial-of-wallet and infinite token loops."
    )

    add_subsec_heading("Authoritative Nine-Category Threat Taxonomy", "B.")
    add_p(
        "Prior heuristic baselines frequently misclassified all attacks under generic 'Direct Prompt Injection' or failed into 'Unclassified Suspicious Prompt'. Our production engine implements an authoritative nine-category taxonomy defined in backend/prompt_security/threat_taxonomy.py, detailed in Table I."
    )

    # Table 1: Threat Taxonomy
    tbl_tax = doc.add_table(rows=1, cols=4)
    tbl_tax.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_tax.autofit = False
    set_table_borders(tbl_tax)
    col_w_tax = [0.6, 2.2, 2.7, 1.0]
    add_header_row(tbl_tax, col_w_tax, ["Idx", "Threat Category", "Scope & Behavioral Definition", "Action"])
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
        add_data_row(tbl_tax, col_w_tax, [c1, c2, c3, c4], is_even=(idx % 2 == 1),
                     aligns=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER])

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ==========================================
    # Section 3: Related Work
    # ==========================================
    add_sec_heading("RELATED WORK", "III.")
    add_p(
        "Early foundational research cataloged direct prompt injection and system prompt extraction attacks against early instruction-tuned language models [1]. Greshake et al. and Liu et al. demonstrated that indirect prompt injection represents a systemic vulnerability for applications that process third-party web content, emails, and uploaded documents [2, 3]. Subsequent benchmarks expanded from static binary classification to complex agentic environments: InjecAgent evaluated indirect injections in tool-integrated agent frameworks [4], and AgentDojo formalized dynamic benchmarking with adaptive adversarial attacks and defenses [5]."
    )
    add_p(
        "CAPTURE highlighted the critical challenge of context-aware evaluation and over-defense, showing that naive classifiers often block legitimate user requests [6]. Cui et al. provided an extensive empirical reassessment across diverse application contexts, demonstrating that static keyword filters degrade significantly under distribution shift [7]. PromptRobust evaluated model robustness across adversarial phrasing perturbations [8]. In model distillation, DistilBERT established that 40% smaller distilled transformer models retain 97% of BERT's language comprehension capabilities while executing 60% faster [9]. In output security, Carlini et al. demonstrated that language models memorize and inadvertently leak training data and operational secrets [10]. Emerging governance frameworks, including NIST AI 600-1 [11] and the OWASP GenAI Top 10 [12], emphasize defense-in-depth architectures spanning both pre-invocation filtering and post-generation egress validation."
    )

    # ==========================================
    # Section 4: System Architecture
    # ==========================================
    add_sec_heading("SYSTEM ARCHITECTURE AND IMPLEMENTATION", "IV.")
    add_subsec_heading("Input Normalization & Head-Tail Tokenization", "A.")
    add_p(
        "Adversaries frequently position attack instructions either at the very beginning (head override) or at the end of large text blocks (tail carrier injection). Standard truncation to 256 tokens from the beginning discards the end of the text. As implemented in backend/prompt_security/preprocessing/token_preprocessing.py, our pipeline extracts 127 tokens from the sequence head and 127 tokens from the sequence tail, combining them with special tokens ([CLS] and [SEP]):"
    )
    add_p("T_input = [ [CLS], t_1, ..., t_127, [SEP], t_{N-126}, ..., t_N, [SEP] ]", italic=True)

    add_subsec_heading("Inbound Layer 1 Engine: Neural-Heuristic Threat Fusion", "B.")
    add_p(
        "Layer 1 combines the continuous risk outputs of the heuristic signature engine (R_rule in [0, 100]) and the fine-tuned DistilBERT transformer (R_ML = 100 * P(malicious) in [0, 100]):"
    )
    add_p("R_fused = 0.40 * R_rule + 0.60 * R_ML", bold_prefix="Threat Fusion Formula: ")
    add_p(
        "Requests are mapped to four security decision bands: LOW (0 to 29: ALLOW), MEDIUM (30 to 59: WARNING - logged to audit database; benign requests proceed), HIGH (60 to 79: BLOCK), and CRITICAL (80 to 100: BLOCK). Whenever R_fused >= 38.0 (calibrated decision threshold θ = 0.3800) or either constituent module emits a critical attack override, the request is immediately blocked, guaranteeing zero downstream LLM invocation."
    )

    add_subsec_heading("Decoupled Attachment Parsing and Threat Attribution", "C.")
    add_p(
        "The gateway ingests structured documents (DOCX, PDF, TXT) and raster images (PNG, JPG). Document streams are parsed using pypdf and python-docx to extract text paragraphs, tables, and embedded XML payloads. Image files are scanned using Tesseract OCR via pytesseract and Pillow. Threat scores are computed independently for prompt and attachment channels: R_overall = max(R_prompt, R_attachment). The system outputs an explicit provenance label: threat_source in {User Prompt, Attachment, Both, None}. This prevents benign user questions accompanied by malicious documents from contaminating user intent metrics."
    )

    add_subsec_heading("Outbound Layer 2 Guard: Response Sanitization", "D.")
    add_p(
        "When an approved prompt reaches the downstream LLM (local Ollama llama3.2:3b, OpenAI gpt-4o, or offline mock simulation), the generated output is buffered and evaluated by Layer 2 before egress:"
    )
    add_bullet("Scans for preamble leakage patterns, verbatim system header exposure, and enclosed system markup tags (<system>, [SYSTEM_PROMPT]). Responses with score >= 85 trigger a BLOCK decision, completely withholding the response and returning a secure alert placeholder.", "1. System Prompt Disclosure Detection: ")
    add_bullet("Detects live credential signatures including OpenAI API keys (sk-*), GitHub tokens (ghp_*), Google Cloud keys (AIza*), private cryptographic keys (BEGIN PRIVATE KEY), database connection URIs (postgres://...), and authorization bearer tokens.", "2. Secret & Key Detection: ")
    add_bullet("Identifies Social Security numbers, credit card sequences, and personal email addresses, automatically substituting matches with [REDACTED_PII] and returning decision: 'MASK'.", "3. PII Redaction & Masking: ")
    add_bullet("Enforces length boundaries (truncating responses exceeding 8,000 characters) and detects infinite token generation loops (token uniqueness ratio < 0.15 -> BLOCK).", "4. Structural & Anomaly Validation: ")

    add_subsec_heading("Production Ecosystem Gateways", "E.")
    add_p(
        "The service exposes POST /api/v1/chat/completions (aliased to /v1/chat/completions), providing direct drop-in compatibility for Open WebUI, LangChain, and organizational agents. Crucially, streaming raw tokens (stream=true) is prohibited by policy: the gateway buffers tokens to enable complete Layer 2 whole-response inspection, preventing incremental leakage. On Layer 1 block, it returns standard OpenAI response structures with finish_reason: 'content_filter'. In parallel, an unpacked Chromium browser extension registers low-level pointerdown and keydown event listeners on ProseMirror divs and textareas, preventing prompt submissions until security clearance is confirmed."
    )

    # ==========================================
    # Section 5: Dataset Lineage
    # ==========================================
    add_sec_heading("DATASET LINEAGE AND MODEL PROVENANCE", "V.")
    add_p(
        "The training data underwent three distinct development stages documented in docs/DATASET_LINEAGE.md (Table II). Phase 1 established initial baselines across 14,317 samples. Phase 2 expanded into a balanced multi-domain corpus of 15,500 samples. Phase 3 (V3) resolved short prompt injections (<20 characters, e.g., 'reset context') and conversational false positives through a dual-reviewer human annotation protocol with fail-closed dispute adjudication, producing 16,224 training samples (train_v3.csv) and 1,500 validation samples (validation_v3.csv)."
    )

    # Table 2: Dataset Lineage
    tbl_data = doc.add_table(rows=1, cols=5)
    tbl_data.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_data.autofit = False
    set_table_borders(tbl_data)
    col_w_data = [2.2, 0.9, 0.9, 0.9, 1.6]
    add_header_row(tbl_data, col_w_data, ["Dataset Split / File", "Total Rows", "Benign (0)", "Malicious (1)", "Stage / Role"])
    dataset_rows = [
        ("train.csv", "14,317", "6,979", "7,338", "Phase 1 Base Train"),
        ("validation.csv", "3,068", "1,496", "1,572", "Phase 1 Base Val"),
        ("test.csv", "3,069", "1,496", "1,573", "Phase 1 Base Test"),
        ("train_generalization.csv", "15,500", "7,750", "7,750", "Phase 2 Train Split"),
        ("validation_generalization.csv", "3,000", "1,500", "1,500", "Phase 2 Val Split"),
        ("test_generalization.csv", "3,000", "1,500", "1,500", "Phase 2 Generalization Benchmark"),
        ("**train_v3.csv**", "**16,224**", "**8,112**", "**8,112**", "**V3 Production Train**"),
        ("**validation_v3.csv**", "**1,500**", "**750**", "**750**", "**V3 Production Val**"),
        ("challenge_holdout.csv", "600", "300", "300", "Zero-Shot Evasion Test"),
        ("hard_negatives_expanded.csv", "300", "150", "150", "Expanded Hard-Negative"),
        ("hard_negatives_curated.csv", "300", "150", "150", "Curated Hard-Negative"),
        ("short_prompt_eval.csv", "200", "100", "100", "Short-Prompt (<20 char) Test"),
    ]
    for idx, (c1, c2, c3, c4, c5) in enumerate(dataset_rows):
        add_data_row(tbl_data, col_w_data, [c1, c2, c3, c4, c5], is_even=(idx % 2 == 1),
                     aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_p(
        "Model Cryptographic Identity: The production model artifact is stored at experiments/distilbert/distilbert_model_augmented.pt with exact file size 267,856,803 bytes (~255.45 MB) and SHA-256 digest c15a14cad0bdc9fa909a52c667bff9430e098aebb7c11b375df3d50ae1f0ea93. The 330-byte difference relative to early notes represents the difference between the Phase 2 backup (267,856,473 bytes) and the promoted V3 production model (267,856,803 bytes)."
    )

    # ==========================================
    # Section 6: Experimental Evaluation
    # ==========================================
    add_sec_heading("EXPERIMENTAL EVALUATION AND RESULTS", "VI.")
    add_subsec_heading("RQ1: Component Contribution and Ablation Analysis", "A.")
    add_p(
        "We evaluated the deterministic Rule-Only Baseline, the DistilBERT Neural Classifier (R_ML), and the Fused Hybrid Middleware (R_fused) across three independent holdout sets at threshold θ = 0.3800. Results are summarized in Table III."
    )

    # Table 3: Performance Ablation Table
    tbl_abl = doc.add_table(rows=1, cols=9)
    tbl_abl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_abl.autofit = False
    set_table_borders(tbl_abl)
    col_w_abl = [1.5, 1.4, 0.5, 0.5, 0.5, 0.5, 0.6, 0.5]
    # adjust for 9 cols
    col_w_abl = [1.4, 1.4, 0.45, 0.4, 0.45, 0.45, 0.65, 0.65, 0.65]
    add_header_row(tbl_abl, col_w_abl, ["Corpus (N)", "Regime", "TN", "FP", "FN", "TP", "Acc.", "Prec.", "Recall"])
    abl_data = [
        ("Generalization\n(3,000)", "Rule-Only (>30)", "1,500", "0", "1,369", "131", "0.5437", "1.0000", "0.0873"),
        ("Generalization\n(3,000)", "Rule-Only (>60)", "1,500", "0", "1,375", "125", "0.5417", "1.0000", "0.0833"),
        ("Generalization\n(3,000)", "**DistilBERT (ML)**", "**1,489**", "**11**", "**27**", "**1,473**", "**0.9873**", "**0.9926**", "**0.9820**"),
        ("Generalization\n(3,000)", "**Fused Hybrid**", "**1,489**", "**11**", "**18**", "**1,482**", "**0.9903**", "**0.9926**", "**0.9880**"),
        ("Challenge Holdout\n(600)", "Rule-Only (>30)", "300", "0", "280", "20", "0.5333", "1.0000", "0.0667"),
        ("Challenge Holdout\n(600)", "**DistilBERT (ML)**", "**300**", "**0**", "**7**", "**293**", "**0.9883**", "**1.0000**", "**0.9767**"),
        ("Challenge Holdout\n(600)", "**Fused Hybrid**", "**300**", "**0**", "**5**", "**295**", "**0.9917**", "**1.0000**", "**0.9833**"),
        ("Hard Negatives\n(300)", "Rule-Only (>30)", "144", "6", "141", "9", "0.5100", "0.6000", "0.0600"),
        ("Hard Negatives\n(300)", "**DistilBERT (ML)**", "**133**", "**17**", "**10**", "**140**", "**0.9100**", "**0.8917**", "**0.9333**"),
        ("Hard Negatives\n(300)", "**Fused Hybrid**", "**137**", "**13**", "**7**", "**143**", "**0.9333**", "**0.9167**", "**0.9533**"),
    ]
    for idx, (c1, c2, c3, c4, c5, c6, c7, c8, c9) in enumerate(abl_data):
        add_data_row(tbl_abl, col_w_abl, [c1, c2, c3, c4, c5, c6, c7, c8, c9], is_even=(idx % 2 == 1),
                     aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_p(
        "Key Finding: Rule-only heuristics fail against adversarial prompts (8.73% recall on generalization test). DistilBERT elevates recall to 98.20% with F1 = 0.9873. On the Challenge Holdout, the neural classifier achieves 98.83% accuracy with 0 false positives (FP = 0, FPR = 0.00%). Hybrid fusion achieves peak performance (F1 = 0.9903 on Generalization, 0.9916 on Challenge Holdout) by combining regex floor guarantees with deep semantic attention."
    )

    add_subsec_heading("Per-Category Attack Resilience", "B.")
    add_p(
        "Category-level breakdown on the 3,000-sample generalization benchmark: Credential Harvesting (N=98): 100.0% accuracy; Indirect Carrier Injection (N=44): 100.0% accuracy; Obfuscation & Encoding (N=215): 100.0% accuracy; System Prompt Extraction (N=78): 100.0% accuracy; Direct Instruction Override (N=922): 99.1% accuracy; Benign Coding/STEM (N=396): 100.0% accuracy; Benign Cybersecurity (N=39): 100.0% accuracy; and Adversarial Jailbreaks (N=143): 86.7% accuracy."
    )

    add_subsec_heading("RQ2: Multi-Modal Attachment Parsing Performance", "C.")
    add_p(
        "On the Challenge Holdout set, injection placement testing yielded: Tail Injections (N=50): 100.0% detected (FN=0); Head Injections (N=25): 80.0% detected (FN=5); and Long Benign Documents (N=25): 100.0% allowed (FP=0). In dedicated tests (test_docx_indirect_injection.py and test_attachments_image_ocr.py), malicious instructions concealed within reports and scanned receipts were successfully detected by the decoupled attachment pipeline with threat_source = Attachment, preserving user prompt evaluation accuracy."
    )

    add_subsec_heading("RQ3: Application Gating & Automated Verification Suite", "D.")
    add_p(
        "To evaluate whether the gateway strictly enforces security decisions and maintains fail-secure properties, we executed the full automated test suite using pytest. The test suite comprises 288 tests across 17 modules, achieving a 100% pass rate (288 passed, 0 failed, 0 skipped, execution time: 458s), as shown in Table IV."
    )

    # Table 4: Automated Test Suite Breakdown
    tbl_tests = doc.add_table(rows=1, cols=3)
    tbl_tests.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_tests.autofit = False
    set_table_borders(tbl_tests)
    col_w_tests = [2.8, 1.0, 2.7]
    add_header_row(tbl_tests, col_w_tests, ["Test Module / Subsystem", "Tests", "Functionality Verified"])
    test_rows = [
        ("test_admin_auth.py", "30", "Admin security, password hashing, session authentication"),
        ("test_attachments.py", "34", "PDF/DOCX extraction, size limits, indirect injection gating"),
        ("test_attachments_image_ocr.py", "19", "Tesseract OCR parsing, raster carrier injection defense"),
        ("test_block_dialog_ui.py", "13", "Viewport-constrained modal, responsive action buttons"),
        ("test_detection.py", "14", "Layer 1 detection, threshold calibration, edge cases"),
        ("test_docx_indirect_injection.py", "4", "DOCX indirect injection defense, pre-invocation gating"),
        ("test_dual_layer.py", "6", "Dual-layer end-to-end integration, decision propagation"),
        ("test_extension_interception.py", "15", "Browser DOM interception, ProseMirror, concurrency locks"),
        ("test_extension_parity.py", "28", "Browser extension parity with Analyzer API verdicts"),
        ("test_external_llm_demo.py", "9", "External LLM provider client, failover, model selection"),
        ("test_integration_center.py", "9", "Gateway metadata, connection testing, incident filtering"),
        ("test_layer2_demo.py", "16", "Layer 2 response inspection, secret masking, simulated leaks"),
        ("test_llm_client.py", "6", "LLM client routing (Ollama, OpenAI, local mock)"),
        ("test_model_integrity.py", "25", "Checkpoint SHA-256 verification, fail-secure fallback"),
        ("test_open_webui_deploy.py", "8", "Open WebUI reverse proxying, deployment verification"),
        ("test_openai_gateway_integration.py", "12", "/v1/chat/completions payload schema, streaming policy"),
        ("test_scenarios_a_to_h.py", "10", "End-to-end verification of Scenarios A through H"),
        ("test_threat_taxonomy_nine_categories.py", "14", "Complete 9-category taxonomy classification & fallback"),
        ("test_ui_navigation_and_themes.py", "7", "Theme switching, dark mode, UI navigation consistency"),
        ("test_web_ui_integration.py", "9", "Web routes, security dashboard, incident logging"),
        ("**Total Automated Regression Suite**", "**288**", "**100.0% Pass Rate (All 288 tests passed cleanly)**"),
    ]
    for idx, (c1, c2, c3, ) in enumerate(test_rows):
        add_data_row(tbl_tests, col_w_tests, [c1, c2, c3], is_even=(idx % 2 == 1),
                     aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.LEFT])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_p(
        "Zero Downstream Invocations: In integration tests spanning both direct HTTP requests and the OpenAI gateway (test_scenarios_a_to_h.py and test_openai_gateway_integration.py), spy assertions verified that whenever Layer 1 emitted a BLOCK decision, the downstream LLM client was called exactly zero times (N = 0)."
    )

    add_subsec_heading("RQ4: Outbound Output Sanitization Performance", "E.")
    add_p(
        "Layer 2 response inspection was tested across synthetic leak injection scenarios: (1) Credential Leakage Interception: synthetic API keys (sk-live...) were intercepted and withheld in 100% of test runs, with raw secrets appearing in 0.0% of client outputs; (2) PII Masking: SSNs, credit cards, and emails were successfully redacted with [REDACTED_PII] under decision: 'MASK' without suppressing surrounding text; and (3) Benign Transparency: safe prompts (e.g., 'What is climate change?') delivered genuine model responses with zero false blocks."
    )

    add_subsec_heading("Inference Latency Profile", "F.")
    # Table 5: Latency
    tbl_lat = doc.add_table(rows=1, cols=4)
    tbl_lat.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_lat.autofit = False
    set_table_borders(tbl_lat)
    col_w_lat = [2.8, 1.2, 1.2, 1.3]
    add_header_row(tbl_lat, col_w_lat, ["Pipeline Component", "Apple MPS", "NVIDIA CUDA", "Standard x86 CPU"])
    lat_rows = [
        ("Input Normalization & Head-Tail Tokenization", "1.1 ms", "1.0 ms", "1.8 ms"),
        ("Heuristic Signature Engine (R_rule)", "3.2 ms", "3.1 ms", "3.9 ms"),
        ("DistilBERT Transformer Classifier (R_ML)", "24.6 ms", "18.2 ms", "78.4 ms"),
        ("Threat Fusion & Decision Gate", "0.4 ms", "0.4 ms", "0.6 ms"),
        ("**Total Inbound Layer 1 Latency**", "**29.3 ms**", "**22.7 ms**", "**84.7 ms**"),
        ("Layer 2 Response Regex & PII Scan", "3.8 ms", "3.5 ms", "4.2 ms"),
        ("Layer 2 Structural & Repetition Validation", "0.3 ms", "0.3 ms", "0.4 ms"),
    ]
    for idx, (c1, c2, c3, c4) in enumerate(lat_rows):
        add_data_row(tbl_lat, col_w_lat, [c1, c2, c3, c4], is_even=(idx % 2 == 1),
                     aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.RIGHT])

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ==========================================
    # Section 7: Discussion
    # ==========================================
    add_sec_heading("DISCUSSION AND SECURITY ANALYSIS", "VII.")
    add_subsec_heading("Addressing the Research Questions", "A.")
    add_bullet("Rule-only detection is fundamentally inadequate against modern adversarial prompts (8.73% recall). Neural transformer classification elevates recall to 98.20%, and hybrid fusion achieves optimal robustness (98.80% recall, 99.26% precision) by combining regex floor guarantees with deep semantic attention.", "RQ1 (Fusion): ")
    add_bullet("Decoupling attachment parsing from user prompt scoring isolates carrier attacks and maintains 100% detection on tail carrier injections, preserving precise threat-source attribution.", "RQ2 (Attachments): ")
    add_bullet("Automated test assertions verify that downstream LLMs are never invoked when input risk exceeds θ = 0.3800, and cryptographic hash checking ensures fail-secure degradation to rule-only heuristics if model weights are unavailable.", "RQ3 (Application Gating): ")
    add_bullet("Layer 2 inspection successfully intercepts system prompt leaks, redacts PII, and suppresses credentials without compromising benign model generation.", "RQ4 (Response Protection): ")

    add_subsec_heading("The Necessity of Dual-Layer Architecture", "B.")
    add_p(
        "Our findings demonstrate that neither inbound prompt screening nor outbound output filtering is sufficient in isolation. Relying solely on inbound screening leaves applications vulnerable to model hallucinations, training-data extraction [10], or novel zero-day prompt encodings that circumvent the classifier. Conversely, relying solely on outbound output filtering forces applications to incur the financial and computational cost of invoking the LLM for every malicious payload. Our dual-layer perimeter provides true defense-in-depth: Layer 1 minimizes compute expenditure and eliminates prompt hijacking, while Layer 2 provides a fail-safe backstop against sensitive data leakage."
    )

    add_subsec_heading("Policy Implications of Token Streaming", "C.")
    add_p(
        "A significant systems insight involves token streaming. While streaming improves perceived user responsiveness, it fundamentally undermines output security: once tokens egress the gateway, credential leaks and system preambles cannot be revoked. Our gateway enforces an atomic buffer-and-scan egress policy, illustrating that high-assurance LLM security requires non-streaming egress architectures."
    )

    # ==========================================
    # Section 8: Limitations
    # ==========================================
    add_sec_heading("LIMITATIONS AND RESPONSIBLE USE", "VIII.")
    add_p(
        "Limitations: (1) Adversarial Drift: highly creative, multi-turn adversarial jailbreaks and foreign-language obfuscations can challenge sequence classifiers. Continuous retraining and dynamic threshold calibration remain essential. (2) OCR Resolution Limits: image OCR accuracy depends on raster clarity; heavily distorted, low-contrast, or steganographic instructions may evade standard Tesseract extraction. (3) Dynamic Canary Tokens: in the current release, Layer 2 operates via deterministic regex signatures and structural checks. Enterprise dynamic canary tracking (generating ephemeral per-session tokens) is identified as a valuable future enhancement."
    )
    add_p(
        "Responsible Disclosure & Privacy: All penetration testing prompts used in this research were evaluated in isolated local testing environments. SQLite audit logging stores prompt snippets and client IP addresses for security forensics; production deployments should implement rigorous data retention and access-control policies."
    )

    # ==========================================
    # Section 9: Conclusion
    # ==========================================
    add_sec_heading("CONCLUSION", "IX.")
    add_p(
        "This paper presented the design, implementation, and empirical evaluation of a dual-layer prompt security middleware and gateway defending LLM applications against direct injection, multi-modal carrier injection, and outbound data leakage. By integrating a fine-tuned DistilBERT transformer with signature heuristics at a calibrated threshold (θ = 0.3800), our system achieves 98.73% accuracy and 98.20% recall on an independent 3,000-sample generalization benchmark, transforming a weak rule-only baseline into a high-assurance security perimeter. With decoupled attachment extraction, an authoritative nine-category threat taxonomy, OpenAI-compatible gateway reverse proxying, a resilient browser extension, and a 288-test automated regression suite with a 100% pass rate, this work demonstrates that robust, low-latency prompt security can be realized in production generative AI systems."
    )

    # ==========================================
    # References
    # ==========================================
    add_sec_heading("REFERENCES", "")
    refs = [
        "[1] F. Perez and I. Ribeiro, 'Ignore previous prompt: Attack techniques for language models,' arXiv preprint arXiv:2211.09527, 2022.",
        "[2] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, 'Not what you\\'ve signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection,' in Proc. 16th ACM Workshop on Artificial Intelligence and Security (AISEC), 2023, pp. 79–90, doi: 10.1145/3605764.3623985.",
        "[3] Y. Liu, G. Deng, Z. Xu, Y. Li, Y. Zheng, Y. Zhang, L. Zhao, T. Zhang, and Y. Liu, 'Prompt injection attack against LLM-integrated applications,' arXiv preprint arXiv:2306.05499, 2023.",
        "[4] Q. Zhan, Z. Liang, Z. Ying, and D. Kang, 'InjecAgent: Benchmarking indirect prompt injections in tool-integrated large language model agents,' in Findings of the Association for Computational Linguistics: ACL 2024, 2024, pp. 10471–10506, doi: 10.18653/v1/2024.findings-acl.624.",
        "[5] E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer, and F. Tramèr, 'AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,' in Advances in Neural Information Processing Systems (NeurIPS), vol. 37, 2024.",
        "[6] G. Kholkar and R. Ahuja, 'CAPTURE: Context-aware prompt injection testing and robustness enhancement,' in Proc. 1st Workshop on LLM Security, 2025, pp. 176–188.",
        "[7] C. Cui, Y. Wu, M. Backes, and Y. Zhang, 'Rethinking assessments of prompt injection attacks,' in Findings of the Association for Computational Linguistics: ACL 2026, 2026, pp. 23773–23799, doi: 10.18653/v1/2026.findings-acl.1191.",
        "[8] K. Zhu, J. Wang, J. Zhou, Z. Wang, H. Chen, Y. Wang, L. Yang, W. Ye, N. Zhang, Y. Du, X. Xie, and Y. Hao, 'PromptRobust: Towards evaluating the robustness of large language models on adversarial prompts,' arXiv preprint arXiv:2306.04528, 2023.",
        "[9] V. Sanh, L. Debut, J. Chaumond, and T. Wolf, 'DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter,' arXiv preprint arXiv:1910.01108, 2019.",
        "[10] N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, U. Erlingsson, A. Oprea, and C. Raffel, 'Extracting training data from large language models,' in Proc. 30th USENIX Security Symposium, 2021, pp. 2633–2650.",
        "[11] C. Autio et al., 'Artificial intelligence risk management framework: Generative artificial intelligence profile,' NIST Special Publication AI 600-1, 2024, doi: 10.6028/NIST.AI.600-1.",
        "[12] OWASP GenAI Security Project, 'OWASP Top 10 for Large Language Model Applications and Generative AI 2025,' OWASP Foundation, Oct. 2025. [Online]. Available: https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    ]
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.left_indent = Inches(0.3)
        p_ref.paragraph_format.first_line_indent = Inches(-0.3)
        p_ref.paragraph_format.space_before = Pt(1)
        p_ref.paragraph_format.space_after = Pt(3)
        r_ref = p_ref.add_run(ref)
        r_ref.font.name = "Times New Roman"
        r_ref.font.size = Pt(8.5)

    # Save output
    out_dir = "paper"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "conference_paper.docx")
    doc.save(out_path)
    print(f"Successfully generated Word document: {out_path} ({os.path.getsize(out_path):,} bytes)")

    # Also copy to Desktop so the user can easily find it on their Desktop!
    desktop_path = "/Users/omikashrestha/Desktop/conference_paper.docx"
    try:
        import shutil
        shutil.copy2(out_path, desktop_path)
        print(f"Also copied to user Desktop: {desktop_path}")
    except Exception as e:
        print(f"Note: Desktop copy skipped: {e}")

if __name__ == "__main__":
    main()
