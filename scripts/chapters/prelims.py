"""
scripts/chapters/prelims.py
Generates the exact preliminary pages for Symbiosis Institute of Technology.
Every section occupies its own individual page with explicit page breaks.
"""

def get_prelims_html(logo_path):
    return f"""
<!-- PAGE 1: TITLE PAGE -->
<div class="cover-page">
    <div style="font-size: 14pt; font-weight: bold; margin-bottom: 6pt;">A PROJECT REPORT</div>
    <div style="font-size: 12pt; font-weight: bold; margin-bottom: 10pt;">ON</div>
    
    <div class="cover-title">
        “PROMPT SECURITY FOR ORGANIZATIONAL LARGE LANGUAGE MODELS: A DUAL-LAYER PROMPT INJECTION DETECTION AND RESPONSE SECURITY FRAMEWORK”
    </div>
    
    <div class="cover-sub">
        A project report submitted in partial fulfillment of the requirements for the degree of<br>
        Bachelor of Technology in Computer Science & Engineering
    </div>
    
    <div class="cover-degree">
        BACHELOR OF TECHNOLOGY<br>
        IN<br>
        COMPUTER SCIENCE & ENGINEERING
    </div>
    
    <div style="font-size: 12pt; font-weight: bold; margin-top: 10pt; margin-bottom: 6pt;">Submitted By</div>
    
    <table class="cover-table">
        <tr>
            <th style="width: 55%; text-align: left; padding-left: 15pt;">Student Name</th>
            <th style="width: 45%; text-align: center;">Permanent Registration No. (PRN)</th>
        </tr>
        <tr>
            <td style="padding-left: 15pt; font-weight: bold;">Omika Shrestha</td>
            <td style="text-align: center;">21070122147</td>
        </tr>
        <tr>
            <td style="padding-left: 15pt; font-weight: bold;">Diksha Jha</td>
            <td style="text-align: center;">21070122127</td>
        </tr>
        <tr>
            <td style="padding-left: 15pt; font-weight: bold;">Group 25 Research Scholar</td>
            <td style="text-align: center;">21070122165</td>
        </tr>
        <tr>
            <td style="padding-left: 15pt; font-weight: bold;">Group 25 Research Scholar</td>
            <td style="text-align: center;">21070122169</td>
        </tr>
    </table>
    
    <div style="font-size: 12pt; font-weight: bold; margin-top: 12pt; margin-bottom: 4pt;">UNDER THE GUIDANCE OF</div>
    <div style="font-size: 12pt; font-weight: bold;">Mrs. Usha Anirudhha Jogalekar</div>
    <div style="font-size: 11pt; margin-top: 2pt;">
        Assistant Professor<br>
        Department of Computer Engineering<br>
        Symbiosis Institute of Technology, Pune
    </div>
    
    <div style="margin-top: 16pt;">
        <img class="cover-logo" src="{logo_path}" alt="Symbiosis Logo">
        <div style="font-size: 9.5pt; color: #333; margin-top: 4pt;">
            Pune – 412115, Maharashtra State, India | https://www.sitpune.edu.in/
        </div>
        <div style="font-size: 12pt; font-weight: bold; margin-top: 6pt;">
            DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING<br>
            ACADEMIC YEAR 2026-27
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- PAGE 2: CERTIFICATE -->
<div class="cert-header">
    <img class="cover-logo" src="{logo_path}" alt="Symbiosis Logo" style="width: 3.5in; margin-top: 10pt;">
    <div style="font-size: 9.5pt; color: #333;">
        Pune – 412115, Maharashtra State, India | https://www.sitpune.edu.in/
    </div>
    <div style="font-size: 12pt; font-weight: bold; margin-top: 6pt; border-bottom: 2px solid #800000; padding-bottom: 6pt;">
        DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
    </div>
</div>

<div class="cert-title">CERTIFICATE</div>

<p style="text-align: justify; font-size: 12pt; line-height: 1.8; margin-top: 30pt;">
This is to certify that the Project work entitled <strong>“Prompt Security for Organizational Large Language Models: A Dual-Layer Prompt Injection Detection and Response Security Framework”</strong> is carried out by <strong>Omika Shrestha (PRN: 21070122147), Diksha Jha (PRN: 21070122127), and Project Group 25</strong> in partial fulfillment for the award of the degree of <strong>Bachelor of Technology in Computer Science & Engineering</strong>, Symbiosis International (Deemed University), Pune during the academic year <strong>2026-2027</strong>.
</p>

<table class="signature-table" style="margin-top: 80pt; width: 100%;">
    <tr>
        <td style="width: 50%; text-align: center;">
            ___________________________<br>
            <strong>Mrs. Usha Anirudhha Jogalekar</strong><br>
            <span style="font-size: 10pt; font-weight: normal;">Guide, Assistant Professor<br>Department of Computer Engineering<br>Symbiosis Institute of Technology, Pune</span>
        </td>
        <td style="width: 50%; text-align: center;">
            ___________________________<br>
            <strong>Dr. Sonali Kothari</strong><br>
            <span style="font-size: 10pt; font-weight: normal;">Head, Department of CSE<br>Symbiosis Institute of Technology, Pune</span>
        </td>
    </tr>
</table>

<div class="page-break"></div>

<!-- PAGE 3: DECLARATION -->
<div class="cert-title" style="margin-top: 25pt;">DECLARATION</div>

<p style="line-height: 1.8; margin-top: 25pt;">
We hereby declare that the project titled <strong>“Prompt Security for Organizational Large Language Models: A Dual-Layer Prompt Injection Detection and Response Security Framework”</strong> submitted to Symbiosis Institute of Technology, Constituent of Symbiosis International (Deemed University) Pune for the award of the degree of Bachelor of Technology in Computer Science & Engineering is a result of original research carried out by us under the supervision of <strong>Mrs. Usha Anirudhha Jogalekar</strong>, Assistant Professor, Department of Computer Engineering.
</p>

<p style="line-height: 1.8;">
We understand that the report may be made electronically available to the public. It is further declared that the project report or any part thereof has not been previously submitted to any University or Institute for the award of any degree or diploma.
</p>

<div style="margin-top: 30pt; line-height: 2.0; font-size: 11.5pt;">
    <strong>Name(s) of Student(s):</strong> Omika Shrestha, Diksha Jha, and Group 25 Scholars<br>
    <strong>Permanent Registration Numbers (PRNs):</strong> 21070122147, 21070122127, 21070122165, 21070122169<br>
    <strong>Degree:</strong> Bachelor of Technology in Computer Science & Engineering<br>
    <strong>Department:</strong> Department of Computer Science & Engineering<br>
    <strong>Title of the Project:</strong> Prompt Security for Organizational Large Language Models: A Dual-Layer Prompt Injection Detection and Response Security Framework
</div>

<div style="margin-top: 60pt;">
    ____________________________________________________<br>
    <strong>(Signatures of all the Students of Project Group 25)</strong><br><br>
    <strong>Date:</strong> 19th October 2026<br>
    <strong>Place:</strong> SIT, Pune
</div>

<div class="page-break"></div>

<!-- PAGE 4: ACKNOWLEDGEMENT -->
<div class="cert-title" style="margin-top: 25pt;">ACKNOWLEDGEMENT</div>

<p style="line-height: 1.7; margin-top: 20pt;">
We want to express our sincere gratitude to everyone who supported us throughout this engineering capstone research project. First and foremost, we would like to thank our project guide, <strong>Mrs. Usha Anirudhha Jogalekar</strong>, Assistant Professor, Department of Computer Engineering, for her invaluable guidance, encouragement, and constructive feedback throughout the design, implementation, and empirical verification of our prompt security framework. She has been a constant source of inspiration and motivation for us.
</p>

<p style="line-height: 1.7;">
We would also like to express our deep gratitude to the Head of the Department, <strong>Dr. Sonali Kothari</strong>, for granting us access to the specialized computational infrastructure, GPU clusters, and laboratory facilities necessary for fine-tuning transformer classifiers and executing high-throughput penetration tests. We are grateful to the department faculty and laboratory technical staff for their constant administrative and technical assistance.
</p>

<p style="line-height: 1.7;">
We would like to acknowledge the collaborative synergy of our project team members—Omika Shrestha, Diksha Jha, and fellow group scholars—who worked rigorously across software architecture, neural model fine-tuning, heuristic pattern engineering, reverse-proxy gateway design, and browser extension development.
</p>

<p style="line-height: 1.7;">
We extend our heartfelt gratitude to our families and friends for their enduring patience, moral support, and motivation during periods of demanding development and evaluation milestones. Finally, we thank <strong>Symbiosis Institute of Technology (SIT), Pune</strong>, for providing a stimulating academic environment that encouraged us to bridge theoretical machine learning research with practical, production-ready enterprise cybersecurity systems.
</p>

<div style="margin-top: 50pt; text-align: right;">
    <strong>Omika Shrestha (PRN: 21070122147)</strong><br>
    <strong>Diksha Jha (PRN: 21070122127)</strong><br>
    Department of Computer Science & Engineering<br>
    Symbiosis Institute of Technology, Pune
</div>

<div class="page-break"></div>

<!-- PAGE 5: ABSTRACT -->
<div class="cert-title" style="margin-top: 15pt; margin-bottom: 12pt;">ABSTRACT</div>

<p style="font-size: 11pt; line-height: 1.4; margin-bottom: 5pt;">
The rapid proliferation of Large Language Models (LLMs) across enterprise autonomous workflows, customer-facing interfaces, and analytical copilot systems has exposed a fundamental security vulnerability: prompt injection. Because transformer architectures process operational instructions and untrusted third-party data within a unified context window, adversaries can manipulate prompt semantics to hijack execution flow, evade safety guardrails, commandeer agentic tools, or exfiltrate sensitive organizational preambles and credentials.
</p>

<p style="font-size: 11pt; line-height: 1.4; margin-bottom: 5pt;">
This project report presents the design, architectural implementation, and empirical evaluation of <strong>Prompt Security Guard</strong>, a production-ready, dual-layer security middleware and reverse-proxy gateway defending enterprise generative AI applications. Our system establishes an active defensive perimeter around language models through two tightly coupled layers:
</p>

<p style="font-size: 11pt; line-height: 1.4; margin-bottom: 5pt;">
<strong>Layer 1 (Inbound Threat Perimeter):</strong> Enforces pre-execution threat screening before model invocation. To neutralize indirect injection vectors, our pipeline decouples prompt text evaluation from multi-modal attachment ingestion (supporting DOCX XML parsing, PDF stream extraction, and optical character recognition via Tesseract), maintaining granular provenance attribution. Inbound inputs undergo head-tail sequence tokenization (127 head + 127 tail tokens) and are processed through a calibrated neural-heuristic risk fusion engine combining a fine-tuned DistilBERT sequence classifier ($R_{{ML}}$) with a deterministic regex signature pattern engine ($R_{{rule}}$) at operational decision threshold $\theta = 0.3800$:
</p>

<div class="code-block" style="text-align: center; font-weight: bold; margin: 4pt 0; padding: 4pt; font-size: 8.5pt;">
    R_fused = 0.40 * R_rule + 0.60 * R_ML  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; (Decision Band: >= 38.0 -> BLOCK)
</div>

<p style="font-size: 11pt; line-height: 1.4; margin-bottom: 5pt;">
Inputs are mapped to an authoritative nine-category threat taxonomy that explicitly protects legitimate academic and defensive cybersecurity queries as safe hard negatives, eliminating catastrophic false alarms. Any input exceeding threshold $\theta$ triggers early termination, guaranteeing exactly zero downstream LLM invocations ($N = 0$).
</p>

<p style="font-size: 11pt; line-height: 1.4; margin-bottom: 5pt;">
<strong>Layer 2 (Outbound Response Guard):</strong> When an approved prompt is processed by the downstream model (Ollama <code>llama3.2:3b</code>, OpenAI <code>gpt-4o</code>, or local mock), the generated output is accumulated in an in-memory buffer under an anti-streaming security policy. Layer 2 scans for system prompt disclosure patterns, live API credentials (e.g., OpenAI <code>sk-*</code>, GitHub <code>ghp_*</code>, Google <code>AIza*</code>, private keys, database URIs), personally identifiable information (PII), and degenerative infinite token loops, enforcing automatic redaction (<code>[REDACTED_PII]</code>) or total response withholding.
</p>

<p style="font-size: 11pt; line-height: 1.4; margin-bottom: 5pt;">
<strong>Empirical Validation:</strong> On an independent 3,000-sample balanced generalization benchmark, our hybrid detector achieves an accuracy of <strong>98.73%</strong>, precision of <strong>99.26%</strong>, recall of <strong>98.20%</strong>, and F1-score of <strong>0.9873</strong>, vastly outperforming rule-only baselines (which achieve only 8.73% recall). On a 600-sample adversarial challenge holdout, the system achieves <strong>100% precision</strong> and <strong>0.00% false-positive rate</strong>. The entire framework exposes an OpenAI-compatible gateway (<code>/v1/chat/completions</code>) for seamless integration with platforms like Open WebUI, a Chromium browser extension for client-side pre-submission interception, and is certified by a <strong>288-test automated regression suite with a 100% pass rate</strong> operating at sub-30ms hardware-accelerated inference latency.
</p>

<p style="font-size: 11pt; line-height: 1.4; margin-top: 6pt; margin-bottom: 0; text-indent: 0;">
<strong>Keywords:</strong> Prompt Injection, Indirect Prompt Injection, Large Language Models, Multi-Modal Ingestion, DistilBERT, Defense-in-Depth, Threat Taxonomy, Data Leakage Prevention, OpenAI Gateway, Chromium Browser Extension.
</p>

<div class="page-break"></div>

<!-- PAGE 6 & 7: TABLE OF CONTENTS (NORMAL TEXT ENTRIES WITH DOT LEADERS, NOT A TABLE) -->
<h1 class="chapter-title">TABLE OF CONTENTS</h1>

<div class="toc-container">
    <div class="toc-line prelim"><span class="toc-title">Certificate</span><span class="toc-dots"></span><span class="toc-page">i</span></div>
    <div class="toc-line prelim"><span class="toc-title">Declaration</span><span class="toc-dots"></span><span class="toc-page">ii</span></div>
    <div class="toc-line prelim"><span class="toc-title">Acknowledgement</span><span class="toc-dots"></span><span class="toc-page">iii</span></div>
    <div class="toc-line prelim"><span class="toc-title">Abstract &amp; Keywords</span><span class="toc-dots"></span><span class="toc-page">iv</span></div>
    <div class="toc-line prelim"><span class="toc-title">Table of Contents</span><span class="toc-dots"></span><span class="toc-page">v</span></div>
    <div class="toc-line prelim"><span class="toc-title">List of Tables</span><span class="toc-dots"></span><span class="toc-page">vii</span></div>
    <div class="toc-line prelim"><span class="toc-title">List of Figures</span><span class="toc-dots"></span><span class="toc-page">viii</span></div>
    <div class="toc-line prelim"><span class="toc-title">List of Abbreviations</span><span class="toc-dots"></span><span class="toc-page">ix</span></div>

    <div class="toc-line chapter"><span class="toc-title">CHAPTER 1: INTRODUCTION</span><span class="toc-dots"></span><span class="toc-page">1</span></div>
    <div class="toc-line sec"><span class="toc-title">1.1 Introduction to Large Language Models and Enterprise Integration</span><span class="toc-dots"></span><span class="toc-page">1</span></div>
    <div class="toc-line sec"><span class="toc-title">1.2 The Prompt Injection Vulnerability: Direct vs. Indirect Attack Vectors</span><span class="toc-dots"></span><span class="toc-page">1</span></div>
    <div class="toc-line sec"><span class="toc-title">1.3 Problem Statement</span><span class="toc-dots"></span><span class="toc-page">2</span></div>
    <div class="toc-line sec"><span class="toc-title">1.4 Scope of Research and Operational Boundaries</span><span class="toc-dots"></span><span class="toc-page">2</span></div>
    <div class="toc-line sec"><span class="toc-title">1.5 Research Hypotheses</span><span class="toc-dots"></span><span class="toc-page">3</span></div>
    <div class="toc-line sec"><span class="toc-title">1.6 Project Objectives</span><span class="toc-dots"></span><span class="toc-page">3</span></div>
    <div class="toc-line sec"><span class="toc-title">1.7 Sustainable Development Goals (SDG) Alignment and Justification</span><span class="toc-dots"></span><span class="toc-page">4</span></div>
    <div class="toc-line sec"><span class="toc-title">1.8 Work Breakdown Structure and Team Contributions</span><span class="toc-dots"></span><span class="toc-page">4</span></div>
    <div class="toc-line sec"><span class="toc-title">1.9 Organization of the Report</span><span class="toc-dots"></span><span class="toc-page">5</span></div>

    <div class="toc-line chapter"><span class="toc-title">CHAPTER 2: LITERATURE REVIEW</span><span class="toc-dots"></span><span class="toc-page">6</span></div>
    <div class="toc-line sec"><span class="toc-title">2.1 Theoretical Background and Evolution of Prompt Injection Attacks</span><span class="toc-dots"></span><span class="toc-page">6</span></div>
    <div class="toc-line sec"><span class="toc-title">2.2 In-Depth Survey of Existing Literature (20 Academic Sources)</span><span class="toc-dots"></span><span class="toc-page">6</span></div>
    <div class="toc-line sec"><span class="toc-title">2.3 Detailed Attack Taxonomy Survey: Direct, Carrier, and Jailbreak Patterns</span><span class="toc-dots"></span><span class="toc-page">9</span></div>
    <div class="toc-line sec"><span class="toc-title">2.4 Mathematical Analysis of Attention Hijacking vs. Defense-in-Depth</span><span class="toc-dots"></span><span class="toc-page">10</span></div>
    <div class="toc-line sec"><span class="toc-title">2.5 Summary of Literature Review and Identified Research Gaps</span><span class="toc-dots"></span><span class="toc-page">10</span></div>
    <div class="toc-line sec"><span class="toc-title">2.6 Comparative Analysis: Proposed Architecture vs. Existing Defenses</span><span class="toc-dots"></span><span class="toc-page">11</span></div>

    <div class="toc-line chapter"><span class="toc-title">CHAPTER 3: SOFTWARE REQUIREMENTS SPECIFICATION</span><span class="toc-dots"></span><span class="toc-page">12</span></div>
    <div class="toc-line sec"><span class="toc-title">3.1 Software Platform, Frameworks, and Dependent Tooling</span><span class="toc-dots"></span><span class="toc-page">12</span></div>
    <div class="toc-line sec"><span class="toc-title">3.2 Hardware Tools, Compute Infrastructure, and Multi-Runtime Support</span><span class="toc-dots"></span><span class="toc-page">12</span></div>
    <div class="toc-line sec"><span class="toc-title">3.3 Work Breakdown Structure (WBS) and Project Timeline</span><span class="toc-dots"></span><span class="toc-page">13</span></div>
    <div class="toc-line sec"><span class="toc-title">3.4 Detailed Functional Requirements Specification (FR-1 to FR-12)</span><span class="toc-dots"></span><span class="toc-page">13</span></div>
    <div class="toc-line sec"><span class="toc-title">3.5 Non-Functional Requirements Specification (NFR-1 to NFR-8)</span><span class="toc-dots"></span><span class="toc-page">16</span></div>
    <div class="toc-line sec"><span class="toc-title">3.6 Use Case Formal Specifications</span><span class="toc-dots"></span><span class="toc-page">16</span></div>
    <div class="toc-line sec"><span class="toc-title">3.7 Requirements Traceability Matrix</span><span class="toc-dots"></span><span class="toc-page">17</span></div>
    <div class="toc-line sec"><span class="toc-title">3.8 Security Architecture Risk Analysis &amp; STRIDE Threat Modeling Matrix</span><span class="toc-dots"></span><span class="toc-page">18</span></div>
    <div class="toc-line sec"><span class="toc-title">3.9 Comprehensive Project Cost and Resource Estimation</span><span class="toc-dots"></span><span class="toc-page">19</span></div>

    <div class="toc-line chapter"><span class="toc-title">CHAPTER 4: SYSTEM DESIGN AND METHODOLOGY</span><span class="toc-dots"></span><span class="toc-page">20</span></div>
    <div class="toc-line sec"><span class="toc-title">4.1 Threat Modeling and Adversarial Assumptions</span><span class="toc-dots"></span><span class="toc-page">20</span></div>
    <div class="toc-line sec"><span class="toc-title">4.2 High-Level System Architecture and Design Principles</span><span class="toc-dots"></span><span class="toc-page">20</span></div>
    <div class="toc-line sec"><span class="toc-title">4.3 Formal Architectural Diagrams and Walkthroughs</span><span class="toc-dots"></span><span class="toc-page">21</span></div>
    <div class="toc-line sec"><span class="toc-title">4.4 Dataset Lineage, Multi-Domain Sourcing, and Human Annotation Protocol</span><span class="toc-dots"></span><span class="toc-page">24</span></div>
    <div class="toc-line sec"><span class="toc-title">4.5 Mathematical Foundations of Transformer Attention &amp; DistilBERT Classification</span><span class="toc-dots"></span><span class="toc-page">24</span></div>
    <div class="toc-line sec"><span class="toc-title">4.6 Input Normalization and Head-Tail Sequence Tokenization Algorithm</span><span class="toc-dots"></span><span class="toc-page">25</span></div>
    <div class="toc-line sec"><span class="toc-title">4.7 Layer 1 Heuristic Signature Engine &amp; Regex Catalog</span><span class="toc-dots"></span><span class="toc-page">26</span></div>
    <div class="toc-line sec"><span class="toc-title">4.8 Neural-Heuristic Fusion Engine &amp; Calibrated Decision Gating</span><span class="toc-dots"></span><span class="toc-page">27</span></div>
    <div class="toc-line sec"><span class="toc-title">4.9 Authoritative Nine-Category Threat Taxonomy with Concrete Exemplars</span><span class="toc-dots"></span><span class="toc-page">27</span></div>
    <div class="toc-line sec"><span class="toc-title">4.10 Decoupled Multi-Modal Attachment Parsing and OCR Ingestion Pipeline</span><span class="toc-dots"></span><span class="toc-page">28</span></div>
    <div class="toc-line sec"><span class="toc-title">4.11 Layer 2 Outbound Response Guard: Secret Scanning &amp; PII Redaction</span><span class="toc-dots"></span><span class="toc-page">29</span></div>
    <div class="toc-line sec"><span class="toc-title">4.12 Ecosystem Gateways and User Interfaces</span><span class="toc-dots"></span><span class="toc-page">29</span></div>

    <div class="toc-line chapter"><span class="toc-title">CHAPTER 5: RESULTS AND DISCUSSION</span><span class="toc-dots"></span><span class="toc-page">32</span></div>
    <div class="toc-line sec"><span class="toc-title">5.1 Experimental Setup and Evaluation Protocol</span><span class="toc-dots"></span><span class="toc-page">32</span></div>
    <div class="toc-line sec"><span class="toc-title">5.2 Comparative Empirical Detection Performance Across Regimes</span><span class="toc-dots"></span><span class="toc-page">32</span></div>
    <div class="toc-line sec"><span class="toc-title">5.3 Per-Category Attack Resilience and Hard-Negative Specificity</span><span class="toc-dots"></span><span class="toc-page">33</span></div>
    <div class="toc-line sec"><span class="toc-title">5.4 Multi-Modal Attachment Parsing and Indirect Injection Defense Results</span><span class="toc-dots"></span><span class="toc-page">33</span></div>
    <div class="toc-line sec"><span class="toc-title">5.5 Layer 2 Outbound Response Sanitization Evaluation</span><span class="toc-dots"></span><span class="toc-page">33</span></div>
    <div class="toc-line sec"><span class="toc-title">5.6 Comprehensive Automated Regression Suite Verification (288 Tests)</span><span class="toc-dots"></span><span class="toc-page">34</span></div>
    <div class="toc-line sec"><span class="toc-title">5.7 Execution Latency and Hardware Compute Overhead Profiling</span><span class="toc-dots"></span><span class="toc-page">35</span></div>
    <div class="toc-line sec"><span class="toc-title">5.8 Comparative Ablation Analysis</span><span class="toc-dots"></span><span class="toc-page">36</span></div>
    <div class="toc-line sec"><span class="toc-title">5.9 In-Depth Error Analysis and Boundary Case Investigation</span><span class="toc-dots"></span><span class="toc-page">36</span></div>
    <div class="toc-line sec"><span class="toc-title">5.10 Statistical Significance Testing</span><span class="toc-dots"></span><span class="toc-page">37</span></div>
    <div class="toc-line sec"><span class="toc-title">5.11 Robustness to Adversarial Evasion and Perturbations</span><span class="toc-dots"></span><span class="toc-page">37</span></div>
    <div class="toc-line sec"><span class="toc-title">5.12 Summary of Results and Empirical Findings</span><span class="toc-dots"></span><span class="toc-page">37</span></div>

    <div class="toc-line chapter"><span class="toc-title">CHAPTER 6: CONCLUSION AND FUTURE SCOPE</span><span class="toc-dots"></span><span class="toc-page">39</span></div>
    <div class="toc-line sec"><span class="toc-title">6.1 Conclusion and Realized Systems Contributions</span><span class="toc-dots"></span><span class="toc-page">39</span></div>
    <div class="toc-line sec"><span class="toc-title">6.2 Research Hypotheses Validation Synthesis</span><span class="toc-dots"></span><span class="toc-page">40</span></div>
    <div class="toc-line sec"><span class="toc-title">6.3 Limitations of Current Framework</span><span class="toc-dots"></span><span class="toc-page">40</span></div>
    <div class="toc-line sec"><span class="toc-title">6.4 Future Scope and Research Roadmap</span><span class="toc-dots"></span><span class="toc-page">40</span></div>

    <div class="toc-line chapter"><span class="toc-title">REFERENCES (APA FORMAT - 30 CITATIONS)</span><span class="toc-dots"></span><span class="toc-page">42</span></div>
    <div class="toc-line chapter"><span class="toc-title">APPENDICES</span><span class="toc-dots"></span><span class="toc-page">45</span></div>
    <div class="toc-line sec"><span class="toc-title">Appendix A: Academic Integrity Committee (AIC) Compliance Form</span><span class="toc-dots"></span><span class="toc-page">45</span></div>
    <div class="toc-line sec"><span class="toc-title">Appendix B: Plagiarism Detection Report Summary &amp; Compliance</span><span class="toc-dots"></span><span class="toc-page">46</span></div>
    <div class="toc-line sec"><span class="toc-title">Appendix C: AI Writing Detection Report Summary &amp; Compliance</span><span class="toc-dots"></span><span class="toc-page">47</span></div>
    <div class="toc-line sec"><span class="toc-title">Appendix D: Peer-Reviewed Conference Paper Metadata &amp; Acceptance</span><span class="toc-dots"></span><span class="toc-page">48</span></div>
    <div class="toc-line sec"><span class="toc-title">Appendix E: Comprehensive Repository Code Manifest &amp; Verification Hashes</span><span class="toc-dots"></span><span class="toc-page">49</span></div>
    <div class="toc-line sec"><span class="toc-title">Appendix F: System Deployment, Configuration, and Quick-Start Operations Manual</span><span class="toc-dots"></span><span class="toc-page">50</span></div>
</div>

<div class="page-break"></div>

<!-- PAGE 8: LIST OF TABLES (NORMAL TEXT ENTRIES WITH DOT LEADERS) -->
<h1 class="chapter-title">LIST OF TABLES</h1>

<div class="lot-container">
    <div class="toc-line"><span class="toc-title">Table 1.1: Sustainable Development Goals (SDG) Alignment and Impact Matrix</span><span class="toc-dots"></span><span class="toc-page">4</span></div>
    <div class="toc-line"><span class="toc-title">Table 1.2: Capstone Project Work Distribution and Team Member Roles</span><span class="toc-dots"></span><span class="toc-page">4</span></div>
    <div class="toc-line"><span class="toc-title">Table 2.1: Comprehensive Comparative Survey of 20 Key Academic Research Studies</span><span class="toc-dots"></span><span class="toc-page">8</span></div>
    <div class="toc-line"><span class="toc-title">Table 2.2: Comparative Architectural Feature Matrix of Prompt Defense Paradigms</span><span class="toc-dots"></span><span class="toc-page">11</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.1: Software Platform, Language Runtime, and Dependent Libraries</span><span class="toc-dots"></span><span class="toc-page">12</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.2: Hardware Development, Acceleration Runtimes, and Hardware Profiles</span><span class="toc-dots"></span><span class="toc-page">12</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.3: Comprehensive Functional Requirements Specification (FR-1 to FR-12)</span><span class="toc-dots"></span><span class="toc-page">15</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.4: Non-Functional Requirements Specification and Operational Thresholds</span><span class="toc-dots"></span><span class="toc-page">16</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.5: Use Case UC-1: Inbound Prompt Submission and Real-Time Risk Gating</span><span class="toc-dots"></span><span class="toc-page">16</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.6: Use Case UC-2: Multi-Modal Attachment Ingestion and Carrier Injection Defense</span><span class="toc-dots"></span><span class="toc-page">17</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.7: Use Case UC-3: Outbound Response Sanitization and Credential Leak Interception</span><span class="toc-dots"></span><span class="toc-page">17</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.8: Requirements Traceability Matrix Linking Requirements to Test Modules</span><span class="toc-dots"></span><span class="toc-page">17</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.9: STRIDE Threat Modeling and Architectural Risk Mitigation Matrix</span><span class="toc-dots"></span><span class="toc-page">18</span></div>
    <div class="toc-line"><span class="toc-title">Table 3.10: Itemized Project Cost Estimation and Amortized Resource Budget</span><span class="toc-dots"></span><span class="toc-page">19</span></div>
    <div class="toc-line"><span class="toc-title">Table 4.1: Three-Phase Dataset Evolution, Splitting Ratios, and File Provenance</span><span class="toc-dots"></span><span class="toc-page">24</span></div>
    <div class="toc-line"><span class="toc-title">Table 4.2: Layer 1 Compiled Regular Expression Signatures and Severity Weights</span><span class="toc-dots"></span><span class="toc-page">26</span></div>
    <div class="toc-line"><span class="toc-title">Table 4.3: Inbound Security Risk Decision Bands and Policy Enforcement</span><span class="toc-dots"></span><span class="toc-page">27</span></div>
    <div class="toc-line"><span class="toc-title">Table 4.4: Exemplar Adversarial Payloads across the Nine-Category Threat Taxonomy</span><span class="toc-dots"></span><span class="toc-page">27</span></div>
    <div class="toc-line"><span class="toc-title">Table 4.5: Layer 2 Response Security Inspection Rules and Sanitization Directives</span><span class="toc-dots"></span><span class="toc-page">29</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.1: Comparative Detection Performance Across Regimes on Independent Holdouts</span><span class="toc-dots"></span><span class="toc-page">32</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.2: Per-Category Attack Resilience and Specificity on 3,000 Generalization Samples</span><span class="toc-dots"></span><span class="toc-page">33</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.3: Multi-Modal Attachment Carrier Extraction and OCR Detection Results</span><span class="toc-dots"></span><span class="toc-page">33</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.4: Comprehensive Automated Regression Suite Matrix (288 Passing Tests)</span><span class="toc-dots"></span><span class="toc-page">34</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.5: End-to-End Operational Verification Across Test Scenarios A through H</span><span class="toc-dots"></span><span class="toc-page">35</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.6: End-to-End Latency Profile Across Hardware Execution Runtimes</span><span class="toc-dots"></span><span class="toc-page">35</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.7: Component Ablation Impact on 3,000 Generalization Samples</span><span class="toc-dots"></span><span class="toc-page">36</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.8: Root Cause Decomposition of Classification Errors on 3,000 Generalization Samples</span><span class="toc-dots"></span><span class="toc-page">36</span></div>
    <div class="toc-line"><span class="toc-title">Table 5.9: Adversarial Robustness to Perturbation Attacks on 500 Adversarial Samples</span><span class="toc-dots"></span><span class="toc-page">37</span></div>
</div>

<div class="page-break"></div>

<!-- PAGE 9: LIST OF FIGURES (NORMAL TEXT ENTRIES WITH DOT LEADERS) -->
<h1 class="chapter-title">LIST OF FIGURES</h1>

<div class="lof-container">
    <div class="toc-line"><span class="toc-title">Figure 3.1: Project Work Breakdown Structure (WBS) and Milestone Gantt Chart</span><span class="toc-dots"></span><span class="toc-page">13</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.1: End-to-End Dual-Layer Prompt Security Gateway Architecture</span><span class="toc-dots"></span><span class="toc-page">21</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.2 &amp; 4.3: Data Flow Diagrams (DFD Level 0 Context and DFD Level 1 Decomposition)</span><span class="toc-dots"></span><span class="toc-page">22</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.4: UML Sequence Diagram of End-to-End Inbound and Outbound Request Lifecycle</span><span class="toc-dots"></span><span class="toc-page">23</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.5: Entity-Relationship (ER) Diagram of SQLite Security Forensics Database</span><span class="toc-dots"></span><span class="toc-page">23</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.6: Production Web Security Analyzer User Interface</span><span class="toc-dots"></span><span class="toc-page">30</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.7: Gateway Deployment and Open WebUI Integration Center</span><span class="toc-dots"></span><span class="toc-page">30</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.8: External LLM Integration Portal (Ollama, OpenAI, Local Mock)</span><span class="toc-dots"></span><span class="toc-page">31</span></div>
    <div class="toc-line"><span class="toc-title">Figure 4.9: Centralized Security Operations Dashboard and Forensics Audit Logger</span><span class="toc-dots"></span><span class="toc-page">31</span></div>
    <div class="toc-line"><span class="toc-title">Figure 5.1: Empirical Confusion Matrices Across Detection Regimes on Generalization Test</span><span class="toc-dots"></span><span class="toc-page">32</span></div>
</div>

<div class="page-break"></div>

<!-- PAGE 10: LIST OF ABBREVIATIONS -->
<h1 class="chapter-title">LIST OF ABBREVIATIONS</h1>

<table>
    <tr>
        <th style="width: 25%; text-align: left;">Abbreviation</th>
        <th style="width: 75%; text-align: left;">Full Expansion / Technical Definition</th>
    </tr>
    <tr>
        <td><strong>AI</strong></td>
        <td>Artificial Intelligence</td>
    </tr>
    <tr>
        <td><strong>AIC</strong></td>
        <td>Academic Integrity Committee</td>
    </tr>
    <tr>
        <td><strong>API</strong></td>
        <td>Application Programming Interface</td>
    </tr>
    <tr>
        <td><strong>AUC</strong></td>
        <td>Area Under the Curve (Receiver Operating Characteristic)</td>
    </tr>
    <tr>
        <td><strong>BERT</strong></td>
        <td>Bidirectional Encoder Representations from Transformers</td>
    </tr>
    <tr>
        <td><strong>CLS</strong></td>
        <td>Classification Token (Transformer special beginning token)</td>
    </tr>
    <tr>
        <td><strong>CPU</strong></td>
        <td>Central Processing Unit</td>
    </tr>
    <tr>
        <td><strong>CRUD</strong></td>
        <td>Create, Read, Update, Delete</td>
    </tr>
    <tr>
        <td><strong>CUDA</strong></td>
        <td>Compute Unified Device Architecture (NVIDIA GPU Computing)</td>
    </tr>
    <tr>
        <td><strong>CVE</strong></td>
        <td>Common Vulnerabilities and Exposures</td>
    </tr>
    <tr>
        <td><strong>DFD</strong></td>
        <td>Data Flow Diagram</td>
    </tr>
    <tr>
        <td><strong>DOCX</strong></td>
        <td>Office Open XML Document Format</td>
    </tr>
    <tr>
        <td><strong>ER</strong></td>
        <td>Entity-Relationship</td>
    </tr>
    <tr>
        <td><strong>F1</strong></td>
        <td>Harmonic Mean of Precision and Recall</td>
    </tr>
    <tr>
        <td><strong>FN</strong></td>
        <td>False Negative</td>
    </tr>
    <tr>
        <td><strong>FP</strong></td>
        <td>False Positive</td>
    </tr>
    <tr>
        <td><strong>FPR</strong></td>
        <td>False Positive Rate</td>
    </tr>
    <tr>
        <td><strong>GPU</strong></td>
        <td>Graphics Processing Unit</td>
    </tr>
    <tr>
        <td><strong>HOD</strong></td>
        <td>Head of Department</td>
    </tr>
    <tr>
        <td><strong>HTTP</strong></td>
        <td>Hypertext Transfer Protocol</td>
    </tr>
    <tr>
        <td><strong>IDE</strong></td>
        <td>Integrated Development Environment</td>
    </tr>
    <tr>
        <td><strong>IEEE</strong></td>
        <td>Institute of Electrical and Electronics Engineers</td>
    </tr>
    <tr>
        <td><strong>JSON</strong></td>
        <td>JavaScript Object Notation</td>
    </tr>
    <tr>
        <td><strong>LLM</strong></td>
        <td>Large Language Model</td>
    </tr>
    <tr>
        <td><strong>ML</strong></td>
        <td>Machine Learning</td>
    </tr>
    <tr>
        <td><strong>MPS</strong></td>
        <td>Metal Performance Shaders (Apple Silicon GPU Acceleration)</td>
    </tr>
    <tr>
        <td><strong>NIST</strong></td>
        <td>National Institute of Standards and Technology</td>
    </tr>
    <tr>
        <td><strong>NLP</strong></td>
        <td>Natural Language Processing</td>
    </tr>
    <tr>
        <td><strong>OCR</strong></td>
        <td>Optical Character Recognition</td>
    </tr>
    <tr>
        <td><strong>OWASP</strong></td>
        <td>Open Worldwide Application Security Project</td>
    </tr>
    <tr>
        <td><strong>PDF</strong></td>
        <td>Portable Document Format</td>
    </tr>
    <tr>
        <td><strong>PII</strong></td>
        <td>Personally Identifiable Information</td>
    </tr>
</table>

<div class="page-break"></div>

<h1 class="chapter-title">LIST OF ABBREVIATIONS (CONTINUED)</h1>

<table>
    <tr>
        <th style="width: 25%; text-align: left;">Abbreviation</th>
        <th style="width: 75%; text-align: left;">Full Expansion / Technical Definition</th>
    </tr>
    <tr>
        <td><strong>PRN</strong></td>
        <td>Permanent Registration Number</td>
    </tr>
    <tr>
        <td><strong>REST</strong></td>
        <td>Representational State Transfer</td>
    </tr>
    <tr>
        <td><strong>ROC</strong></td>
        <td>Receiver Operating Characteristic</td>
    </tr>
    <tr>
        <td><strong>ROT13</strong></td>
        <td>Rotate by 13 Places (Substitution Cipher)</td>
    </tr>
    <tr>
        <td><strong>SDG</strong></td>
        <td>Sustainable Development Goals (United Nations)</td>
    </tr>
    <tr>
        <td><strong>SEP</strong></td>
        <td>Separator Token (Transformer special delimiter token)</td>
    </tr>
    <tr>
        <td><strong>SHA</strong></td>
        <td>Secure Hash Algorithm</td>
    </tr>
    <tr>
        <td><strong>SIT</strong></td>
        <td>Symbiosis Institute of Technology</td>
    </tr>
    <tr>
        <td><strong>SRS</strong></td>
        <td>Software Requirements Specification</td>
    </tr>
    <tr>
        <td><strong>SSN</strong></td>
        <td>Social Security Number</td>
    </tr>
    <tr>
        <td><strong>STEM</strong></td>
        <td>Science, Technology, Engineering, and Mathematics</td>
    </tr>
    <tr>
        <td><strong>STRIDE</strong></td>
        <td>Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege</td>
    </tr>
    <tr>
        <td><strong>TN</strong></td>
        <td>True Negative</td>
    </tr>
    <tr>
        <td><strong>TOC</strong></td>
        <td>Table of Contents</td>
    </tr>
    <tr>
        <td><strong>TP</strong></td>
        <td>True Positive</td>
    </tr>
    <tr>
        <td><strong>UI</strong></td>
        <td>User Interface</td>
    </tr>
    <tr>
        <td><strong>UML</strong></td>
        <td>Unified Modeling Language</td>
    </tr>
    <tr>
        <td><strong>URI</strong></td>
        <td>Uniform Resource Identifier</td>
    </tr>
    <tr>
        <td><strong>WBS</strong></td>
        <td>Work Breakdown Structure</td>
    </tr>
    <tr>
        <td><strong>XML</strong></td>
        <td>Extensible Markup Language</td>
    </tr>
</table>

<div class="page-break"></div>
"""
