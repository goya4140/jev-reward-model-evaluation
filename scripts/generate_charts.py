"""Generate dependency-free SVG charts for the GitHub report."""

from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

INK = "#172033"
MUTED = "#667085"
GRID = "#E4E7EC"
JEV = "#2563EB"
BASE = "#D0D5DD"
GOLD = "#D69E2E"
PALE = "#F8FAFC"


def esc(value: object) -> str:
    return html.escape(str(value))


def text(x: float, y: float, value: object, size: int = 14, weight: int = 400,
         anchor: str = "start", fill: str = INK) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter,Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="{fill}">{esc(value)}</text>'
    )


def svg_doc(width: int, height: int, body: list[str], title: str) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        '<desc id="desc">Source-backed statistical visualization for the Jev reward-model evaluation.</desc>',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        *body,
        '</svg>',
    ])


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def headline_comparison() -> None:
    results = {row["benchmark"]: row for row in read_csv("benchmark_summary.csv")}
    refs = {
        row["benchmark"]: row for row in read_csv("baselines.csv")
        if row["chart_reference"].lower() == "true"
    }
    order = list(results)
    width, height = 1200, 720
    left, right, top = 355, 80, 124
    plot_w = width - left - right
    row_h = 66
    body = [
        text(52, 48, "Jev is close to leading baselines on preference ranking", 25, 700),
        text(52, 78, "Primary score within each benchmark; reference baselines use the closest public model setting available", 14, 400, fill=MUTED),
    ]
    for tick in range(50, 101, 10):
        x = left + (tick - 50) / 50 * plot_w
        body.append(f'<line x1="{x:.1f}" y1="{top-18}" x2="{x:.1f}" y2="{height-58}" stroke="{GRID}" stroke-width="1"/>')
        body.append(text(x, top - 28, tick, 12, 500, "middle", MUTED))
    body.append(text(width - 54, top - 28, "score (%)", 12, 500, "end", MUTED))
    for idx, name in enumerate(order):
        y = top + idx * row_h
        jev = float(results[name]["score_pct"])
        ref = float(refs[name]["score_pct"])
        xj = left + (jev - 50) / 50 * plot_w
        xb = left + (ref - 50) / 50 * plot_w
        delta = jev - ref
        short = name.replace(" · ", "\n")
        pieces = short.split("\n", 1)
        body.append(text(left - 22, y + 4, pieces[0], 14, 650, "end"))
        if len(pieces) > 1:
            body.append(text(left - 22, y + 23, pieces[1], 11, 400, "end", MUTED))
        body.append(f'<line x1="{min(xj, xb):.1f}" y1="{y:.1f}" x2="{max(xj, xb):.1f}" y2="{y:.1f}" stroke="#98A2B3" stroke-width="3"/>')
        body.append(f'<circle cx="{xb:.1f}" cy="{y:.1f}" r="8" fill="white" stroke="#667085" stroke-width="3"/>')
        body.append(f'<circle cx="{xj:.1f}" cy="{y:.1f}" r="9" fill="{JEV}"/>')
        body.append(text(xj, y - 15, f"{jev:.1f}", 12, 700, "middle", JEV))
        body.append(text(xb, y + 25, f"{ref:.1f}", 11, 600, "middle", MUTED))
        body.append(text(width - 42, y + 4, f"{delta:+.1f} pp", 13, 700, "end", JEV if delta >= 0 else MUTED))
    body += [
        f'<circle cx="52" cy="{height-31}" r="7" fill="{JEV}"/>',
        text(66, height - 26, "Jev 1.13", 12, 600),
        f'<circle cx="155" cy="{height-31}" r="6" fill="white" stroke="#667085" stroke-width="2"/>',
        text(168, height - 26, "selected public reference", 12, 500, fill=MUTED),
        text(width - 42, height - 26, "Delta = Jev − reference", 11, 400, "end", MUTED),
    ]
    (ASSETS / "headline_comparison.svg").write_text(svg_doc(width, height, body, "Jev headline benchmark comparison"), encoding="utf-8")


def capability_heatmap() -> None:
    rows = read_csv("capability_breakdown.csv")
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row["benchmark"], []).append(row)
    width, height = 1200, 560
    body = [
        text(52, 48, "Safety leads; precise instruction following is the weakest dimension", 25, 700),
        text(52, 78, "Each cell uses the benchmark's own official submetric; darker blue indicates a higher score", 14, 400, fill=MUTED),
    ]
    y = 122
    label_w, cell_w, cell_h = 235, 142, 58
    for group, items in groups.items():
        body.append(text(52, y + 34, group, 14, 650))
        for j, row in enumerate(items):
            score = float(row["score_pct"])
            x = 52 + label_w + j * cell_w
            intensity = max(0.0, min(1.0, (score - 45) / 55))
            r = round(235 - 175 * intensity)
            g = round(242 - 118 * intensity)
            b = round(255 - 25 * intensity)
            fill = f"rgb({r},{g},{b})"
            fg = "white" if score >= 72 else INK
            body.append(f'<rect x="{x}" y="{y}" width="{cell_w-8}" height="{cell_h}" rx="8" fill="{fill}"/>')
            body.append(text(x + (cell_w - 8) / 2, y + 23, row["dimension"], 11, 600, "middle", fg))
            body.append(text(x + (cell_w - 8) / 2, y + 45, f"{score:.1f}%", 15, 750, "middle", fg))
        y += 78
    body.append(text(52, height - 24, "Note: values are comparable within a row, not across benchmark families with different tasks and scoring rules.", 11, 400, fill=MUTED))
    (ASSETS / "capability_heatmap.svg").write_text(svg_doc(width, height, body, "Jev capability breakdown"), encoding="utf-8")


def operating_profile() -> None:
    rows = read_csv("benchmark_summary.csv")
    width, height = 1200, 650
    body = [
        text(52, 48, "Eight tracks: 40.9k evaluations for an estimated $3.19 input cost", 25, 700),
        text(52, 78, "Cost estimate uses $0.042 per million input tokens; latency is observed request latency", 14, 400, fill=MUTED),
    ]
    panels = [
        ("Samples", "samples", 17000, "{:.0f}"),
        ("Estimated input cost (USD)", "estimated_input_cost_usd", 1.15, "${:.2f}"),
        ("p50 latency (ms)", "p50_latency_ms", 800, "{:.0f}"),
    ]
    panel_w = 352
    for p, (title, key, maximum, fmt) in enumerate(panels):
        x0 = 52 + p * 382
        body.append(text(x0, 122, title, 15, 700))
        for i, row in enumerate(rows):
            y = 153 + i * 56
            value = float(row[key])
            bar_w = value / maximum * (panel_w - 128)
            label = row["benchmark"].split(" · ")[0]
            if label == "PPE": label = "PPE"
            body.append(text(x0, y + 14, label[:18], 10, 500, fill=MUTED))
            body.append(f'<rect x="{x0+104}" y="{y}" width="{panel_w-128}" height="18" rx="4" fill="{GRID}"/>')
            body.append(f'<rect x="{x0+104}" y="{y}" width="{bar_w:.1f}" height="18" rx="4" fill="{JEV if p != 1 else GOLD}"/>')
            body.append(text(x0 + panel_w, y + 14, fmt.format(value), 10, 650, "end"))
    body.append(text(52, height - 26, "Input tokens: 76.0M · API errors across completed tracks: 0 · model version returned by API: jev-1.13.0", 12, 500, fill=MUTED))
    (ASSETS / "operating_profile.svg").write_text(svg_doc(width, height, body, "Jev evaluation operating profile"), encoding="utf-8")


def ppe_comparison() -> None:
    rows = read_csv("ppe_comparison.csv")
    metrics = [
        ("Accuracy", "accuracy"), ("R.W. Pearson", "row_wise_pearson"),
        ("Separability", "separability"), ("Confidence agreement", "confidence_agreement"),
        ("Kendall tau", "kendall_tau"), ("Spearman", "spearman"),
    ]
    width, height = 1200, 560
    left, top, plot_w = 255, 132, 850
    body = [
        text(52, 48, "PPE: Jev matches Athene-RM-8B accuracy and ranks models better", 25, 700),
        text(52, 78, "Human Preference V1; all metrics are higher-is-better except Brier score", 14, 400, fill=MUTED),
    ]
    colors = [JEV, "#111827", "#D69E2E", "#98A2B3"]
    for i, (label, key) in enumerate(metrics):
        y = top + i * 58
        body.append(text(left - 18, y + 7, label, 13, 600, "end"))
        body.append(f'<line x1="{left}" y1="{y}" x2="{left+plot_w}" y2="{y}" stroke="{GRID}" stroke-width="8" stroke-linecap="round"/>')
        for j, row in enumerate(rows):
            value = float(row[key])
            x = left + (value - 55) / 45 * plot_w
            body.append(f'<circle cx="{x:.1f}" cy="{y + (j-1.5)*7:.1f}" r="6" fill="{colors[j]}"/>')
            if j == 0:
                body.append(text(x - 8, y - 14, f"{value:.1f}", 11, 700, "middle", JEV))
    legend_y = height - 82
    for j, row in enumerate(rows):
        x = 52 + j * 270
        body.append(f'<circle cx="{x}" cy="{legend_y}" r="7" fill="{colors[j]}"/>')
        body.append(text(x + 14, legend_y + 5, row["model"], 12, 600 if j == 0 else 500))
    briers = " · ".join(f'{row["model"]}: {float(row["brier"]):.2f}' for row in rows)
    body.append(text(52, height - 28, f"Brier score (lower is better) — {briers}", 11, 400, fill=MUTED))
    (ASSETS / "ppe_comparison.svg").write_text(svg_doc(width, height, body, "PPE multi-metric comparison"), encoding="utf-8")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    headline_comparison()
    capability_heatmap()
    operating_profile()
    ppe_comparison()


if __name__ == "__main__":
    main()
