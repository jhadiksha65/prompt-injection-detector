"""
scripts/generate_architecture_diagram.py
Generates a crisp, publication-grade IEEE conference paper architecture diagram
for the Dual-Layer Prompt Security Gateway.

Output formats:
- figures/pipeline_architecture.png (300 DPI high-resolution for LaTeX/Word)
- paper/figures/pipeline_architecture.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_diagram():
    os.makedirs("figures", exist_ok=True)
    os.makedirs("paper/figures", exist_ok=True)

    fig, ax = plt.subplots(figsize=(15.5, 7.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Background color
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Color Palette - Professional Academic IEEE Style
    c_bg_box = "#F8F9FA"
    c_border_gray = "#BDC3C7"
    c_blue_head = "#1B4F72"
    c_blue_box = "#EAF2F8"
    c_blue_border = "#2980B9"
    c_teal_head = "#0E6251"
    c_teal_box = "#E8F8F5"
    c_teal_border = "#16A085"
    c_orange_head = "#7E5109"
    c_orange_box = "#FEF9E7"
    c_orange_border = "#F39C12"
    c_purple_head = "#4A235A"
    c_purple_box = "#F4ECF7"
    c_purple_border = "#8E44AD"
    c_red_head = "#78281F"
    c_red_box = "#FDEDEC"
    c_red_border = "#C0392B"
    c_green_head = "#145A32"
    c_green_box = "#EAFAF1"
    c_green_border = "#27AE60"

    # Helper function for drawing rounded boxes
    def draw_box(x, y, w, h, title, subtitle, items, head_bg, body_bg, border_col, title_col="white"):
        # Body
        body = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                     linewidth=1.4, edgecolor=border_col, facecolor=body_bg)
        ax.add_patch(body)
        
        # Header banner
        head_h = 4.2
        head_y = y + h - head_h
        head = patches.FancyBboxPatch((x, head_y), w, head_h, boxstyle="round,pad=0.1,rounding_size=1.0",
                                     linewidth=1.0, edgecolor=border_col, facecolor=head_bg)
        ax.add_patch(head)
        
        # Title text
        ax.text(x + w/2.0, head_y + head_h/2.0, title, ha='center', va='center',
                fontsize=9.5, fontweight='bold', color=title_col, family='sans-serif')
        
        # Subtitle
        if subtitle:
            ax.text(x + w/2.0, head_y - 2.0, subtitle, ha='center', va='center',
                    fontsize=8.0, fontweight='bold', color=border_col, family='sans-serif')
            start_y = head_y - 4.2
        else:
            start_y = head_y - 2.5
            
        # Items
        line_spacing = 2.4
        for i, item in enumerate(items):
            curr_y = start_y - (i * line_spacing)
            if item.startswith("•") or item.startswith("-"):
                ax.text(x + 1.2, curr_y, item, ha='left', va='center',
                        fontsize=7.8, color='#2C3E50', family='sans-serif')
            elif item.startswith(">>") or item.startswith("**"):
                ax.text(x + w/2.0, curr_y, item.replace("**","").replace(">>",""), ha='center', va='center',
                        fontsize=8.0, fontweight='bold', color='#1A252F', family='sans-serif')
            elif item == "---":
                ax.plot([x + 1.5, x + w - 1.5], [curr_y, curr_y], color=border_col, linestyle='--', linewidth=0.8)
            else:
                ax.text(x + w/2.0, curr_y, item, ha='center', va='center',
                        fontsize=7.8, color='#34495E', family='sans-serif')

    # Helper for simple sub-blocks
    def draw_sub_box(x, y, w, h, text, bg, border, font_size=7.5, bold=False, text_col="#2C3E50"):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.8",
                                     linewidth=1.0, edgecolor=border, facecolor=bg)
        ax.add_patch(box)
        ax.text(x + w/2.0, y + h/2.0, text, ha='center', va='center',
                fontsize=font_size, fontweight='bold' if bold else 'normal', color=text_col, family='sans-serif')

    # ==================== MAIN SECTION PANELS ====================
    # Overall Title Banner
    ax.text(50, 97.2, "DUAL-LAYER PROMPT SECURITY GATEWAY ARCHITECTURE", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1A252F', family='sans-serif')
    ax.text(50, 94.6, "Defense-in-Depth Pipeline: Multi-Modal Decoupling  |  Inbound Neural-Heuristic Fusion (Layer 1)  |  Outbound Response Sanitization (Layer 2)", 
            ha='center', va='center', fontsize=9.0, fontstyle='italic', color='#566573', family='sans-serif')

    # --- 1. CLIENT / INGESTION ZONE (Left: x=2 to 21) ---
    panel1 = patches.Rectangle((1.5, 6), 20.0, 85, linewidth=1.2, edgecolor='#BDC3C7',
                               facecolor='#FAFAFA', linestyle=':')
    ax.add_patch(panel1)
    ax.text(11.5, 88.5, "CLIENTS & INGESTION", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color='#2C3E50', family='sans-serif')

    draw_box(2.8, 62, 17.4, 23, "Client Interfaces", "Untrusted Inputs", [
        "• Web UI Analyzer (Prompt + File)",
        "• Browser Extension Interceptor",
        "• Open WebUI (/v1/chat/completions)",
        "• LangChain / Agent Frameworks",
        "• Organizational API Gateways"
    ], c_blue_head, c_blue_box, c_blue_border)

    draw_box(2.8, 10, 17.4, 48, "Multi-Modal Extraction", "Decoupled Attachment Parsing", [
        "• Direct Text: User Input Box",
        "---",
        ">> Attachment Ingestion Pipeline:",
        "• DOCX: python-docx (XML parser)",
        "• PDF: pypdf (text stream parser)",
        "• Images: pytesseract (OCR engine)",
        "---",
        "Threat Source Attribution:",
        "threat_source ∈ {User Prompt,",
        " Attachment, Both, None}",
        "---",
        "Score Decoupling:",
        "R_overall = max(R_prompt, R_attach)"
    ], c_teal_head, c_teal_box, c_teal_border)

    # --- 2. LAYER 1: INBOUND PERIMETER (Center-Left: x=24 to 53) ---
    panel2 = patches.Rectangle((23.5, 6), 31.0, 85, linewidth=1.5, edgecolor=c_blue_border,
                               facecolor='#F4F9FD', linestyle='-')
    ax.add_patch(panel2)
    ax.text(39.0, 88.5, "LAYER 1: INBOUND THREAT PERIMETER", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=c_blue_head, family='sans-serif')

    # Preprocessing
    draw_sub_box(25.0, 78.5, 28.0, 6.5, 
                 "Head-Tail Tokenizer\n127 head + 127 tail tokens -> 256 tokens ([CLS] ... [SEP])", 
                 "#FFFFFF", c_blue_border, font_size=8.0, bold=True)

    # Parallel detectors
    draw_box(25.0, 50, 13.2, 25, "Heuristic Rules", "Regex & Signatures", [
        "• Override verbs",
        "• Delimiter bypasses",
        "• Exfiltration patterns",
        "• Output: R_rule ∈ [0, 100]"
    ], c_orange_head, c_orange_box, c_orange_border)

    draw_box(39.8, 50, 13.2, 25, "DistilBERT ML", "Fine-Tuned Classifier", [
        "• 6 layers, 66M params",
        "• Head-tail attention",
        "• Calibrated threshold",
        "• Output: R_ML ∈ [0, 100]"
    ], c_purple_head, c_purple_box, c_purple_border)

    # Taxonomy & Risk Fusion Box
    draw_box(25.0, 18, 28.0, 28, "Threat Taxonomy & Calibrated Risk Fusion", "", [
        "Authoritative 9-Category Threat Classification",
        "(Direct, Indirect, Override, Jailbreak, Obfuscation, Carrier, Exfil, Benign, Hard Negatives)",
        "---",
        ">> Weighted Risk Fusion Engine:",
        "R_fused = 0.40 * R_rule + 0.60 * R_ML",
        "Decision Bands: LOW (<30) | MED (30-59) | HIGH (60-79) | CRIT (80-100)"
    ], c_blue_head, "#FFFFFF", c_blue_border)

    # Decision Gate Threshold
    draw_sub_box(25.0, 9, 28.0, 6.8,
                 "DECISION GATE  (θ = 0.3800)\nRfused >= 38.0  ->  BLOCK  |  Rfused < 38.0  ->  ALLOW",
                 "#FEF5E7", "#D35400", font_size=8.0, bold=True, text_col="#A04000")

    # --- 3. CORE GENERATION (Center: x=56.5 to 70.5) ---
    panel3 = patches.Rectangle((56.0, 6), 15.5, 85, linewidth=1.2, edgecolor='#BDC3C7',
                               facecolor='#FAFAFA', linestyle=':')
    ax.add_patch(panel3)
    ax.text(63.75, 88.5, "DOWNSTREAM LLM", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color='#2C3E50', family='sans-serif')

    draw_box(57.2, 48, 13.1, 35, "Protected Model", "Isolated Execution", [
        ">> Configured LLM:",
        "• Ollama (llama3.2:3b)",
        "• OpenAI (gpt-4o)",
        "• Offline Mock / Fallback",
        "---",
        "ZERO Invocation on",
        "Layer 1 BLOCK decisions",
        "(Verified by N=0 assertions)"
    ], c_teal_head, c_teal_box, c_teal_border)

    draw_box(57.2, 10, 13.1, 34, "Egress Buffer", "Anti-Streaming Policy", [
        ">> Whole-Response Buffer:",
        "Streaming (stream=true)",
        "prohibited to prevent",
        "partial secret leakage.",
        "---",
        "Accumulates raw token",
        "stream before Layer 2",
        "deep content analysis."
    ], "#34495E", "#EAEDED", "#7F8C8D")

    # --- 4. LAYER 2: OUTBOUND PERIMETER (Right: x=73.5 to 98.5) ---
    panel4 = patches.Rectangle((73.0, 6), 25.5, 85, linewidth=1.5, edgecolor=c_green_border,
                               facecolor='#F4FAF6', linestyle='-')
    ax.add_patch(panel4)
    ax.text(85.75, 88.5, "LAYER 2: OUTBOUND RESPONSE GUARD", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=c_green_head, family='sans-serif')

    draw_box(74.5, 52, 22.5, 31, "Response Sanitization Engine", "Pre-Egress Deep Inspection", [
        "• System Prompt Disclosure (headers, <system>)",
        "• Secret & API Key Scanner (sk-*, ghp_*, AIza*, DB)",
        "• Automatic PII Redaction (SSN, Cards, Emails)",
        "• Structural & Anomaly Loop Validator (<0.15)",
        "---",
        ">> Enforcement Actions:",
        "Leak Score >= 85: BLOCK & WITHHOLD",
        "PII Found: MASK with [REDACTED_PII]",
        "Benign Safe: ALLOW (Verified safe content)"
    ], c_green_head, "#FFFFFF", c_green_border)

    draw_box(74.5, 27, 22.5, 21, "Forensics & Audit Logger", "Centralized Compliance", [
        "• SQLite Audit Log (prompt_audit.db)",
        "• Records: Timestamp, Client IP, Verdict,",
        "  Risk Score, Latency, Threat Category",
        "• Real-time Incident Dashboard"
    ], "#2C3E50", "#EAECEE", "#5D6D7E")

    draw_box(74.5, 9, 22.5, 15, "Client Delivery", "Secure Egress", [
        "• Sanitized Output Delivered to User",
        "• OpenAI finish_reason: 'stop' / 'content_filter'",
        "• Sub-30ms Hardware-Accelerated Latency"
    ], c_blue_head, c_blue_box, c_blue_border)

    # ==================== CONNECTING ARROWS ====================
    arrow_props = dict(arrowstyle="->,head_width=0.4,head_length=0.6", linewidth=1.6, color="#2C3E50")
    arrow_red = dict(arrowstyle="->,head_width=0.4,head_length=0.6", linewidth=1.6, color="#C0392B", linestyle="--")
    arrow_green = dict(arrowstyle="->,head_width=0.4,head_length=0.6", linewidth=1.6, color="#27AE60")

    # Ingestion -> Preprocessing
    ax.annotate("", xy=(25.0, 81.7), xytext=(20.2, 73.5), arrowprops=arrow_props)
    ax.text(22.6, 78.5, "Prompt", fontsize=7.5, color='#2C3E50', fontweight='bold', ha='center')

    ax.annotate("", xy=(25.0, 81.7), xytext=(20.2, 34.0), arrowprops=arrow_props)
    ax.text(22.6, 56.0, "Attachment Text", fontsize=7.5, color='#2C3E50', fontweight='bold', ha='center')

    # Preprocessing -> Dual Detectors
    ax.annotate("", xy=(31.6, 75.0), xytext=(31.6, 78.5), arrowprops=arrow_props)
    ax.annotate("", xy=(46.4, 75.0), xytext=(46.4, 78.5), arrowprops=arrow_props)

    # Detectors -> Fusion Box
    ax.annotate("", xy=(31.6, 46.0), xytext=(31.6, 50.0), arrowprops=arrow_props)
    ax.annotate("", xy=(46.4, 46.0), xytext=(46.4, 50.0), arrowprops=arrow_props)

    # Fusion -> Decision Gate
    ax.annotate("", xy=(39.0, 15.8), xytext=(39.0, 18.0), arrowprops=arrow_props)

    # Decision Gate -> BLOCK (Early Termination)
    ax.annotate("", xy=(39.0, 0.5), xytext=(39.0, 9.0), arrowprops=arrow_red)
    ax.text(39.0, 3.5, "BLOCK (Risk >= 38%): EARLY TERMINATION (LLM Never Called)", 
            fontsize=8.0, fontweight='bold', color="#C0392B", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#FDEDEC", edgecolor="#C0392B", linewidth=1.0))

    # Decision Gate -> ALLOW (Forward to LLM)
    ax.annotate("", xy=(57.2, 65.0), xytext=(53.0, 12.4), 
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", 
                                connectionstyle="arc3,rad=-0.25", linewidth=1.8, color="#27AE60"))
    ax.text(55.0, 33.0, "ALLOW (<38%)\nForward Safe Prompt", fontsize=7.8, fontweight='bold', color="#27AE60", ha='center')

    # LLM -> Buffer
    ax.annotate("", xy=(63.75, 44.0), xytext=(63.75, 48.0), arrowprops=arrow_props)

    # Buffer -> Layer 2 Sanitization
    ax.annotate("", xy=(74.5, 67.5), xytext=(70.3, 27.0), 
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6",
                                connectionstyle="arc3,rad=-0.22", linewidth=1.8, color="#2980B9"))
    ax.text(72.5, 48.0, "Buffered Raw Output", fontsize=7.8, fontweight='bold', color="#2980B9", ha='center')

    # Layer 2 -> Forensics
    ax.annotate("", xy=(85.75, 48.0), xytext=(85.75, 52.0), arrowprops=arrow_props)

    # Forensics -> Client Delivery
    ax.annotate("", xy=(85.75, 24.0), xytext=(85.75, 27.0), arrowprops=arrow_green)

    # Save outputs
    out_fig1 = "figures/pipeline_architecture.png"
    out_fig2 = "paper/figures/pipeline_architecture.png"
    plt.tight_layout()
    plt.savefig(out_fig1, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.savefig(out_fig2, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated architecture diagram successfully:\n - {out_fig1}\n - {out_fig2}")

if __name__ == "__main__":
    create_architecture_diagram()
