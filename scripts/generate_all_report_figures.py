"""
scripts/generate_all_report_figures.py
Generates all architectural, design, UML, and experimental diagrams
required for the comprehensive B.Tech Blackbook report (60+ pages).
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

os.makedirs("figures/report", exist_ok=True)

def generate_dfd():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), dpi=300)
    
    # ---------------- DFD Level 0 (Context Diagram) ----------------
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 50)
    ax1.axis('off')
    ax1.set_title("Figure 4.2: Data Flow Diagram (DFD Level 0 - Context Level)", fontsize=12, fontweight='bold', pad=15)
    
    # External Entity: User / Client
    b1 = patches.FancyBboxPatch((4, 18), 20, 14, boxstyle="round,pad=0.2", facecolor="#EBF5FB", edgecolor="#2980B9", linewidth=1.5)
    ax1.add_patch(b1)
    ax1.text(14, 25, "External Entity\nUser / Enterprise\nClient App", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#1B4F72")
    
    # Process 0: Security Gateway
    p0 = patches.Circle((50, 25), 11, facecolor="#FEF9E7", edgecolor="#D35400", linewidth=1.8)
    ax1.add_patch(p0)
    ax1.text(50, 25, "0.0\nPrompt Security\nMiddleware &\nGateway", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#7E5109")
    
    # External Entity: Downstream LLM
    b2 = patches.FancyBboxPatch((76, 18), 20, 14, boxstyle="round,pad=0.2", facecolor="#E8F8F5", edgecolor="#16A085", linewidth=1.5)
    ax1.add_patch(b2)
    ax1.text(86, 25, "Downstream Core\nConfigured LLM\n(Ollama / OpenAI)", ha='center', va='center', fontsize=9.5, fontweight='bold', color="#0E6251")
    
    # Data Store: Audit DB
    ds = patches.FancyBboxPatch((40, 2), 20, 7, boxstyle="round,pad=0.1", facecolor="#F4ECF7", edgecolor="#8E44AD", linewidth=1.2)
    ax1.add_patch(ds)
    ax1.text(50, 5.5, "D1: SQLite Audit Forensics", ha='center', va='center', fontsize=8.5, fontweight='bold', color="#4A235A")
    
    # Arrows Level 0
    ax1.annotate("", xy=(39, 27), xytext=(24, 27), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2C3E50"))
    ax1.text(31.5, 29, "Prompt + File", ha='center', va='bottom', fontsize=8, color="#2C3E50")
    
    ax1.annotate("", xy=(24, 22), xytext=(39, 22), arrowprops=dict(arrowstyle="->", lw=1.5, color="#27AE60"))
    ax1.text(31.5, 19.5, "Verified Response / Blocker", ha='center', va='top', fontsize=8, color="#27AE60")
    
    ax1.annotate("", xy=(76, 27), xytext=(61, 27), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2C3E50"))
    ax1.text(68.5, 29, "Approved Prompt", ha='center', va='bottom', fontsize=8, color="#2C3E50")
    
    ax1.annotate("", xy=(61, 22), xytext=(76, 22), arrowprops=dict(arrowstyle="->", lw=1.5, color="#D35400"))
    ax1.text(68.5, 19.5, "Raw Response", ha='center', va='top', fontsize=8, color="#D35400")
    
    ax1.annotate("", xy=(50, 9), xytext=(50, 14), arrowprops=dict(arrowstyle="->", lw=1.2, color="#8E44AD"))
    ax1.text(52, 11.5, "Log Incident", ha='left', va='center', fontsize=8, color="#8E44AD")

    # ---------------- DFD Level 1 (Detailed Subsystems) ----------------
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 50)
    ax2.axis('off')
    ax2.set_title("Figure 4.3: Data Flow Diagram (DFD Level 1 - Detailed Functional Decomposition)", fontsize=12, fontweight='bold', pad=15)
    
    def draw_proc(x, y, num, name, bg="#FEF9E7", border="#D35400"):
        c = patches.Circle((x, y), 5.5, facecolor=bg, edgecolor=border, linewidth=1.5)
        ax2.add_patch(c)
        ax2.text(x, y, f"{num}\n{name}", ha='center', va='center', fontsize=7.5, fontweight='bold', color="#2C3E50")

    draw_proc(12, 38, "1.0", "Ingest &\nDecouple")
    draw_proc(32, 38, "2.0", "Head-Tail\nTokenize")
    draw_proc(52, 38, "3.0", "Layer 1\nFusion")
    draw_proc(72, 38, "4.0", "Decision\nGating")
    draw_proc(88, 20, "5.0", "Forward\nLLM Core")
    draw_proc(62, 10, "6.0", "Layer 2\nSanitize")
    draw_proc(32, 10, "7.0", "Audit Log\n& Forensics")
    draw_proc(12, 20, "8.0", "Deliver\nEgress")

    # Connectors Level 1
    props = dict(arrowstyle="->", lw=1.3, color="#2C3E50")
    ax2.annotate("", xy=(26.5, 38), xytext=(17.5, 38), arrowprops=props)
    ax2.annotate("", xy=(46.5, 38), xytext=(37.5, 38), arrowprops=props)
    ax2.annotate("", xy=(66.5, 38), xytext=(57.5, 38), arrowprops=props)
    ax2.annotate("", xy=(84, 25), xytext=(76, 34), arrowprops=props)
    ax2.text(82, 32, "ALLOW", fontsize=7.5, fontweight='bold', color="#27AE60")
    
    ax2.annotate("", xy=(20, 20), xytext=(70, 33), arrowprops=dict(arrowstyle="->", lw=1.3, color="#C0392B", connectionstyle="arc3,rad=0.2"))
    ax2.text(48, 28, "BLOCK (Early Term)", fontsize=7.5, fontweight='bold', color="#C0392B")

    ax2.annotate("", xy=(67.5, 10), xytext=(83, 17), arrowprops=props)
    ax2.annotate("", xy=(37.5, 10), xytext=(56.5, 10), arrowprops=props)
    ax2.annotate("", xy=(16, 16), xytext=(26.5, 10), arrowprops=props)

    plt.tight_layout()
    plt.savefig("figures/report/fig_dfd.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated figures/report/fig_dfd.png")

def generate_uml_sequence():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_title("Figure 4.4: UML Sequence Diagram of End-to-End Request Lifecycle", fontsize=12, fontweight='bold', pad=15)

    entities = [
        (10, "Client / WebUI"),
        (30, "Gateway Ingest"),
        (50, "Layer 1 Perimeter"),
        (70, "Downstream LLM"),
        (90, "Layer 2 Perimeter")
    ]

    for x, name in entities:
        # Box header
        box = patches.FancyBboxPatch((x - 8, 88), 16, 7, boxstyle="round,pad=0.2", facecolor="#2C3E50", edgecolor="#1A252F")
        ax.add_patch(box)
        ax.text(x, 91.5, name, ha='center', va='center', fontsize=8.5, fontweight='bold', color="white")
        # Lifeline
        ax.plot([x, x], [88, 8], color="#BDC3C7", linestyle="--", lw=1.2)

    # Lifeline events
    events = [
        (82, 10, 30, "1: POST /api/v1/chat/completions (Prompt + Attach)", "#2C3E50", False),
        (74, 30, 50, "2: Decoupled Extraction & Head-Tail Tokens", "#2980B9", False),
        (66, 50, 50, "3: Parallel Heuristic (Rrule) + DistilBERT (RML) Evaluation", "#8E44AD", True),
        (58, 50, 30, "4: Decision Verdict (Rfused < 38% -> ALLOW)", "#27AE60", False),
        (50, 30, 70, "5: Forward Clean Prompt (LLM Invoked)", "#27AE60", False),
        (42, 70, 30, "6: Return Raw Model Tokens (Buffered in RAM)", "#D35400", False),
        (34, 30, 90, "7: Submit Buffered Response for Sanitization", "#2980B9", False),
        (26, 90, 90, "8: System Disclosure, Secret & PII Masking Scan", "#C0392B", True),
        (18, 90, 30, "9: Output Clearance Verdict (ALLOW/MASK)", "#27AE60", False),
        (10, 30, 10, "10: Deliver Sanitized Response to Client", "#27AE60", False)
    ]

    for y, x1, x2, label, col, self_call in events:
        if self_call:
            ax.annotate("", xy=(x1, y - 4), xytext=(x1, y + 2), 
                        arrowprops=dict(arrowstyle="->", lw=1.3, color=col, connectionstyle="arc3,rad=-1.2"))
            ax.text(x1 + 2.5, y - 1, label, fontsize=7.5, fontweight='bold', color=col, va='center')
        else:
            ax.annotate("", xy=(x2, y), xytext=(x1, y), 
                        arrowprops=dict(arrowstyle="->", lw=1.3, color=col))
            ax.text((x1 + x2)/2.0, y + 1.8, label, fontsize=7.8, fontweight='bold', color=col, ha='center')

    plt.tight_layout()
    plt.savefig("figures/report/fig_sequence.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated figures/report/fig_sequence.png")

def generate_er_diagram():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_title("Figure 4.5: Entity-Relationship (ER) Diagram of SQLite Security Forensics Database", fontsize=12, fontweight='bold', pad=15)

    def draw_entity(x, y, w, h, title, fields, border="#2980B9", header_bg="#1B4F72"):
        # Header
        hb = patches.FancyBboxPatch((x, y + h - 5), w, 5, boxstyle="round,pad=0.1", facecolor=header_bg, edgecolor=border)
        ax.add_patch(hb)
        ax.text(x + w/2.0, y + h - 2.5, title, ha='center', va='center', fontsize=9, fontweight='bold', color="white")
        # Body
        bb = patches.FancyBboxPatch((x, y), w, h - 5, boxstyle="round,pad=0.1", facecolor="#F8F9FA", edgecolor=border)
        ax.add_patch(bb)
        for i, (pk_fk, fname, ftype) in enumerate(fields):
            curr_y = y + h - 7.5 - (i * 3.4)
            ax.text(x + 1.5, curr_y, pk_fk, fontsize=7.5, fontweight='bold', color="#C0392B" if "PK" in pk_fk else "#27AE60")
            ax.text(x + 6, curr_y, fname, fontsize=7.5, color="#2C3E50")
            ax.text(x + w - 1.5, curr_y, ftype, fontsize=7.5, fontstyle='italic', color="#7F8C8D", ha='right')

    draw_entity(5, 50, 38, 38, "PROMPT_AUDIT_LOGS", [
        ("PK", "id", "INTEGER"),
        ("  ", "timestamp", "DATETIME"),
        ("  ", "client_ip", "VARCHAR(45)"),
        ("  ", "prompt_text", "TEXT"),
        ("  ", "extracted_attachment", "TEXT"),
        ("  ", "rule_score", "FLOAT"),
        ("  ", "ml_score", "FLOAT"),
        ("  ", "fused_score", "FLOAT"),
        ("FK", "threat_category_id", "INTEGER"),
        ("  ", "decision", "VARCHAR(15)")
    ])

    draw_entity(57, 50, 38, 32, "THREAT_TAXONOMY", [
        ("PK", "category_id", "INTEGER"),
        ("  ", "category_name", "VARCHAR(60)"),
        ("  ", "description", "TEXT"),
        ("  ", "default_action", "VARCHAR(10)"),
        ("  ", "severity_band", "VARCHAR(15)"),
        ("  ", "is_hard_negative", "BOOLEAN"),
        ("  ", "override_priority", "INTEGER")
    ])

    draw_entity(5, 10, 38, 30, "OUTBOUND_LEAKAGE_EVENTS", [
        ("PK", "event_id", "INTEGER"),
        ("FK", "audit_id", "INTEGER"),
        ("  ", "disclosure_score", "FLOAT"),
        ("  ", "credential_type", "VARCHAR(30)"),
        ("  ", "pii_entities_count", "INTEGER"),
        ("  ", "enforced_action", "VARCHAR(15)"),
        ("  ", "sanitization_latency_ms", "FLOAT")
    ])

    draw_entity(57, 10, 38, 30, "SYSTEM_CONFIG_INTEGRATION", [
        ("PK", "config_id", "INTEGER"),
        ("  ", "decision_threshold", "FLOAT (0.3800)"),
        ("  ", "rule_weight", "FLOAT (0.40)"),
        ("  ", "ml_weight", "FLOAT (0.60)"),
        ("  ", "model_sha256", "VARCHAR(64)"),
        ("  ", "active_runtime", "VARCHAR(20)"),
        ("  ", "streaming_policy", "VARCHAR(15)")
    ])

    # Relationships
    ax.annotate("", xy=(57, 70), xytext=(43, 70), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2C3E50"))
    ax.text(50, 72, "1 : N (Categorized As)", fontsize=7.5, fontweight='bold', ha='center', color="#2C3E50")

    ax.annotate("", xy=(24, 40), xytext=(24, 50), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2C3E50"))
    ax.text(25.5, 45, "1 : 1 (Triggers)", fontsize=7.5, fontweight='bold', ha='left', color="#2C3E50")

    plt.tight_layout()
    plt.savefig("figures/report/fig_er.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated figures/report/fig_er.png")

def generate_confusion_matrices():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), dpi=300)
    
    # 1. Rule-Only
    cm1 = np.array([[1500, 0], [1369, 131]])
    ax = axes[0]
    im = ax.imshow(cm1, interpolation='nearest', cmap=plt.cm.Blues)
    ax.set_title("Rule-Only Baseline (>30)\nAcc: 54.37% | Recall: 8.73%", fontsize=10, fontweight='bold')
    tick_marks = np.arange(2)
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(['Benign (0)', 'Malicious (1)'], fontsize=8.5)
    ax.set_yticklabels(['Benign (0)', 'Malicious (1)'], fontsize=8.5)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm1[i, j]:,}", ha="center", va="center", color="white" if cm1[i, j] > 700 else "black", fontsize=10, fontweight='bold')
    ax.set_ylabel('True Label', fontsize=9, fontweight='bold')
    ax.set_xlabel('Predicted Label', fontsize=9, fontweight='bold')

    # 2. DistilBERT
    cm2 = np.array([[1489, 11], [27, 1473]])
    ax = axes[1]
    im = ax.imshow(cm2, interpolation='nearest', cmap=plt.cm.Greens)
    ax.set_title("DistilBERT Transformer (θ=0.38)\nAcc: 98.73% | Recall: 98.20%", fontsize=10, fontweight='bold')
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(['Benign (0)', 'Malicious (1)'], fontsize=8.5)
    ax.set_yticklabels(['Benign (0)', 'Malicious (1)'], fontsize=8.5)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm2[i, j]:,}", ha="center", va="center", color="white" if cm2[i, j] > 700 else "black", fontsize=10, fontweight='bold')
    ax.set_ylabel('True Label', fontsize=9, fontweight='bold')
    ax.set_xlabel('Predicted Label', fontsize=9, fontweight='bold')

    # 3. Hybrid Fusion
    cm3 = np.array([[1489, 11], [18, 1482]])
    ax = axes[2]
    im = ax.imshow(cm3, interpolation='nearest', cmap=plt.cm.Purples)
    ax.set_title("Dual-Layer Fused Middleware\nAcc: 99.03% | Recall: 98.80%", fontsize=10, fontweight='bold')
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(['Benign (0)', 'Malicious (1)'], fontsize=8.5)
    ax.set_yticklabels(['Benign (0)', 'Malicious (1)'], fontsize=8.5)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm3[i, j]:,}", ha="center", va="center", color="white" if cm3[i, j] > 700 else "black", fontsize=10, fontweight='bold')
    ax.set_ylabel('True Label', fontsize=9, fontweight='bold')
    ax.set_xlabel('Predicted Label', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig("figures/report/fig_confusion_matrix.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated figures/report/fig_confusion_matrix.png")

def generate_gantt_chart():
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=300)
    
    stages = [
        "1. Problem Formulation & Threat Modeling",
        "2. Corpus Collection & Three-Phase Lineage",
        "3. Model Architecture & DistilBERT Fine-Tuning",
        "4. Inbound Layer 1 Heuristic Pattern Design",
        "5. Decoupled Multi-Modal Attachment & OCR",
        "6. Outbound Layer 2 Leakage & PII Sanitizer",
        "7. Gateway Reverse Proxy (/v1/chat/completions)",
        "8. Chromium Browser Extension Engine",
        "9. Automated Regression Testing (288 Tests)",
        "10. Conference Paper & Blackbook Documentation"
    ]
    
    start_weeks = [1, 3, 5, 8, 10, 12, 14, 16, 18, 20]
    durations =   [3, 3, 4, 3,  3,  3,  3,  3,  3,  4]
    colors = ["#1B4F72", "#2980B9", "#8E44AD", "#D35400", "#16A085", "#27AE60", "#2C3E50", "#7E5109", "#C0392B", "#145A32"]

    y_pos = np.arange(len(stages))
    ax.barh(y_pos, durations, left=start_weeks, height=0.55, align='center', color=colors, alpha=0.85, edgecolor="#1A252F")
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages, fontsize=9, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlabel('Project Timeline (Weeks - Academic Year 2026-27)', fontsize=10, fontweight='bold')
    ax.set_xlim(0, 26)
    ax.set_xticks(range(0, 27, 2))
    ax.set_xticklabels([f"W{i}" for i in range(0, 27, 2)], fontsize=8.5)
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    ax.set_title("Figure 3.1: Project Work Breakdown Structure and Milestone Gantt Chart", fontsize=11, fontweight='bold', pad=12)

    plt.tight_layout()
    plt.savefig("figures/report/fig_gantt.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated figures/report/fig_gantt.png")

if __name__ == "__main__":
    generate_dfd()
    generate_uml_sequence()
    generate_er_diagram()
    generate_confusion_matrices()
    generate_gantt_chart()
