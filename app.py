import streamlit as st
import time
import matplotlib.pyplot as plt
import pandas as pd
import os
import json

from core.monitor import get_all_stats
from core.analyzer import analyze
from core.agent import decide_action, execute_action, decide_action_ai
from core.actions import get_top_processes

# --- Page Config ---
st.set_page_config(
    page_title="HealthAgent AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sleek Professional Styling ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Custom Card Style */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        border: 1px solid #4CAF50;
        transform: translateY(-5px);
    }

    /* Status Indicators */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    /* Title Styling */
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 42px;
        margin-bottom: 0px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2091/2091665.png", width=80)
    st.markdown("### Agent Settings")
    auto_refresh = st.toggle("🔄 Real-time Monitoring", value=True)
    st.divider()
    st.info("The AI Agent is actively monitoring system interrupts and memory leaks.")
    if st.button("Force System Clean"):
        execute_action("clear_temp")
        st.toast("Temporary files purged!")

# --- Header Section ---
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.markdown('<p class="main-title">HealthAgent AI</p>', unsafe_allow_html=True)
    st.caption("Autonomous System Optimization & Self-Healing Terminal")

# --- Data Acquisition ---
stats = get_all_stats()
issues = analyze(stats)
action, reason = decide_action_ai(stats, issues)

if action not in ["kill_process", "clear_temp", "do_nothing"]:
    action, reason = decide_action(issues)

# --- Metric Row ---
st.write("---")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

def render_metric(col, label, value, suffix="%"):
    color = "#4CAF50" if value < 60 else "#FFA000" if value < 85 else "#FF5252"
    with col:
        st.markdown(f"""
            <div class="metric-card">
                <p style="color: gray; margin-bottom: 0;">{label}</p>
                <h2 style="color: {color}; margin-top: 0;">{value}{suffix}</h2>
            </div>
        """, unsafe_allow_html=True)

render_metric(m_col1, "CPU LOAD", stats['cpu'])
render_metric(m_col2, "MEMORY USAGE", stats['ram'])
render_metric(m_col3, "DISK STORAGE", stats['disk'])

with m_col4:
    if stats["battery"]:
        bat = stats["battery"]
        icon = "⚡" if bat["plugged"] else "🔋"
        render_metric(m_col4, f"{icon} BATTERY", bat['percent'])
    else:
        render_metric(m_col4, "SYSTEM", "AC", suffix=" PWR")

# --- Dashboard Body ---
layout_left, layout_right = st.columns([2, 1])

with layout_left:
    st.subheader("📈 Performance Telemetry")
    if "cpu_history" not in st.session_state:
        st.session_state.cpu_history = []
    
    st.session_state.cpu_history.append(stats["cpu"])
    st.session_state.cpu_history = st.session_state.cpu_history[-30:]

    # Using native streamlit line chart for a cleaner look
    chart_data = pd.DataFrame(st.session_state.cpu_history, columns=["CPU %"])
    st.area_chart(chart_data, color="#4CAF50", use_container_width=True)

    with st.expander("🔍 Detailed Process Inspector", expanded=True):
        processes = get_top_processes()
        if processes:
            df_proc = pd.DataFrame(processes, columns=["Process Name", "CPU %"])
            st.dataframe(df_proc, use_container_width=True, hide_index=True)

with layout_right:
    st.subheader("🤖 Agent Intelligence")
    
    # Status of the AI Agent
    with st.status("🧠 AI Reasoning...", expanded=True) as status:
        if "Decided by AI" in reason:
            source_label = "AI"
        elif "System is healthy" in reason:
            source_label = "System"
        else:
            source_label = "Fallback/Policy"
        model_used = "N/A"
        if "model=" in reason:
            model_used = reason.split("model=", 1)[1].split("|")[0].strip()
        st.write(f"**Analysis:** {len(issues)} anomalies detected.")
        st.write(f"**Action:** `{action.replace('_', ' ').title()}`")
        st.write(f"**Decision Source:** {source_label}")
        st.write(f"**Model:** {model_used}")
        st.write(f"**Logic:** {reason}")
        
        if action != "do_nothing":
            result = execute_action(action)
            status.update(label=f"Action Executed: {action}", state="complete", expanded=False)
            st.toast(f"Agent Action: {result}")
        else:
            status.update(label="System Optimized", state="complete", expanded=False)

    # Issues List
    st.markdown("### ⚠️ Logs")
    if issues:
        for issue in issues:
            st.error(f"**Anomaly:** {issue['message']}")
    else:
        st.success("Pulse Check: Nominal")

    with st.expander("🧾 Decision Trace", expanded=False):
        log_path = "logs/agent_decisions.jsonl"
        if os.path.exists(log_path):
            rows = []
            with open(log_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            if rows:
                recent = rows[-20:]
                df_logs = pd.DataFrame(recent)
                preferred_cols = [
                    "timestamp",
                    "source",
                    "final_action",
                    "severity",
                    "confidence",
                    "fallback_used",
                    "reason",
                ]
                visible_cols = [col for col in preferred_cols if col in df_logs.columns]
                st.dataframe(df_logs[visible_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No decision entries yet.")
        else:
            st.info("Decision log file not found yet.")

# --- Refresh Logic ---
if auto_refresh:
    time.sleep(300)
    st.rerun()