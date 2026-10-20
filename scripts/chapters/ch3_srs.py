"""
scripts/chapters/ch3_srs.py
Generates Chapter 3: Software Requirements Specification (SRS) for the B.Tech Blackbook.
"""

def get_ch3_html(fig_gantt_path):
    return f"""
<!-- CHAPTER 3: SOFTWARE REQUIREMENTS SPECIFICATION -->
<h1 class="chapter-title">CHAPTER 3<br>SOFTWARE REQUIREMENTS SPECIFICATION</h1>

<h2 class="section-title">3.1 Software Platform, Frameworks, and Dependent Tooling</h2>
<p>
The Prompt Security Guard framework is implemented in Python 3.12, selected for its mature ecosystem in transformer machine learning, high-performance web frameworks, and robust parsing libraries. The system is architected as an asynchronous modular middleware that interfaces seamlessly between external clients and target generative language models. Table 3.1 summarizes the complete software platform and third-party dependencies.
</p>

<div class="table-caption">Table 3.1: Software Platform, Language Runtime, and Dependent Libraries</div>
<table>
    <tr>
        <th style="width: 22%;">Software Component</th>
        <th style="width: 18%;">Version / Release</th>
        <th style="width: 25%;">Primary Operational Role</th>
        <th style="width: 35%;">Engineering Utilization in System</th>
    </tr>
    <tr>
        <td><strong>Python Core</strong></td>
        <td>3.12.9</td>
        <td>Execution Runtime</td>
        <td>Core asynchronous execution, type-hinted backend architecture, process management.</td>
    </tr>
    <tr>
        <td><strong>Flask</strong></td>
        <td>3.0.3</td>
        <td>Web Server & Gateway</td>
        <td>Routing for web analyzer, administrative dashboard, and <code>/v1/chat/completions</code> reverse proxy.</td>
    </tr>
    <tr>
        <td><strong>PyTorch</strong></td>
        <td>2.5.1</td>
        <td>Deep Learning Engine</td>
        <td>Tensor evaluation, DistilBERT forward inference, GPU/MPS device tensor offloading.</td>
    </tr>
    <tr>
        <td><strong>Transformers (HuggingFace)</strong></td>
        <td>4.46.2</td>
        <td>Transformer Pipeline</td>
        <td>DistilBERT sequence classification head, tokenizer management, token pooling.</td>
    </tr>
    <tr>
        <td><strong>python-docx</strong></td>
        <td>1.1.2</td>
        <td>Document Parsing</td>
        <td>XML paragraph and table text extraction from Microsoft Word (.docx) files.</td>
    </tr>
    <tr>
        <td><strong>pypdf</strong></td>
        <td>5.1.0</td>
        <td>PDF Stream Parsing</td>
        <td>Stream extraction, page decoding, and metadata harvesting from PDF attachments.</td>
    </tr>
    <tr>
        <td><strong>pytesseract & Pillow</strong></td>
        <td>0.3.13 / 12.3.0</td>
        <td>Image OCR Engine</td>
        <td>Raster graphics processing, contrast adjustment, and Tesseract OCR character recognition.</td>
    </tr>
    <tr>
        <td><strong>SQLite3</strong></td>
        <td>3.45.1</td>
        <td>Forensic Audit Database</td>
        <td>ACID-compliant storage of incident logs, risk scores, IP provenance, and latency metrics.</td>
    </tr>
    <tr>
        <td><strong>pytest</strong></td>
        <td>8.3.3</td>
        <td>Automated Testing</td>
        <td>Execution of 288-test regression matrix, mock downstream assertions, and UI verification.</td>
    </tr>
</table>

<h2 class="section-title">3.2 Hardware Tools, Compute Infrastructure, and Multi-Runtime Support</h2>
<p>
To ensure enterprise flexibility across heterogeneous deployment environments, the security middleware is engineered to auto-detect and utilize available hardware acceleration primitives without configuration changes. Table 3.2 outlines the verified compute profiles.
</p>

<div class="table-caption">Table 3.2: Hardware Development, Acceleration Runtimes, and Hardware Profiles</div>
<table>
    <tr>
        <th style="width: 22%;">Hardware Platform</th>
        <th style="width: 25%;">Acceleration Runtime</th>
        <th style="width: 28%;">Hardware Specifications</th>
        <th style="width: 25%;">Layer 1 Mean Latency</th>
    </tr>
    <tr>
        <td><strong>Apple Silicon (ARM64)</strong></td>
        <td>PyTorch Metal (MPS)</td>
        <td>Apple M-Series Unified Memory Architecture (16-core Neural Engine)</td>
        <td><strong>29.3 ms</strong> (Production Active)</td>
    </tr>
    <tr>
        <td><strong>NVIDIA Enterprise GPU</strong></td>
        <td>CUDA 12.4 / cuDNN</td>
        <td>NVIDIA RTX 4090 / A100 Tensor Core Architecture</td>
        <td><strong>22.7 ms</strong> (Peak Datacenter)</td>
    </tr>
    <tr>
        <td><strong>Standard x86 Server</strong></td>
        <td>Intel MKL / OpenMP CPU</td>
        <td>Intel Xeon / Core i7 x86_64 Multi-threaded Vector Execution</td>
        <td><strong>84.7 ms</strong> (Fallback Safe)</td>
    </tr>
</table>

<h2 class="section-title">3.3 Work Breakdown Structure (WBS) and Project Timeline</h2>
<p>
The project was executed across five primary work packages over 24 weeks: (WP1) Requirements & Threat Modeling, (WP2) Dataset Sourcing & Annotation, (WP3) Model Fine-Tuning & Inbound Perimeter, (WP4) Outbound Perimeter & Multi-Modal Extraction, and (WP5) Gateway Integration & Automated Regression Testing. Figure 3.1 illustrates the milestone Gantt chart.
</p>

<div class="figure-box">
    <img src="{fig_gantt_path}" alt="Figure 3.1: Project WBS and Milestone Gantt Chart">
    <div class="figure-caption">Figure 3.1: Project Work Breakdown Structure (WBS) and Milestone Gantt Chart</div>
</div>

<h2 class="section-title">3.4 Detailed Functional Requirements Specification</h2>
<p>
The functional requirements formalize the concrete behavioral contracts implemented by the Prompt Security Guard system:
</p>

<p>
<strong>FR-1: Inbound Prompt Risk Scoring</strong><br>
<em>Description:</em> The gateway shall intercept every inbound text submission and evaluate it against the neural-heuristic risk engine.<br>
<em>Input:</em> JSON payload containing user prompt string <code>prompt</code> (UTF-8 encoded).<br>
<em>Processing:</em> Compute $R_{{rule}}$ via regex pattern bank; compute $R_{{ML}}$ via DistilBERT; fuse via $R_{{fused}} = 0.40 R_{{rule}} + 0.60 R_{{ML}}$.<br>
<em>Output:</em> Continuous risk score $[0, 100]$, risk level (LOW, MEDIUM, HIGH, CRITICAL), and decision (ALLOW, BLOCK).<br>
<em>Exceptions:</em> If input is empty, return HTTP 400 Bad Request with informative error JSON.
</p>

<p>
<strong>FR-2: Decoupled Multi-Modal Attachment Parsing</strong><br>
<em>Description:</em> The system shall extract text content from uploaded files (DOCX, PDF, TXT) independently of the user prompt string.<br>
<em>Input:</em> Multipart form-data containing binary file upload.<br>
<em>Processing:</em> For DOCX, traverse document XML elements; for PDF, extract page text streams; for TXT, decode UTF-8.<br>
<em>Output:</em> Extracted attachment text string; separate risk evaluation $R_{{attachment}}$.<br>
<em>Exceptions:</em> If file size exceeds 20MB or format is unsupported, reject upload with secure error code.
</p>

<p>
<strong>FR-3: Image Optical Character Recognition (OCR) Scanning</strong><br>
<em>Description:</em> The system shall detect text embedded inside image attachments (PNG, JPG) using Tesseract OCR.<br>
<em>Input:</em> Image file upload (PNG or JPEG).<br>
<em>Processing:</em> Preprocess image via Pillow (grayscale, contrast normalization); extract text using <code>pytesseract.image_to_string()</code>.<br>
<em>Output:</em> Extracted optical text string passed to Layer 1 scanner.<br>
<em>Exceptions:</em> Corrupted image headers return HTTP 422 Unprocessable Entity.
</p>

<p>
<strong>FR-4: Fine-Grained Threat Provenance Attribution</strong><br>
<em>Description:</em> The system shall explicitly record and output the source of any detected security risk.<br>
<em>Processing:</em> If only prompt risk exceeds threshold, set <code>threat_source = "User Prompt"</code>; if only attachment risk exceeds threshold, set <code>threat_source = "Attachment"</code>; if both exceed, set <code>threat_source = "Both"</code>; otherwise set <code>threat_source = "None"</code>.<br>
<em>Output:</em> Provenance label included in API responses and audit logs.
</p>

<p>
<strong>FR-5: Head-Tail Sequence Tokenization</strong><br>
<em>Description:</em> To neutralize attacks placed at sequence boundaries, inputs longer than 254 tokens shall be truncated symmetrically.<br>
<em>Processing:</em> Extract 127 tokens from the start and 127 tokens from the end; assemble <code>[[CLS], t_1..t_127, [SEP], t_N-126..t_N, [SEP]]</code>.<br>
<em>Output:</em> 256-token tensor passed to DistilBERT classifier.
</p>

<p>
<strong>FR-6: Authoritative Nine-Category Threat Classification</strong><br>
<em>Description:</em> Inbound threats shall be categorized into nine explicit taxonomy buckets.<br>
<em>Processing:</em> Map detected pattern evidence into: (1) Benign, (2) Direct Injection, (3) Indirect Injection, (4) Instruction Override, (5) Jailbreak, (6) Obfuscation, (7) Carrier Injection, (8) Sensitive Exfiltration, or (9) Safe Hard Negatives.<br>
<em>Output:</em> Authoritative category name and explanation string.
</p>

<p>
<strong>FR-7: Hard-Negative Exemption for Security Inquiries</strong><br>
<em>Description:</em> Legitimate academic and professional cybersecurity queries shall not be blocked.<br>
<em>Processing:</em> Inputs categorized under Category 9 shall be assigned an <code>ALLOW</code> verdict regardless of heuristic matches.<br>
<em>Output:</em> Threat score capped at LOW/MEDIUM; prompt forwarded to model.
</p>

<p>
<strong>FR-8: Strict Pre-Execution Decision Gating</strong><br>
<em>Description:</em> When an input is classified as BLOCK, downstream language models shall never be called.<br>
<em>Processing:</em> Gating check verifies $R_{{fused}} < 38.0$; if blocked, abort pipeline and return security alert.<br>
<em>Output:</em> HTTP 200/403 with block alert; zero downstream network calls ($N=0$).
</p>

<p>
<strong>FR-9: Outbound Whole-Response Buffering</strong><br>
<em>Description:</em> Downstream token streams shall be accumulated before client egress.<br>
<em>Processing:</em> Policy prohibits raw token streaming (<code>stream=false</code>); buffer collects full generated response.<br>
<em>Output:</em> Complete text buffer passed to Layer 2 inspection engine.
</p>

<p>
<strong>FR-10: Outbound System Prompt and Preamble Disclosure Detection</strong><br>
<em>Description:</em> The generated response shall be scanned for leaked system prompt preambles.<br>
<em>Processing:</em> Pattern matching checks for system headers, XML system tags, and confidential operational rules.<br>
<em>Output:</em> If leak score $\ge 85$, enforce BLOCK & WITHHOLD; deliver secure alert placeholder.
</p>

<p>
<strong>FR-11: Live Secret and API Key Scanning</strong><br>
<em>Description:</em> Outbound responses shall be scanned for exposed credentials and private keys.<br>
<em>Processing:</em> Regex scanners search for OpenAI keys (<code>sk-*</code>), GitHub tokens (<code>ghp_*</code>), Google Cloud keys (<code>AIza*</code>), private keys, and database URIs.<br>
<em>Output:</em> If detected, withhold response and log critical credential breach event.
</p>

<p>
<strong>FR-12: Personally Identifiable Information (PII) Redaction</strong><br>
<em>Description:</em> Personal identity numbers and financial credentials in responses shall be masked.<br>
<em>Processing:</em> Detect SSNs, credit cards (with Luhn validation), and emails; substitute matches with <code>[REDACTED_PII]</code>.<br>
<em>Output:</em> Sanitized text returned under verdict <code>MASK</code>.
</p>

<div class="table-caption">Table 3.3: Comprehensive Functional Requirements Specification (FR-1 to FR-12)</div>
<table>
    <tr>
        <th style="width: 12%;">Req. ID</th>
        <th style="width: 22%;">Requirement Name</th>
        <th style="width: 48%;">Functional Description & Input/Output Mapping</th>
        <th style="width: 18%;">Priority / Status</th>
    </tr>
    <tr>
        <td><strong>FR-1</strong></td>
        <td>Inbound Screening</td>
        <td>Intercept all inbound text prompts and compute continuous risk scores prior to model execution.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-2</strong></td>
        <td>Decoupled Parsing</td>
        <td>Extract text from DOCX, PDF, and TXT attachments independently of user prompt text.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-3</strong></td>
        <td>Image OCR Scanning</td>
        <td>Ingest PNG/JPG attachments and perform optical character recognition via Tesseract.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-4</strong></td>
        <td>Threat Attribution</td>
        <td>Tag every request with provenance: <code>threat_source &in; {{Prompt, Attachment, Both, None}}</code>.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-5</strong></td>
        <td>Head-Tail Tokens</td>
        <td>Extract 127 head and 127 tail tokens into a 256-token sequence to defeat sequence hiding.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-6</strong></td>
        <td>Neural-Rule Fusion</td>
        <td>Compute $R_{{fused}} = 0.40 R_{{rule}} + 0.60 R_{{ML}}$; enforce decision band mappings.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-7</strong></td>
        <td>Decision Gating</td>
        <td>Immediately abort processing if $R_{{fused}} \ge 38.0$; guarantee zero downstream LLM calls ($N=0$).</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-8</strong></td>
        <td>Response Buffering</td>
        <td>Enforce whole-response accumulation; prohibit streaming (<code>stream=false</code>) to ensure inspection.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-9</strong></td>
        <td>Disclosure Detection</td>
        <td>Scan generated text for system headers and preamble patterns; withhold output if score $\ge 85$.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-10</strong></td>
        <td>Secret/Key Scanning</td>
        <td>Detect live credential signatures (<code>sk-*</code>, <code>ghp_*</code>, <code>AIza*</code>, private keys, DB URIs) and block delivery.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-11</strong></td>
        <td>PII Masking</td>
        <td>Identify Social Security numbers, credit cards, and emails; replace with <code>[REDACTED_PII]</code>.</td>
        <td>Mandatory / Implemented</td>
    </tr>
    <tr>
        <td><strong>FR-12</strong></td>
        <td>OpenAI Proxy</td>
        <td>Expose <code>POST /v1/chat/completions</code> returning standard OpenAI schema with content filters.</td>
        <td>Mandatory / Implemented</td>
    </tr>
</table>

<h2 class="section-title">3.5 Non-Functional Requirements Specification</h2>
<p>
The non-functional requirements define the quality attributes, security constraints, and operational bounds required of the system, summarized in Table 3.4.
</p>

<div class="table-caption">Table 3.4: Non-Functional Requirements Specification and Operational Thresholds</div>
<table>
    <tr>
        <th style="width: 15%;">Req. ID</th>
        <th style="width: 25%;">Quality Attribute</th>
        <th style="width: 42%;">Operational Specification & Tolerance Bound</th>
        <th style="width: 18%;">Verification Method</th>
    </tr>
    <tr>
        <td><strong>NFR-1</strong></td>
        <td>Performance & Latency</td>
        <td>Layer 1 evaluation latency must execute within $<50$ms on GPU/MPS and $<100$ms on CPU.</td>
        <td>Benchmarked (29.3ms)</td>
    </tr>
    <tr>
        <td><strong>NFR-2</strong></td>
        <td>Fail-Closed Security</td>
        <td>In the event of model corruption or weight missing, gateway degrades to rule-only blocking.</td>
        <td>Verified by Tests</td>
    </tr>
    <tr>
        <td><strong>NFR-3</strong></td>
        <td>Cryptographic Integrity</td>
        <td>Model weights must verify against exact SHA-256 digest on startup before accepting requests.</td>
        <td>Verified on Startup</td>
    </tr>
    <tr>
        <td><strong>NFR-4</strong></td>
        <td>Zero Over-Defense</td>
        <td>False positive rate on educational and defensive cybersecurity inquiries must remain $\le 0.5\%$.</td>
        <td>Holdout Test (0.00%)</td>
    </tr>
    <tr>
        <td><strong>NFR-5</strong></td>
        <td>Forensic Auditability</td>
        <td>100% of analyzed requests, scores, verdicts, and IP provenance must be logged to SQLite.</td>
        <td>Audit DB Inspection</td>
    </tr>
    <tr>
        <td><strong>NFR-6</strong></td>
        <td>UI Responsiveness</td>
        <td>Security blocker dialogs must remain fully accessible at 100% zoom without screen overflow.</td>
        <td>Playwright/DOM Tests</td>
    </tr>
    <tr>
        <td><strong>NFR-7</strong></td>
        <td>Browser Compatibility</td>
        <td>Extension must intercept submissions across standard textareas and ProseMirror contenteditable.</td>
        <td>Extension Parity Tests</td>
    </tr>
    <tr>
        <td><strong>NFR-8</strong></td>
        <td>Reliability</td>
        <td>Zero regression across 288 automated integration tests spanning 17 subsystem test modules.</td>
        <td>Pytest Suite (100%)</td>
    </tr>
</table>

<h2 class="section-title">3.6 Use Case Formal Specifications</h2>
<p>
To formalize user and system interactions, the primary operational workflows are structured as detailed use cases in Tables 3.5 through 3.7.
</p>

<div class="table-caption">Table 3.5: Use Case UC-1: Inbound Prompt Submission and Real-Time Risk Gating</div>
<table>
    <tr>
        <th style="width: 25%;">Use Case Element</th>
        <th style="width: 75%;">Detailed Specification</th>
    </tr>
    <tr>
        <td><strong>Use Case ID & Name</strong></td>
        <td>UC-1: Inbound Prompt Submission and Real-Time Risk Gating</td>
    </tr>
    <tr>
        <td><strong>Primary Actor</strong></td>
        <td>End User / Enterprise Application Client</td>
    </tr>
    <tr>
        <td><strong>Preconditions</strong></td>
        <td>Gateway Flask server is running; DistilBERT model weights verified with SHA-256 digest on startup.</td>
    </tr>
    <tr>
        <td><strong>Trigger</strong></td>
        <td>Client dispatches HTTP POST request to <code>/analyze</code> or <code>/v1/chat/completions</code>.</td>
    </tr>
    <tr>
        <td><strong>Main Success Scenario</strong></td>
        <td>
            1. Gateway intercepts prompt and tokenizes sequence via Head-Tail algorithm (127 head + 127 tail).<br>
            2. Heuristic engine calculates regex score $R_{{rule}}$; DistilBERT calculates ML probability $R_{{ML}}$.<br>
            3. Fusion engine calculates $R_{{fused}} = 0.40 R_{{rule}} + 0.60 R_{{ML}}$.<br>
            4. If $R_{{fused}} < 38.00$, verdict is ALLOW. Request is forwarded to downstream LLM.<br>
            5. Downstream model generates response; Layer 2 inspects text; sanitized response returned to client.<br>
            6. Audit log entry recorded in SQLite database.
        </td>
    </tr>
    <tr>
        <td><strong>Alternate Flow (Attack)</strong></td>
        <td>
            3a. If $R_{{fused}} \ge 38.00$, verdict is BLOCK.<br>
            3b. Downstream LLM invocation is aborted immediately ($N=0$).<br>
            3c. Gateway returns HTTP 200/403 with detailed security violation JSON and threat category.<br>
            3d. Browser extension renders viewport-constrained modal blocking prompt submission.
        </td>
    </tr>
    <tr>
        <td><strong>Postconditions</strong></td>
        <td>Transaction recorded in SQLite database; security metrics incremented in real-time.</td>
    </tr>
</table>

<div class="table-caption">Table 3.6: Use Case UC-2: Multi-Modal Attachment Ingestion and Carrier Injection Defense</div>
<table>
    <tr>
        <th style="width: 25%;">Use Case Element</th>
        <th style="width: 75%;">Detailed Specification</th>
    </tr>
    <tr>
        <td><strong>Use Case ID & Name</strong></td>
        <td>UC-2: Multi-Modal Attachment Ingestion and Carrier Injection Defense</td>
    </tr>
    <tr>
        <td><strong>Primary Actor</strong></td>
        <td>End User uploading document (DOCX, PDF, image) alongside conversational query</td>
    </tr>
    <tr>
        <td><strong>Preconditions</strong></td>
        <td>File upload size $\le 20$ MB; file type in supported extensions (.docx, .pdf, .txt, .png, .jpg).</td>
    </tr>
    <tr>
        <td><strong>Trigger</strong></td>
        <td>User attaches document and submits form via Web UI or API.</td>
    </tr>
    <tr>
        <td><strong>Main Success Scenario</strong></td>
        <td>
            1. Gateway receives multipart payload; extracts raw user prompt and binary file stream.<br>
            2. Attachment parser routes file to specialized extraction module:<br>
            &nbsp;&nbsp;&nbsp;&bull; DOCX: traverses XML paragraph, table cells, and header/footer elements.<br>
            &nbsp;&nbsp;&nbsp;&bull; PDF: decompresses object text streams.<br>
            &nbsp;&nbsp;&nbsp;&bull; Image: applies contrast enhancement and executes Tesseract OCR.<br>
            3. User prompt is evaluated ($R_{{prompt}}$); extracted document text is evaluated independently ($R_{{attach}}$).<br>
            4. Overall risk computed as $R_{{overall}} = \max(R_{{prompt}}, R_{{attach}})$.<br>
            5. Threat provenance tagged: <code>threat_source &in; {{User Prompt, Attachment, Both, None}}</code>.<br>
            6. If $R_{{overall}} < 38.00$, combined prompt and document context forwarded to LLM.
        </td>
    </tr>
    <tr>
        <td><strong>Alternate Flow (Carrier Attack)</strong></td>
        <td>
            4a. If $R_{{attach}} \ge 38.00$ while $R_{{prompt}} < 38.00$, threat source tagged as "Attachment".<br>
            4b. Execution halted before calling LLM; user notified that uploaded document contains hostile payload.
        </td>
    </tr>
    <tr>
        <td><strong>Postconditions</strong></td>
        <td>Carrier injection blocked; user cleared of malicious intent score if prompt itself was benign.</td>
    </tr>
</table>

<div class="table-caption">Table 3.7: Use Case UC-3: Outbound Response Sanitization and Credential Leak Interception</div>
<table>
    <tr>
        <th style="width: 25%;">Use Case Element</th>
        <th style="width: 75%;">Detailed Specification</th>
    </tr>
    <tr>
        <td><strong>Use Case ID & Name</strong></td>
        <td>UC-3: Outbound Response Sanitization and Credential Leak Interception</td>
    </tr>
    <tr>
        <td><strong>Primary Actor</strong></td>
        <td>Downstream Generative Model responding to an approved user request</td>
    </tr>
    <tr>
        <td><strong>Preconditions</strong></td>
        <td>Inbound prompt was approved by Layer 1; response generated by downstream LLM.</td>
    </tr>
    <tr>
        <td><strong>Trigger</strong></td>
        <td>Downstream model completes generation and returns output text to gateway.</td>
    </tr>
    <tr>
        <td><strong>Main Success Scenario</strong></td>
        <td>
            1. Gateway buffers complete generated response in memory (streaming prohibited).<br>
            2. Response scanner executes regex secret catalog (OpenAI, GitHub, Google, AWS, private keys).<br>
            3. Scanner evaluates PII regexes (SSNs, credit cards with Luhn check, emails).<br>
            4. Scanner calculates system preamble leakage similarity score.<br>
            5. Scanner calculates n-gram uniqueness ratio to detect token degeneration loops.<br>
            6. If clean, text returned to client; if PII detected, masked with <code>[REDACTED_PII]</code>.<br>
            7. Response delivered to end user with sub-5ms inspection overhead.
        </td>
    </tr>
    <tr>
        <td><strong>Alternate Flow (Credential Leak)</strong></td>
        <td>
            4a. If live API key or private key detected in response text, verdict is BLOCK.<br>
            4b. Output text is completely withheld from client.<br>
            4c. Generic security alert delivered: <em>"Response blocked due to sensitive credential disclosure."</em><br>
            4d. High-severity security incident logged in forensic database.
        </td>
    </tr>
    <tr>
        <td><strong>Postconditions</strong></td>
        <td>Zero credentials leaked to client; incident logged for security operations review.</td>
    </tr>
</table>

<h2 class="section-title">3.7 Requirements Traceability Matrix</h2>
<p>
To ensure complete verification and full engineering rigor, Table 3.8 maps every functional and non-functional requirement to the corresponding architectural subsystem and automated regression test suite.
</p>

<div class="table-caption">Table 3.8: Requirements Traceability Matrix Linking Requirements to Test Modules</div>
<table>
    <tr>
        <th style="width: 15%;">Requirement ID</th>
        <th style="width: 25%;">Subsystem Module</th>
        <th style="width: 35%;">Automated Pytest Verification Suite</th>
        <th style="width: 25%;">Pass Criteria & Status</th>
    </tr>
    <tr>
        <td><strong>FR-1, FR-6</strong></td>
        <td><code>backend/prompt_security/</code></td>
        <td><code>test_detection.py</code>, <code>test_threat_taxonomy_nine_categories.py</code></td>
        <td>Accuracy $>98\%$, F1 $>0.98$ (PASSED)</td>
    </tr>
    <tr>
        <td><strong>FR-2, FR-4</strong></td>
        <td><code>backend/attachments/</code></td>
        <td><code>test_attachments.py</code>, <code>test_docx_indirect_injection.py</code></td>
        <td>100% indirect attack detection (PASSED)</td>
    </tr>
    <tr>
        <td><strong>FR-3</strong></td>
        <td><code>backend/attachments/</code></td>
        <td><code>test_attachments_image_ocr.py</code></td>
        <td>100% OCR text extraction (PASSED)</td>
    </tr>
    <tr>
        <td><strong>FR-5</strong></td>
        <td><code>backend/preprocessing/</code></td>
        <td><code>test_detection.py::test_head_tail_tokens</code></td>
        <td>Boundary payload capture (PASSED)</td>
    </tr>
    <tr>
        <td><strong>FR-7</strong></td>
        <td><code>backend/prompt_security/</code></td>
        <td><code>test_threat_taxonomy_nine_categories.py</code></td>
        <td>0.00% FPR on hard negatives (PASSED)</td>
    </tr>
    <tr>
        <td><strong>FR-8</strong></td>
        <td><code>backend/app.py</code></td>
        <td><code>test_dual_layer.py</code>, <code>test_scenarios_a_to_h.py</code></td>
        <td>$N=0$ downstream calls on block (PASSED)</td>
    </tr>
    <tr>
        <td><strong>FR-9..FR-12</strong></td>
        <td><code>backend/response_security/</code></td>
        <td><code>test_layer2_demo.py</code>, <code>test_dual_layer.py</code></td>
        <td>100% secret interception, PII mask (PASSED)</td>
    </tr>
    <tr>
        <td><strong>NFR-1</strong></td>
        <td>Hardware Runtimes</td>
        <td>Latency benchmark test harness</td>
        <td>$<50$ms on MPS/CUDA (PASSED: 29.3ms)</td>
    </tr>
    <tr>
        <td><strong>NFR-2, NFR-3</strong></td>
        <td>Model Pipeline</td>
        <td><code>test_model_integrity.py</code></td>
        <td>SHA-256 match, fail-closed (PASSED)</td>
    </tr>
    <tr>
        <td><strong>NFR-6, NFR-7</strong></td>
        <td>Extension & Web UI</td>
        <td><code>test_extension_interception.py</code>, <code>test_block_dialog_ui.py</code></td>
        <td>Viewport fit, zero overflow (PASSED)</td>
    </tr>
    <tr>
        <td><strong>NFR-8</strong></td>
        <td>Entire Framework</td>
        <td>All 17 test modules (288 tests)</td>
        <td>100.0% pass rate (288/288 PASSED)</td>
    </tr>
</table>

<h2 class="section-title">3.8 Security Architecture Risk Analysis & STRIDE Threat Modeling Matrix</h2>
<p>
To ensure comprehensive defensive rigor, the Prompt Security Guard system was evaluated under the Microsoft STRIDE threat modeling framework across all six threat vectors, summarized in Table 3.9.
</p>

<div class="table-caption">Table 3.9: STRIDE Threat Modeling and Architectural Risk Mitigation Matrix</div>
<table>
    <tr>
        <th style="width: 18%;">STRIDE Category</th>
        <th style="width: 25%;">Potential Threat & Attack Surface</th>
        <th style="width: 32%;">Impact on System Assets</th>
        <th style="width: 25%;">Architectural Countermeasure</th>
    </tr>
    <tr>
        <td><strong>Spoofing</strong></td>
        <td>Adversary mimics authorized administrative client to disable gateway guardrails.</td>
        <td>Unauthorized bypass of Layer 1 security; unrestricted LLM access.</td>
        <td>Enforced <code>GATEWAY_API_KEY</code> bearer tokens and PBKDF2 admin password hashing.</td>
    </tr>
    <tr>
        <td><strong>Tampering</strong></td>
        <td>Adversary alters on-disk DistilBERT weights to introduce neural trojan backdoors.</td>
        <td>Subversion of classification logic; intentional false negatives.</td>
        <td>Startup SHA-256 cryptographic hash verification (Digest: <code>c15a14ca...</code>).</td>
    </tr>
    <tr>
        <td><strong>Repudiation</strong></td>
        <td>Malicious insider denies submitting injection attack or exfiltrating data.</td>
        <td>Loss of forensic accountability; inability to audit security breaches.</td>
        <td>Immutable SQLite audit database logging IP, timestamps, scores, and raw payloads.</td>
    </tr>
    <tr>
        <td><strong>Information Disclosure</strong></td>
        <td>LLM reveals confidential developer preambles, API credentials, or customer PII.</td>
        <td>Compromise of internal system logic; credential harvesting; GDPR breaches.</td>
        <td>Layer 2 outbound whole-response inspection, secret regex scanner, and PII masking.</td>
    </tr>
    <tr>
        <td><strong>Denial of Service</strong></td>
        <td>Adversary submits recursive loop prompt or 50MB file to exhaust RAM and GPU memory.</td>
        <td>Gateway crash; resource exhaustion; denial-of-wallet on downstream API bills.</td>
        <td>Strict 20MB file limits, 8,000-character caps, and loop degeneration detection.</td>
    </tr>
    <tr>
        <td><strong>Elevation of Privilege</strong></td>
        <td>Adversary overrides roleplay boundaries to commandeer agentic tool execution.</td>
        <td>Execution of arbitrary agent tools (e.g., database writes, email dispatch).</td>
        <td>Pre-execution Layer 1 blocking (Zero downstream model invocation on attack).</td>
    </tr>
</table>

<h2 class="section-title">3.9 Comprehensive Project Cost and Resource Estimation</h2>
<p>
To substantiate real-world deployment viability, Table 3.10 provides an itemized cost estimation detailing capital expenditure, cloud computing resources, hardware amortization, and engineering person-hours.
</p>

<div class="table-caption">Table 3.10: Itemized Project Cost Estimation and Amortized Resource Budget</div>
<table>
    <tr>
        <th style="width: 15%;">Budget Category</th>
        <th style="width: 32%;">Item / Resource Description</th>
        <th style="width: 28%;">Quantity / Duration</th>
        <th style="width: 25%;">Estimated Cost (INR / USD)</th>
    </tr>
    <tr>
        <td><strong>Compute Hardware</strong></td>
        <td>Apple Silicon M-Series Unified Workstation (Amortized development)</td>
        <td>1 Unit (24 Weeks)</td>
        <td>₹45,000 / $540 (Amortized)</td>
    </tr>
    <tr>
        <td><strong>GPU Cloud Compute</strong></td>
        <td>NVIDIA A100 / RTX 4090 GPU Cloud Instances for DistilBERT fine-tuning</td>
        <td>120 GPU Hours</td>
        <td>₹18,500 / $220</td>
    </tr>
    <tr>
        <td><strong>API Tokens</strong></td>
        <td>OpenAI GPT-4o API tokens for challenge holdout generation & validation</td>
        <td>1.5M Tokens</td>
        <td>₹3,800 / $45</td>
    </tr>
    <tr>
        <td><strong>Storage & Database</strong></td>
        <td>Local SSD storage & encrypted SQLite backup volumes</td>
        <td>500 GB NVMe SSD</td>
        <td>₹6,500 / $78</td>
    </tr>
    <tr>
        <td><strong>Developer Effort</strong></td>
        <td>4 Student Software Engineers (Academic Capstone Research)</td>
        <td>960 Total Person-Hours</td>
        <td>Academic Project (Zero Direct)</td>
    </tr>
    <tr>
        <td><strong>Total Budget</strong></td>
        <td><strong>Complete Engineering Lifecycle Investment</strong></td>
        <td><strong>24 Weeks Duration</strong></td>
        <td><strong>₹73,800 / $883 USD</strong></td>
    </tr>
</table>

<div class="page-break"></div>
"""
