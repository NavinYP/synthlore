"""Programmatic figure plates for track 1A.

These carry the visual-only facts. They are rendered with matplotlib so the
numbers are pixel-perfect and guaranteed legible - unlike diffusion-generated
images, which garble digits and would make 1A questions unanswerable. Styling
imitates plates from an old tabletop rulebook (parchment, ink, ornate frames).
"""
import os
from typing import Dict, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge

PARCHMENT = "#efe6cf"
INK = "#2b1d12"
ACCENT = "#8c2f2f"
FADED = "#7a6a52"

PROP_LABELS = {
    "garrison_strength": ("Recorded Garrison Strength", "souls under arms"),
    "casualty_figure": ("Recorded Casualties", "souls lost"),
    "attunement_cost": ("Attunement Cost", "vitae-grains"),
    "threat_rating": ("Threat Rating", "of 10, per the Vanguard scale"),
}

# Fictional reference constants for comparison bars (NOT entities - no leakage).
REFERENCE_STANDARDS = {
    "garrison_strength": [("Old Imperial minimum", 800), ("Border-march standard", 2400), ("Great Keep standard", 6000)],
    "casualty_figure": [("A 'skirmish' by the Annals' scale", 2000), ("A 'campaign' by the Annals' scale", 20000), ("A 'ruination' by the Annals' scale", 60000)],
    "attunement_cost": [("Novice tolerance", 20), ("Adept tolerance", 55), ("Master tolerance", 85)],
    "threat_rating": [("Nuisance", 3), ("Menace", 6), ("Calamity", 9)],
}


def _new_plate(title: str):
    fig, ax = plt.subplots(figsize=(7, 7), dpi=150)
    fig.patch.set_facecolor(PARCHMENT)
    ax.set_facecolor(PARCHMENT)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    for pad, lw in [(0.15, 2.5), (0.35, 1.0)]:
        ax.add_patch(Rectangle((pad, pad), 10 - 2 * pad, 10 - 2 * pad,
                               fill=False, edgecolor=INK, linewidth=lw))
    ax.text(5, 9.1, title, ha="center", va="center", fontsize=15,
            color=INK, family="serif", weight="bold")
    ax.plot([2, 8], [8.65, 8.65], color=ACCENT, linewidth=1.2)
    return fig, ax


def render_spec_plate(fig_spec: Dict[str, Any], out_path: str):
    label, unit = PROP_LABELS.get(fig_spec["prop"], (fig_spec["prop"].replace("_", " ").title(), ""))
    fig, ax = _new_plate(fig_spec["entity_name"])
    ax.text(5, 7.4, label.upper(), ha="center", fontsize=12, color=FADED, family="serif")
    ax.text(5, 5.6, f"{fig_spec['value']:,}", ha="center", fontsize=46,
            color=ACCENT, family="serif", weight="bold")
    ax.text(5, 4.3, unit, ha="center", fontsize=11, color=INK, family="serif", style="italic")
    ax.text(5, 1.2, "As entered into the Codex Vaeloria. Figures verified by the Silent Choir.",
            ha="center", fontsize=8, color=FADED, family="serif", style="italic")
    fig.savefig(out_path, facecolor=PARCHMENT, bbox_inches="tight")
    plt.close(fig)


def render_tally_chart(fig_spec: Dict[str, Any], out_path: str):
    label, unit = PROP_LABELS.get(fig_spec["prop"], (fig_spec["prop"].replace("_", " ").title(), ""))
    refs = REFERENCE_STANDARDS.get(fig_spec["prop"], [])
    rows = refs + [(fig_spec["entity_name"], fig_spec["value"])]
    fig, ax = _new_plate(f"{fig_spec['entity_name']} - {label}")
    max_v = max(v for _, v in rows) * 1.15
    y = 7.3
    for name, v in rows:
        is_subject = name == fig_spec["entity_name"]
        width = 5.5 * (v / max_v)
        ax.add_patch(Rectangle((3.3, y - 0.28), width, 0.56,
                               facecolor=ACCENT if is_subject else FADED,
                               edgecolor=INK, linewidth=0.8))
        ax.text(3.2, y - 0.55, name, ha="left", va="center", fontsize=8.5,
                color=INK, family="serif", weight="bold" if is_subject else "normal")
        ax.text(3.45 + width, y, f"{v:,}", ha="left", va="center", fontsize=10,
                color=ACCENT if is_subject else INK, family="serif",
                weight="bold" if is_subject else "normal")
        y -= 1.5
    ax.text(5, 1.0, f"Measured in {unit}." if unit else "", ha="center",
            fontsize=8.5, color=FADED, family="serif", style="italic")
    fig.savefig(out_path, facecolor=PARCHMENT, bbox_inches="tight")
    plt.close(fig)


def render_gauge_plate(fig_spec: Dict[str, Any], out_path: str):
    label, unit = PROP_LABELS.get(fig_spec["prop"], (fig_spec["prop"].replace("_", " ").title(), ""))
    refs = REFERENCE_STANDARDS.get(fig_spec["prop"], [("max", fig_spec["value"] * 1.5)])
    max_v = max(max(v for _, v in refs), fig_spec["value"]) * 1.2
    frac = fig_spec["value"] / max_v
    fig, ax = _new_plate(fig_spec["entity_name"])
    ax.add_patch(Wedge((5, 3.4), 3.1, 0, 180, width=0.8, facecolor="#ddd0b4", edgecolor=INK))
    ax.add_patch(Wedge((5, 3.4), 3.1, 180 - frac * 180, 180, width=0.8,
                       facecolor=ACCENT, edgecolor=INK))
    ax.text(5, 4.4, f"{fig_spec['value']:,}", ha="center", fontsize=34,
            color=ACCENT, family="serif", weight="bold")
    ax.text(5, 7.6, label.upper(), ha="center", fontsize=12, color=FADED, family="serif")
    ax.text(5, 2.2, unit, ha="center", fontsize=10, color=INK, family="serif", style="italic")
    ax.text(1.7, 3.0, "0", fontsize=9, color=INK, family="serif")
    ax.text(7.9, 3.0, f"{int(max_v):,}", fontsize=9, color=INK, family="serif")
    fig.savefig(out_path, facecolor=PARCHMENT, bbox_inches="tight")
    plt.close(fig)


RENDERERS = {
    "spec_plate": render_spec_plate,
    "tally_chart": render_tally_chart,
    "gauge_plate": render_gauge_plate,
}


def render_all_figures(figures: Dict[str, Dict[str, Any]], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for fig_spec in figures.values():
        RENDERERS[fig_spec["style"]](fig_spec, os.path.join(out_dir, fig_spec["filename"]))
