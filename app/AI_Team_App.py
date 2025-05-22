import streamlit as st
import os
from datetime import datetime
import logging
from execute_sowFile_byTeam import (
    load_team_data,
    extract_text_from_docx,
    SOWAnalyzer,
    execute_team,
    setup_logging
)

# CSS Styling
st.set_page_config(page_title="🤖 AI Team Manager", layout="wide")
st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', sans-serif;
    }
    .log-box {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: monospace;
        padding: 1rem;
        border-radius: 6px;
        max-height: 400px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    .activity-entry {
        background-color: #f0f2f5;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 5px solid #007bff;
        border-radius: 6px;
    }
    .activity-entry .header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        color: #333;
    }
    .activity-entry .role {
        font-weight: bold;
        color: #007bff;
    }
    .activity-entry .timestamp {
        color: #888;
        font-size: 0.8rem;
    }
    .activity-entry .message {
        color: #222;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_state():
    defaults = {
        'sow_file': None,
        'tasks': None,
        'team_members': None,
        'execution_started': False,
        'execution_completed': False,
        'activity_log': [],
        'logs': [],
        'team_status': {},
        'show_logs': False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def upload_file():
    st.subheader("📄 Upload SOW Document")
    file = st.file_uploader("Choose a DOCX file", type=["docx"])
    if file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
        os.makedirs(docs_dir, exist_ok=True)
        path = os.path.join(docs_dir, f"sow_{timestamp}.docx")
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        st.session_state.sow_file = path
        st.success("File uploaded successfully")
        st.rerun() #refresh Streamlit  

def analyze():
    if st.session_state.sow_file:
        with st.spinner("Analyzing SOW and generating tasks..."):
            try:
                members = load_team_data()
                st.session_state.team_members = members
                text = extract_text_from_docx(st.session_state.sow_file)
                analyzer = SOWAnalyzer(text, members)
                tasks = analyzer.analyze_and_generate_tasks()
                if not any(tasks.values()):
                    st.error("No tasks generated. Check your OpenAI API key or SOW content.")
                    return
                st.session_state.tasks = tasks
                st.success("✅ Analysis complete")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def get_streamlit_log_handler(log_placeholder):
    class StreamlitHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            if 'logs' not in st.session_state:
                st.session_state.logs = []
            st.session_state.logs.append(msg)
            st.session_state.logs = st.session_state.logs[-200:]

            log_text = "\n".join(st.session_state.logs[-50:])
            log_placeholder.code(log_text, language="text")
    return StreamlitHandler()

def execute():
    st.markdown("### 🔄 Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛑 Stop Activity Stream"):
            st.session_state.execution_started = False
            st.session_state.execution_completed = False
            st.rerun()
    with col2:
        if st.button("🔁 Start Over"):
            for key in [
                'sow_file', 'tasks', 'team_members',
                'execution_started', 'execution_completed',
                'activity_log', 'logs', 'team_status', 'show_logs'
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    if st.session_state.execution_started and not st.session_state.execution_completed:
        st.subheader("⚙️ Live Execution Monitor")
        log_placeholder = st.empty()
        st.session_state.logs = []

        handler = get_streamlit_log_handler(log_placeholder)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        with st.spinner("Running agents..."):
            try:
                result = execute_team(st.session_state.team_members, st.session_state.tasks)
                st.session_state.execution_completed = True
                st.session_state.execution_result = result["execution_result"]
                st.success("🎉 Execution completed!")
            except Exception as e:
                st.error(f"Execution error: {str(e)}")
            finally:
                logger.removeHandler(handler)

    if st.session_state.execution_completed and st.session_state.get("logs"):
        st.markdown("### 📜 Final Logs")
        st.code("\n".join(st.session_state.logs[-100:]), language="text")

    if st.session_state.execution_completed:
        st.markdown("### 🧠 Final Result")
        st.markdown(st.session_state.execution_result)

def main():
    st.title("🤖 AI Team Manager")
    initialize_state()

    # הצגת משימות קבועה בראש המסך
    if st.session_state.tasks:
        st.markdown("### 📋 Task Overview")
        for role, tasks in st.session_state.tasks.items():
            with st.expander(f"{role}", expanded=False):
                for i, task in enumerate(tasks, 1):
                    st.markdown(f"{i}. {task}")

    if not st.session_state.sow_file:
        upload_file()
    elif not st.session_state.tasks:
        analyze()
    elif not st.session_state.execution_started:
        st.button("🚀 Start Execution", on_click=lambda: st.session_state.update({"execution_started": True}))
    else:
        execute()

if __name__ == "__main__":
    main()
