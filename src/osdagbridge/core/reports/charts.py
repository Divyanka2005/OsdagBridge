"""Matplotlib chart helpers for the design report (UR charts, material charts)."""
import os
import re
import tempfile

import matplotlib
matplotlib.use("Agg")          # no GUI window; safe inside the Qt app
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Colours are imported from the central style module (Task 6)
from osdagbridge.core.reports.styles import (
    COLOR_PASS, COLOR_FAIL,
    COLOR_STEEL, COLOR_CONC, COLOR_REBAR,
)

_OUTDIR = tempfile.mkdtemp(prefix="osdag_report_charts_")


def to_float(value):
    """'0.84', 0.84 or '\\textcolor{red}{2.67}' -> float; '—' / None -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group()) if m else None


def _group_of(label):
    l = label.lower()
    if l.startswith("girder"):
        return "Steel Plate Girders"
    if l.startswith("deck") or "(slab)" in l:
        return "Concrete Deck Slab"
    if l.startswith("cross bracing"):
        return "Cross Bracing"
    if l.startswith("end diaphragm"):
        return "End Diaphragms"
    return None


def ur_bar_chart(title, labels, urs, fname):
    fig, ax = plt.subplots(figsize=(7, 3.3))
    colors = [COLOR_FAIL if u > 1.0 else COLOR_PASS for u in urs]
    bars = ax.bar(range(len(urs)), urs, color=colors, width=0.6)
    ax.axhline(1.0, color="red", linestyle="--", linewidth=1.5, label="UR = 1.0")
    ax.set_ylabel("Utilization Ratio")
    ax.set_title(title, fontsize=10)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, max(1.2, max(urs) * 1.15))
    for b, u in zip(bars, urs):
        ax.text(b.get_x() + b.get_width() / 2, u, f"{u:.2f}",
                ha="center", va="bottom", fontsize=8)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    path = os.path.join(_OUTDIR, fname)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path.replace("\\", "/")        # LaTeX needs forward slashes


def build_ur_charts_latex(rows):
    """
    rows: list of (label, ur) taken from the Table 5.29 data,
          e.g. [("Girder — Moment", "0.19"), ("Deck — Flexure (sagging)", 0.89), ...]
    Returns a LaTeX string with one figure per element group.
    """
    groups = {}
    for label, ur in rows:
        g, u = _group_of(label), to_float(ur)
        if g is None or u is None:
            continue
        short = re.sub(r"^(Girder|Deck|Cross Bracing|End Diaphragm)\s*[—-]\s*", "", label)
        groups.setdefault(g, []).append((short, u))

    out = []
    order = ["Steel Plate Girders", "Concrete Deck Slab", "Cross Bracing", "End Diaphragms"]
    for i, g in enumerate(order, 1):
        if g not in groups:
            continue
        labels, urs = zip(*groups[g])
        path = ur_bar_chart(f"Utilization Ratio: {g}", list(labels), list(urs), f"ur_{i}.png")
        out.append(
            "\\begin{figure}[H]\n\\centering\n"
            f"\\includegraphics[width=0.9\\textwidth]{{{path}}}\n"
            f"\\caption{{Utilization Ratio (Demand/Capacity) -- {g}}}\n"
            "\\end{figure}\n"
        )
    return "\n".join(out)



# =============================================================================
# Task 5 — Material Quantity Bar Charts (Chapter 7)
# =============================================================================

import matplotlib.ticker as mticker

COLOR_STEEL = "#4472C4"   # Blue   — structural steel bars
COLOR_CONC  = "#ED7D31"   # Orange — concrete volume bar
COLOR_REBAR = "#70AD47"   # Green  — reinforcement steel bar


def _safe_float(value):
    """Convert a string/number to float; return None for 'N.A.' / None / ''."""
    if value is None or str(value).strip() in ("", "N.A.", "N/A", "---"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def steel_tonnage_chart(labels, weights_mt, fname):
    """Bar chart: Structural Steel Tonnage (MT) for each member group."""
    fig, ax = plt.subplots(figsize=(7, 3.5))
    x = range(len(labels))
    bars = ax.bar(x, weights_mt, color=COLOR_STEEL, width=0.55, edgecolor="white")
    ax.set_ylabel("Weight (MT)", fontsize=9)
    ax.set_title("Structural Steel Tonnage by Member Group", fontsize=10)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    max_w = max(weights_mt)
    for b, w in zip(bars, weights_mt):
        ax.text(b.get_x() + b.get_width() / 2, w + max_w * 0.02,
                f"{w:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, max_w * 1.20)
    fig.tight_layout()
    path = os.path.join(_OUTDIR, fname)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path.replace("\\", "/")


def concrete_vs_rebar_chart(concrete_vol_m3, rebar_wt_mt, fname):
    """Twin-axis bar chart: Concrete Volume (m3) vs Reinforcement Steel (MT)."""
    fig, ax1 = plt.subplots(figsize=(5, 3.5))

    # Left axis — concrete volume
    ax1.bar(0, concrete_vol_m3, width=0.35, color=COLOR_CONC,
            label="Concrete Volume (m3)", edgecolor="white")
    ax1.set_ylabel("Concrete Volume (m3)", color=COLOR_CONC, fontsize=9)
    ax1.tick_params(axis="y", labelcolor=COLOR_CONC)
    ax1.set_ylim(0, concrete_vol_m3 * 1.35)
    ax1.text(0, concrete_vol_m3 * 1.05,
             f"{concrete_vol_m3:.2f} m3", ha="center", va="bottom",
             fontsize=8, color=COLOR_CONC)

    # Right axis — rebar weight
    ax2 = ax1.twinx()
    ax2.bar(0.4, rebar_wt_mt, width=0.35, color=COLOR_REBAR,
            label="Rebar Weight (MT)", edgecolor="white")
    ax2.set_ylabel("Reinforcement Steel (MT)", color=COLOR_REBAR, fontsize=9)
    ax2.tick_params(axis="y", labelcolor=COLOR_REBAR)
    ax2.set_ylim(0, rebar_wt_mt * 1.35)
    ax2.text(0.4, rebar_wt_mt * 1.05,
             f"{rebar_wt_mt:.2f} MT", ha="center", va="bottom",
             fontsize=8, color=COLOR_REBAR)

    ax1.set_title("Concrete Deck Slab: Volume vs Reinforcement Steel", fontsize=10)
    ax1.set_xticks([0, 0.4])
    ax1.set_xticklabels(["Concrete\n(m3)", "Rebar\n(MT)"], fontsize=9)
    fig.tight_layout()
    path = os.path.join(_OUTDIR, fname)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path.replace("\\", "/")


def build_material_charts_latex(input_dict):
    """Generate material quantity bar charts and return a LaTeX string with
    embedded figures, ready to be appended after Table 7.1 in Chapter 7.

    Parameters
    ----------
    input_dict : dict — same dict passed to ch7_quantities(), containing
                        BOQ keys from boq_generator.py.
    Returns
    -------
    str — LaTeX figure blocks (empty string when data is unavailable).
    """
    out = []

    # ── Chart 1: Structural Steel Tonnage ─────────────────────────────────────
    steel_items = [
        ("Girders",           _safe_float(input_dict.get("steel_girders_wt_total"))),
        ("Bracing\n(Top)",    _safe_float(input_dict.get("bracing_top_wt_total"))),
        ("Bracing\n(Bottom)", _safe_float(input_dict.get("bracing_bot_wt_total"))),
        ("Bracing\n(Diag.)",  _safe_float(input_dict.get("bracing_diag_wt_total"))),
    ]
    steel_valid = [(lbl, w) for lbl, w in steel_items if w is not None and w > 0]

    if steel_valid:
        try:
            labels, weights = zip(*steel_valid)
            path1 = steel_tonnage_chart(list(labels), list(weights),
                                        "material_steel_tonnage.png")
            out.append(
                "\\begin{figure}[H]\n\\centering\n"
                f"\\includegraphics[width=0.85\\textwidth]{{{path1}}}\n"
                "\\caption{Structural Steel Tonnage by Member Group (MT)}\n"
                "\\end{figure}\n"
            )
        except Exception:
            pass

    # ── Chart 2: Concrete Volume vs Rebar Weight ───────────────────────────────
    concrete_vol = _safe_float(input_dict.get("concrete_deck_vol_total"))
    rebar_wt     = _safe_float(input_dict.get("rebar_deck_wt_total"))

    if concrete_vol and concrete_vol > 0 and rebar_wt and rebar_wt > 0:
        try:
            path2 = concrete_vs_rebar_chart(concrete_vol, rebar_wt,
                                            "material_concrete_vs_rebar.png")
            out.append(
                "\\begin{figure}[H]\n\\centering\n"
                f"\\includegraphics[width=0.70\\textwidth]{{{path2}}}\n"
                "\\caption{Concrete Deck Slab: Volume (m\\textsuperscript{3})"
                " vs Reinforcement Steel Weight (MT)}\n"
                "\\end{figure}\n"
            )
        except Exception:
            pass

    return "\n".join(out)
