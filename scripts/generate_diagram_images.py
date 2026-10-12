#!/usr/bin/env python3
"""
scripts/generate_diagram_images.py

Renders publication-ready, high-resolution diagrams for Medium articles,
GitHub README, and presentations using Matplotlib and Pillow.

Generated diagrams:
  1. assets/diagrams/pipeline_sequence.png
     - Detailed swimlane / sequence diagram showing fact flow and verification loop.
  2. assets/diagrams/architecture_flowchart.png
     - Clean modern 4-layer architecture flowchart.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def render_pipeline_sequence(output_path: Path):
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_facecolor("#0f141c")
    fig.patch.set_facecolor("#0f141c")

    # Column definitions
    lanes = [
        ("Layer 1: Causal World", 1.8, "#38bdf8", "WorldBuilder\n(NetworkX Multigraph)"),
        ("Layer 2: Fact Planner", 4.8, "#818cf8", "CorpusPlanner\n(Constraint Placement)"),
        ("Layer 3: Compilers", 7.8, "#a78bfa", "Prose & Renderers\n(PDF/DOCX/MD/PNG)"),
        ("Layer 4: Verification", 10.8, "#34d399", "LeakCheck & VLM Gate\n(Closed-Loop Go/No-Go)"),
        ("Final Outputs", 13.5, "#f59e0b", "Corpus + Benchmark\n(public/ & answer_key/)")
    ]

    # Draw lane headers & vertical gridlines
    for title, x, color, sub in lanes:
        # Header box
        box = patches.FancyBboxPatch(
            (x - 1.15, 7.1), 2.3, 0.7,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            facecolor="#1e293b", edgecolor=color, linewidth=1.8
        )
        ax.add_patch(box)
        ax.text(x, 7.5, title, ha="center", va="center", color=color, fontsize=10.5, fontweight="bold")
        ax.text(x, 7.25, sub, ha="center", va="center", color="#94a3b8", fontsize=8.5)

        # Vertical lane dashed line
        ax.plot([x, x], [0.8, 7.0], color="#334155", linestyle="--", linewidth=1.2, zorder=1)

    # Sequence steps (y-levels from 6.3 down to 1.2)
    steps = [
        # (y, x_from, x_to, step_no, text, note, color)
        (6.3, 1.8, 4.8, "1", "Deterministic Causal Multigraph", "571 atomic facts, 8 disputes, temporal invariants", "#38bdf8"),
        (5.3, 4.8, 4.8, "2", "Constraint Satisfaction Optimization", "Hold back 15 visual facts • Split 24 two-hop chains • Route disputes", "#818cf8"),
        (4.3, 4.8, 7.8, "3", "Document Placement Specs", "Assigned atomic facts per doc (Codex, Wiki, Chronicles, Ephemera)", "#818cf8"),
        (3.3, 7.8, 7.8, "4", "Synthesis & Missing-Fact Repair", "Multi-pass LLM compilation • Matplotlib charts • Generative plates", "#a78bfa"),
        (2.3, 7.8, 10.8, "5", "Compiled Drafts + Images", "All documents rendered to target formats (PDF, DOCX, MD, TXT)", "#a78bfa"),
        (1.4, 10.8, 13.5, "6", "Automated Validation Gate", "Lexical leak detection • VLM trait inspection • Go/No-Go decision", "#34d399")
    ]

    for y, x1, x2, num, title, desc, col in steps:
        if x1 != x2:
            # Directed arrow between lanes
            ax.annotate(
                "", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=col, lw=2.2)
            )
            # Step badge
            badge = patches.Circle(((x1 + x2)/2 - 1.1, y), 0.18, facecolor=col, edgecolor="#ffffff", linewidth=1)
            ax.add_patch(badge)
            ax.text((x1 + x2)/2 - 1.1, y, num, ha="center", va="center", color="#0f141c", fontsize=9, fontweight="bold")

            # Label box
            box = patches.FancyBboxPatch(
                ((x1 + x2)/2 - 0.8, y - 0.28), 2.2, 0.56,
                boxstyle="round,pad=0.06,rounding_size=0.1",
                facecolor="#1e293b", edgecolor="#475569", linewidth=1, zorder=3
            )
            ax.add_patch(box)
            ax.text((x1 + x2)/2 + 0.3, y + 0.08, title, ha="center", va="center", color="#f8fafc", fontsize=9, fontweight="bold", zorder=4)
            ax.text((x1 + x2)/2 + 0.3, y - 0.12, desc, ha="center", va="center", color="#94a3b8", fontsize=7.5, zorder=4)
        else:
            # Self-loop / processing box inside lane
            box = patches.FancyBboxPatch(
                (x1 - 1.4, y - 0.32), 2.8, 0.64,
                boxstyle="round,pad=0.08,rounding_size=0.12",
                facecolor="#1e293b", edgecolor=col, linewidth=1.5, zorder=3
            )
            ax.add_patch(box)
            # Badge
            badge = patches.Circle((x1 - 1.15, y), 0.18, facecolor=col, edgecolor="#ffffff", linewidth=1, zorder=4)
            ax.add_patch(badge)
            ax.text(x1 - 1.15, y, num, ha="center", va="center", color="#0f141c", fontsize=9, fontweight="bold", zorder=5)

            ax.text(x1 + 0.1, y + 0.1, title, ha="center", va="center", color="#f8fafc", fontsize=9, fontweight="bold", zorder=4)
            ax.text(x1 + 0.1, y - 0.12, desc, ha="center", va="center", color="#cbd5e1", fontsize=7.5, zorder=4)

    # Title & Subtitle
    ax.text(7.6, 7.85, "SYNTHLORE FACT-PLACEMENT & VERIFICATION SEQUENCE", ha="center", va="center", color="#f8fafc", fontsize=15, fontweight="bold")

    ax.set_xlim(0, 15.2)
    ax.set_ylim(0.5, 8.2)
    ax.axis("off")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Rendered: {output_path}")


def render_architecture_flowchart(output_path: Path):
    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=300)
    ax.set_facecolor("#0b0f17")
    fig.patch.set_facecolor("#0b0f17")

    layers = [
        {
            "num": "LAYER 1",
            "name": "Causal Universe Engine",
            "module": "src/world/builder.py",
            "color": "#38bdf8",
            "x": 0.8, "y": 4.5, "w": 2.6, "h": 2.2,
            "bullets": [
                "• NetworkX directed multigraph",
                "• Temporal causality enforcement",
                "• Global entity uniqueness",
                "• 571 atomic world facts"
            ]
        },
        {
            "num": "LAYER 2",
            "name": "Constraint Fact Planner",
            "module": "src/planning/corpus_planner.py",
            "color": "#818cf8",
            "x": 3.9, "y": 4.5, "w": 2.6, "h": 2.2,
            "bullets": [
                "• 2-Hop non-cohabitation matrix",
                "• Withholds visual-only facts",
                "• Tiered authority dispute routing",
                "• Generates plan.json specs"
            ]
        },
        {
            "num": "LAYER 3",
            "name": "Multi-Format Compilers",
            "module": "src/generation/ & renderer_v2.py",
            "color": "#a78bfa",
            "x": 7.0, "y": 4.5, "w": 2.6, "h": 2.2,
            "bullets": [
                "• Fact-to-prose LLM compilers",
                "• Programmatic Matplotlib plates",
                "• Generative visual plates",
                "• PDF, DOCX, Markdown, TXT"
            ]
        },
        {
            "num": "LAYER 4",
            "name": "Closed-Loop Verification",
            "module": "src/evaluation/ & leakcheck.py",
            "color": "#34d399",
            "x": 10.1, "y": 4.5, "w": 2.6, "h": 2.2,
            "bullets": [
                "• Lexical entity leak detection",
                "• Vision LLM trait confirmation",
                "• Automated repair loop",
                "• Go/No-Go release gate"
            ]
        }
    ]

    for layer in layers:
        x, y, w, h = layer["x"], layer["y"], layer["w"], layer["h"]
        col = layer["color"]

        # Main layer box
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1,rounding_size=0.18",
            facecolor="#161f2e", edgecolor=col, linewidth=1.8
        )
        ax.add_patch(box)

        # Header tag
        tag = patches.FancyBboxPatch(
            (x + 0.15, y + h - 0.38), 0.9, 0.26,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=col, edgecolor=col
        )
        ax.add_patch(tag)
        ax.text(x + 0.6, y + h - 0.25, layer["num"], ha="center", va="center", color="#0b0f17", fontsize=7.5, fontweight="bold")

        # Layer title
        ax.text(x + 0.15, y + h - 0.6, layer["name"], ha="left", va="center", color="#ffffff", fontsize=10.5, fontweight="bold")
        ax.text(x + 0.15, y + h - 0.85, layer["module"], ha="left", va="center", color="#94a3b8", fontsize=8, fontfamily="monospace")

        # Separator line
        ax.plot([x + 0.15, x + w - 0.15], [y + h - 0.98, y + h - 0.98], color="#334155", linewidth=1)

        # Bullets
        by = y + h - 1.25
        for b in layer["bullets"]:
            ax.text(x + 0.15, by, b, ha="left", va="center", color="#cbd5e1", fontsize=8.2)
            by -= 0.24

    # Connectors between layers
    for i in range(3):
        x1 = layers[i]["x"] + layers[i]["w"]
        x2 = layers[i+1]["x"]
        cy = 5.6
        ax.annotate(
            "", xy=(x2, cy), xytext=(x1, cy),
            arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.7", color="#64748b", lw=2.4)
        )

    # Bottom output brackets: Public Corpus vs Answer Key
    bottom_y = 1.3
    # Box 1: Public Corpus
    b1 = patches.FancyBboxPatch(
        (1.5, bottom_y), 4.8, 2.0,
        boxstyle="round,pad=0.1,rounding_size=0.15",
        facecolor="#161f2e", edgecolor="#38bdf8", linewidth=1.5
    )
    ax.add_patch(b1)
    ax.text(3.9, bottom_y + 1.65, "PUBLIC EVALUATION CORPUS", ha="center", va="center", color="#38bdf8", fontsize=11, fontweight="bold")
    ax.text(3.9, bottom_y + 1.25, "415 Documents • ~511,000 Words • 85 Figures", ha="center", va="center", color="#f8fafc", fontsize=9.5)
    ax.text(3.9, bottom_y + 0.85, "• Codex & Annals (PDF/DOCX)   • Narrative Chronicles (PDF/DOCX)", ha="center", va="center", color="#94a3b8", fontsize=8)
    ax.text(3.9, bottom_y + 0.55, "• Wiki Articles (Markdown)      • Ephemera & Letters (TXT/PDF)", ha="center", va="center", color="#94a3b8", fontsize=8)

    # Box 2: Verified Answer Key
    b2 = patches.FancyBboxPatch(
        (7.2, bottom_y), 4.8, 2.0,
        boxstyle="round,pad=0.1,rounding_size=0.15",
        facecolor="#161f2e", edgecolor="#34d399", linewidth=1.5
    )
    ax.add_patch(b2)
    ax.text(9.6, bottom_y + 1.65, "VERIFIED BENCHMARK & ANSWER KEY", ha="center", va="center", color="#34d399", fontsize=11, fontweight="bold")
    ax.text(9.6, bottom_y + 1.25, "70 Verified Multi-Hop / Multimodal Questions", ha="center", va="center", color="#f8fafc", fontsize=9.5)
    ax.text(9.6, bottom_y + 0.85, "• Track 1A: 38 Multimodal questions (visual-only facts & traits)", ha="center", va="center", color="#94a3b8", fontsize=8)
    ax.text(9.6, bottom_y + 0.55, "• Track 1B: 24 Multi-hop chains  • Track 1C: 8 Conflict resolutions", ha="center", va="center", color="#94a3b8", fontsize=8)

    # Arrows from Layer 4 to outputs
    ax.annotate(
        "", xy=(3.9, bottom_y + 2.0), xytext=(11.4, 4.5),
        arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#38bdf8", lw=2, connectionstyle="arc3,rad=0.25")
    )
    ax.annotate(
        "", xy=(9.6, bottom_y + 2.0), xytext=(11.4, 4.5),
        arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#34d399", lw=2, connectionstyle="arc3,rad=-0.15")
    )

    # Main Title
    ax.text(6.75, 7.2, "SYNTHLORE: FOUR-LAYER SYSTEM ARCHITECTURE", ha="center", va="center", color="#f8fafc", fontsize=15, fontweight="bold")

    ax.set_xlim(0, 13.5)
    ax.set_ylim(0.8, 7.6)
    ax.axis("off")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Rendered: {output_path}")


def main():
    root = Path(__file__).resolve().parent.parent
    assets_dir = root / "assets" / "diagrams"

    render_architecture_flowchart(assets_dir / "architecture_flowchart.png")
    render_pipeline_sequence(assets_dir / "pipeline_sequence.png")


if __name__ == "__main__":
    main()
