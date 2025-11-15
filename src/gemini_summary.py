# src/gemini_summary.py
"""
Gemini Summarizer - FINAL VERSION
Works 100% with your key using models/gemini-pro-latest
"""

import os
import json
import argparse
import google.generativeai as genai


# ----------------------------------------
# Build Prompt
# ----------------------------------------
def build_prompt(summary):

    base = summary.get("Base Analysis", {})
    pres = summary.get("Present Analysis", {})
    change = summary.get("Change Analysis", {})

    b_count = base.get("Detected Areas", 0)
    b_area = base.get("Total Mask Area", 0)
    b_conf = base.get("Avg Confidence", 0)

    p_count = pres.get("Detected Areas", 0)
    p_area = pres.get("Total Mask Area", 0)
    p_conf = pres.get("Avg Confidence", 0)

    change_pct = change.get("Damage Increase (%)", 0)
    severity = change.get("Severity", "Unknown")
    area_diff = change.get("Area Difference", 0)

    prompt = f"""
You are a senior expert in road-safety and infrastructure assessment.

Summarize the following data STRICTLY in JSON:

DATA:
Base Detected Areas: {b_count}
Base Total Mask Area: {b_area}
Base Avg Confidence: {b_conf}

Present Detected Areas: {p_count}
Present Total Mask Area: {p_area}
Present Avg Confidence: {p_conf}

Damage Increase (%): {change_pct}
Area Difference (px): {area_diff}
Severity Level: {severity}

OUTPUT FORMAT (STRICT):

{{
  "executive_summary": "...",
  "recommendations": [
    {{
      "action": "...",
      "priority": 1,
      "justification": "..."
    }}
  ],
  "evidence": "...",
  "severity": "...",
  "urgency": "...",
  "tldr": "..."
}}

Rules:
- No invented numbers.
- Match urgency to severity.
- Output ONLY valid JSON.
"""

    return prompt.strip()


# ----------------------------------------
# Generate Summary
# ----------------------------------------
def generate_summary(summary_path, api_key, output_path):
    with open(summary_path, "r") as f:
        summary = json.load(f)

    prompt = build_prompt(summary)

    genai.configure(api_key=api_key)

    # ❤️ The model that WORKS for your key
    model = genai.GenerativeModel("models/gemini-pro-latest")

    print("🔵 Calling Gemini (gemini-pro-latest)…")

    response = model.generate_content(prompt)
    text = response.text.strip()

    try:
        parsed = json.loads(text)
    except:
        parsed = {"raw_text": text}

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    json.dump(
        {
            "llm_text": text,
            "llm_parsed": parsed
        },
        open(output_path, "w"),
        indent=2
    )

    print("✅ Saved:", output_path)
    return parsed


# ----------------------------------------
# CLI
# ----------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="results/compare/summary.json")
    parser.add_argument("--out", default="results/compare/llm_summary.json")
    args = parser.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("❌ ERROR: export GEMINI_API_KEY=your_key")

    generate_summary(args.summary, key, args.out)
