import streamlit as st
import os, json
from PIL import Image

# ------------------------------------
# Page Config
# ------------------------------------
st.set_page_config(
    page_title="AI Road Safety Dashboard",
    layout="wide",
    page_icon="🛣️"
)

# ------------------------------------
# Helper
# ------------------------------------
def load_json(path):
    try:
        return json.load(open(path))
    except:
        return None

# ------------------------------------
# Paths
# ------------------------------------
FINAL_PDF = "results/final_report.pdf"
MULTI_PDF = "results/compare/multi_report.pdf"
MULTI_SUMMARY = "results/compare/multi_summary.json"
LLM_SUMMARY = "results/compare/llm_summary.json"
CHARTS_DIR = "results/charts"

# ------------------------------------
# Sidebar Navigation
# ------------------------------------
st.sidebar.title("📌 Navigation")

page = st.sidebar.radio(
    "Go to section:",
    [
        "🏠 Dashboard Home",
        "📊 Aggregated Summary",
        "🧠 AI Summary",
        "📈 Visual Charts",
        "📄 Reports",
    ]
)

st.sidebar.info("Built using your AI Road Analysis Pipeline 🚀")

# ------------------------------------
# HOME PAGE
# ------------------------------------
if page == "🏠 Dashboard Home":
    st.title("🛣️ AI Road Infrastructure Comparative Dashboard")
    st.write("### Automated detection • Smart comparison • AI Summary • Final Reports")

    colA, colB, colC = st.columns(3)

    # KPIs (if summary exists)
    data = load_json(MULTI_SUMMARY)

    if data:
        pavement_change = round(
            (data['pavement']["avg_present_area"] - data['pavement']["avg_base_area"]) / 
            max(1, data['pavement']["avg_base_area"]) * 100, 2
        )
        lane_change = data['lane']["avg_present_lines"] - data['lane']["avg_base_lines"]
        sign_diff = data['signs']["present_sign_count"] - data['signs']["base_sign_count"]

        colA.metric("Pavement Condition Change (%)", f"{pavement_change}%")
        colB.metric("Lane Markings Change", f"{lane_change}")
        colC.metric("Sign Difference", f"{sign_diff}")

    else:
        st.warning("Run pipeline to generate results first.")

    # Show sample chart preview if exists
    if os.path.exists(CHARTS_DIR):
        images = [f for f in os.listdir(CHARTS_DIR) if f.endswith(".png")]
        if images:
            st.write("### Recent Comparison Visualization")
            preview = os.path.join(CHARTS_DIR, images[0])
            st.image(preview, caption="Comparison Preview", use_column_width=True)
        else:
            st.info("Charts will appear here once generated.")
    else:
        st.info("Charts directory not found.")


# ------------------------------------
# AGGREGATED SUMMARY
# ------------------------------------
elif page == "📊 Aggregated Summary":
    st.title("📊 Aggregated Comparison Summary")

    data = load_json(MULTI_SUMMARY)

    if data:
        st.success("Summary Loaded")
        st.json(data)

        st.write("### Key Takeaways")
        st.markdown("""
        - **Pavement area** shows road surface degradation or improvement  
        - **Lane markings** measure visibility and maintenance  
        - **Shoulder erosion** indicates safety risk  
        - **Signs count** helps track missing/new road signs  
        """)

    else:
        st.error("multi_summary.json not found.")


# ------------------------------------
# AI SUMMARY PAGE
# ------------------------------------
elif page == "🧠 AI Summary":
    st.title("🧠 LLM-Generated Summary & Recommendations")

    ai = load_json(LLM_SUMMARY)

    if ai:
        parsed_text = ai.get("llm_text") or ai.get("llm_parsed") or ""
        st.json(ai)

        st.write("### 💡 Executive Summary")
        st.info(parsed_text)

    else:
        st.error("llm_summary.json not found.")


# ------------------------------------
# CHARTS PAGE
# ------------------------------------
elif page == "📈 Visual Charts":
    st.title("📈 Visual Comparison Charts")

    if os.path.exists(CHARTS_DIR):
        images = [f for f in os.listdir(CHARTS_DIR) if f.endswith(".png")]

        if images:
            cols = st.columns(2)

            for i, img in enumerate(images):
                with cols[i % 2]:
                    st.image(os.path.join(CHARTS_DIR, img), caption=img)
        else:
            st.warning("Charts folder is empty.")
    else:
        st.error("Charts directory missing.")


# ------------------------------------
# REPORTS PAGE
# ------------------------------------
elif page == "📄 Reports":
    st.title("📄 Downloadable Reports")

    col1, col2 = st.columns(2)

    with col1:
        if os.path.exists(FINAL_PDF):
            st.download_button(
                "⬇️ Download FINAL Report", 
                open(FINAL_PDF, "rb"), 
                file_name="final_report.pdf"
            )
            st.write("#### Preview:")
            st.pdf(FINAL_PDF)
        else:
            st.error("final_report.pdf not found.")

    with col2:
        if os.path.exists(MULTI_PDF):
            st.download_button(
                "⬇️ Download YOLO Multi Report", 
                open(MULTI_PDF, "rb"), 
                file_name="multi_report.pdf"
            )
        else:
            st.error("multi_report.pdf not found.")
