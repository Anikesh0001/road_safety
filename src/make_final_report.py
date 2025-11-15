# src/make_final_report.py
"""
FINAL HACKATHON PDF GENERATOR (Stable + Accurate)
- Uses ONLY the correct older logic
- Adds clean comparison charts
- Keeps AI summary formatting perfect
- No risky aggregation, no wrong computations
"""

import json
import os
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from PyPDF2 import PdfReader, PdfWriter


AI_SUMMARY_PATH = "results/compare/llm_summary.json"
MULTI_SUMMARY_PATH = "results/compare/multi_summary.json"
YOLO_PDF_PATH = "results/compare/multi_report.pdf"
METADATA_PATH = "results/compare/metadata.json"
OUTPUT_FINAL_PDF = "results/final_report.pdf"


# ------------------------------------------------------------
# WORD WRAPPING
# ------------------------------------------------------------
def draw_wrapped_text(c, text, x, y, max_width, line_height=14):
    words = text.split()
    line = ""

    for word in words:
        test = line + " " + word if line else word
        width = c.stringWidth(test, "Helvetica", 12)

        if width <= max_width:
            line = test
        else:
            # new page if needed
            if y < 2 * cm:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 27 * cm
            c.drawString(x, y, line)
            y -= line_height
            line = word

    if line:
        if y < 2 * cm:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 27 * cm
        c.drawString(x, y, line)
        y -= line_height

    return y


# ------------------------------------------------------------
# CLEAN AI SUMMARY JSON
# ------------------------------------------------------------
def clean_llm_json(raw):
    if not raw:
        return {}

    text = raw.strip()

    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    try:
        return json.loads(text)
    except:
        return {"raw_text": text}


# ------------------------------------------------------------
# AI PAGE (MAIN PAGE)
# ------------------------------------------------------------
def draw_ai_page(c, data):
    y = 27 * cm
    x = 2 * cm
    max_w = 17 * cm

    c.setFont("Helvetica-Bold", 22)
    c.drawString(x, y, "AI-Generated Road Safety Summary")
    y -= 1.3 * cm

    # --------------------- METADATA ----------------------------
    if os.path.exists(METADATA_PATH):
        try:
            meta = json.load(open(METADATA_PATH))
        except:
            meta = {}

        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "Road Metadata:")
        y -= 0.7 * cm

        c.setFont("Helvetica", 12)
        y = draw_wrapped_text(c, f"Start GPS: {meta.get('start_gps','N/A')}", x, y, max_w)
        y = draw_wrapped_text(c, f"End GPS: {meta.get('end_gps','N/A')}", x, y, max_w)
        y = draw_wrapped_text(c, f"Date: {meta.get('date','N/A')}", x, y, max_w)
        y = draw_wrapped_text(c, f"Road Type: {meta.get('road_type','N/A')}", x, y, max_w)
        y -= 1 * cm

    # --------------------- AI SUMMARY SECTIONS ------------------
    def sec(title, val):
        nonlocal y
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, f"{title}:")
        y -= 0.6 * cm
        c.setFont("Helvetica", 12)
        y = draw_wrapped_text(c, val, x, y, max_w)
        y -= 0.3 * cm

    sec("Executive Summary", data.get("executive_summary", "N/A"))
    sec("Severity Level", data.get("severity", "N/A"))
    sec("Urgency", data.get("urgency", "N/A"))
    sec("Evidence", data.get("evidence", "N/A"))
    sec("TL;DR", data.get("tldr", "N/A"))

    # --------------------- RECOMMENDATIONS ------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Recommendations:")
    y -= 0.6 * cm

    recs = data.get("recommendations", [])
    c.setFont("Helvetica", 12)

    if recs:
        for r in recs:
            y = draw_wrapped_text(c, f"• {r.get('action','')}", x, y, max_w)
            y = draw_wrapped_text(c, f"Priority: {r.get('priority','')}", x+1*cm, y, max_w)
            y = draw_wrapped_text(c, f"Justification: {r.get('justification','')}", x+1*cm, y, max_w)
            y -= 0.3 * cm
    else:
        y = draw_wrapped_text(c, "No recommendations provided.", x, y, max_w)


# ------------------------------------------------------------
# GENERATE CHARTS
# ------------------------------------------------------------
def make_charts(data):
    os.makedirs("results/charts", exist_ok=True)

    factors = {
        "Pavement Area": (
            data["pavement"]["avg_base_area"],
            data["pavement"]["avg_present_area"],
        ),
        "Lane Line Count": (
            data["lane"]["avg_base_lines"],
            data["lane"]["avg_present_lines"],
        ),
        "Lane Fade Score": (
            data["lane"]["avg_base_fade"],
            data["lane"]["avg_present_fade"],
        ),
        "Shoulder Erosion": (
            data["shoulder"]["avg_base_erosion"],
            data["shoulder"]["avg_present_erosion"],
        ),
        "Road Signs Count": (
            data["signs"]["base_sign_count"],
            data["signs"]["present_sign_count"],
        ),
    }

    chart_paths = []

    for title, (base, present) in factors.items():
        plt.figure(figsize=(6, 4))
        plt.bar(["Base", "Present"], [base, present], color=["#2c7bb6", "#527de1"])
        plt.title(title)
        plt.tight_layout()

        path = f"results/charts/{title.replace(' ', '_')}.png"
        plt.savefig(path)
        plt.close()

        chart_paths.append((title, path))

    return chart_paths


# ------------------------------------------------------------
# CHART PAGES
# ------------------------------------------------------------
def draw_chart_pages(c, chart_paths):
    for title, img_path in chart_paths:
        c.showPage()
        c.setFont("Helvetica-Bold", 18)
        c.drawString(2 * cm, 27 * cm, title)
        c.drawImage(img_path, 2 * cm, 10 * cm, width=16 * cm, preserveAspectRatio=True)


# ------------------------------------------------------------
# MERGE PDFS
# ------------------------------------------------------------
def merge_pdfs(ai_pdf, yolo_pdf, out):
    writer = PdfWriter()

    for p in PdfReader(ai_pdf).pages:
        writer.add_page(p)

    if os.path.exists(yolo_pdf):
        for p in PdfReader(yolo_pdf).pages:
            writer.add_page(p)
    else:
        print("⚠ YOLO report not found — skipping.")

    with open(out, "wb") as f:
        writer.write(f)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def generate_final_report():
    # Load AI summary
    with open(AI_SUMMARY_PATH) as f:
        raw_ai = json.load(f)

    raw = raw_ai.get("llm_text", "") or raw_ai.get("llm_parsed", {}).get("raw_text", "")
    parsed = clean_llm_json(raw)

    # Load multi-summary
    with open(MULTI_SUMMARY_PATH) as f:
        multi = json.load(f)

    # Generate charts
    charts = make_charts(multi)

    # Build PDF
    ai_pdf = "results/compare/_ai_summary_page.pdf"
    os.makedirs("results/compare", exist_ok=True)

    c = canvas.Canvas(ai_pdf, pagesize=A4)
    draw_ai_page(c, parsed)
    draw_chart_pages(c, charts)
    c.save()

    merge_pdfs(ai_pdf, YOLO_PDF_PATH, OUTPUT_FINAL_PDF)

    print("\n🎉 FINAL REPORT READY!")
    print("➡", OUTPUT_FINAL_PDF)


if __name__ == "__main__":
    generate_final_report()
