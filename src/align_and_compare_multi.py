# src/align_and_compare_multi.py

"""
Multi-Class Comparative Analysis
--------------------------------
Compares:
 - Pavement (mask area / crack severity)
 - Lane markings (line count / faded score)
 - Road signs (count)
 - Shoulder condition (erosion score / presence)
 - VRU elements (optional)
Outputs:
  results/compare/multi_summary.json
  results/compare/multi_report.pdf
"""

import json
import os
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def compute_average(values):
    return sum(values) / len(values) if values else 0

def compare_pavement(base, present):
    base_areas = [v["pavement"].get("total_mask_area", 0) for v in base.values()]
    present_areas = [v["pavement"].get("total_mask_area", 0) for v in present.values()]

    avg_base = compute_average(base_areas)
    avg_present = compute_average(present_areas)

    change = avg_present - avg_base
    percent = (change / avg_base * 100) if avg_base > 1 else 0

    verdict = "Worsened" if change > 0 else "Improved"

    return {
        "avg_base_area": int(avg_base),
        "avg_present_area": int(avg_present),
        "change_pixels": int(change),
        "percent_change": round(percent, 2),
        "verdict": verdict
    }

def compare_lane_markings(base, present):
    base_lines = [v["lane"].get("line_count", 0) for v in base.values()]
    present_lines = [v["lane"].get("line_count", 0) for v in present.values()]

    base_faded = [v["lane"].get("faded_score", 0) for v in base.values()]
    present_faded = [v["lane"].get("faded_score", 0) for v in present.values()]

    avg_line_change = compute_average(present_lines) - compute_average(base_lines)
    avg_fade_change = compute_average(present_faded) - compute_average(base_faded)

    verdict = "Improved"
    if avg_fade_change > 0.05:
        verdict = "Worsened"

    return {
        "avg_base_lines": round(compute_average(base_lines), 2),
        "avg_present_lines": round(compute_average(present_lines), 2),
        "line_change": round(avg_line_change, 2),
        "avg_base_fade": round(compute_average(base_faded), 2),
        "avg_present_fade": round(compute_average(present_faded), 2),
        "fade_change": round(avg_fade_change, 3),
        "verdict": verdict
    }

def compare_signs(base, present):
    def count_signs(d):
        count = 0
        for v in d.values():
            objs = v.get("objects", [])
            for o in objs:
                label = o["label"].lower()
                if "sign" in label:
                    count += 1
        return count

    base_count = count_signs(base)
    present_count = count_signs(present)

    verdict = "Improved" if present_count >= base_count else "Worsened"

    return {
        "base_sign_count": base_count,
        "present_sign_count": present_count,
        "difference": present_count - base_count,
        "verdict": verdict
    }

def compare_shoulder(base, present):
    base_erosion = [v["shoulder"].get("erosion_score", 0) for v in base.values()]
    present_erosion = [v["shoulder"].get("erosion_score", 0) for v in present.values()]

    avg_base = compute_average(base_erosion)
    avg_present = compute_average(present_erosion)

    change = avg_present - avg_base
    verdict = "Worsened" if change > 0 else "Improved"

    return {
        "avg_base_erosion": round(avg_base, 3),
        "avg_present_erosion": round(avg_present, 3),
        "change": round(change, 3),
        "verdict": verdict
    }

# --------------------------------------------------------------------
# PDF Generator
# --------------------------------------------------------------------
def generate_pdf(summary, out_pdf):
    c = canvas.Canvas(out_pdf, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, 800, "Road Infrastructure Comparison Report")
    c.setFont("Helvetica", 12)

    y = 760

    def add_section(title, data_dict):
        nonlocal y
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, title)
        y -= 20
        c.setFont("Helvetica", 12)
        for k, v in data_dict.items():
            c.drawString(60, y, f"{k}: {v}")
            y -= 15
        y -= 10

    add_section("Pavement Condition", summary["pavement"])
    add_section("Lane Markings", summary["lane"])
    add_section("Road Signs", summary["signs"])
    add_section("Shoulder Condition", summary["shoulder"])

    c.save()
    print(f"📄 PDF saved: {out_pdf}")

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--present", required=True)
    parser.add_argument("--out", default="results/compare/multi_summary.json")
    parser.add_argument("--pdf", default="results/compare/multi_report.pdf")
    args = parser.parse_args()

    ensure_dir(os.path.dirname(args.out))

    base = load_json(args.base)
    present = load_json(args.present)

    summary = {
        "pavement": compare_pavement(base, present),
        "lane": compare_lane_markings(base, present),
        "signs": compare_signs(base, present),
        "shoulder": compare_shoulder(base, present)
    }

    json.dump(summary, open(args.out, "w"), indent=2)
    print("Saved summary:", args.out)

    generate_pdf(summary, args.pdf)


if __name__ == "__main__":
    main()
