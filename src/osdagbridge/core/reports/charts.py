"""Matplotlib chart helpers for the design report (UR charts, material charts)."""
import os
import re
import tempfile

import matplotlib
matplotlib.use("Agg")          # no GUI window; safe inside the Qt app
import matplotlib.pyplot as plt

# TODO (Task 6): move these two colors into your styles.py and import them
COLOR_PASS = "#91B014"
COLOR_FAIL = "#D62728"

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