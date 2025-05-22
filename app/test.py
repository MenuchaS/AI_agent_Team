import streamlit as st
import os
from execute_sowFile_byTeam import (
    load_team_data,
    extract_text_from_docx,
    SOWAnalyzer,
    execute_team,
    setup_logging
)
import json
from datetime import datetime
import time
import logging

# Page configuration
st.set_page_config(
    page_title="AI Team Manager",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .agent-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .task-list {
        margin-left: 1rem;
    }
    .log-container {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
        max-height: 400px;
        overflow-y: auto;
    }
    .activity-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .log-entry {
        font-family: monospace;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .activity-entry {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.5rem;
    }
    .activity-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .role-badge {
        background-color: #007bff;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    }
    .timestamp {
        color: #6c757d;
        font-size: 0.875rem;
    }
    .activity-content {
        color: #212529;
    }
    .status-card {
        background-color: #fff;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-indicator {
        font-size: 1.25rem;
        margin: 0.5rem 0;
    }
    .current-task {
        color: #6c757d;
        font-size: 0.875rem;
    }
    .result-card {
        background-color: #fff;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .result-card h3 {
        color: #007bff;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'sow_file' not in st.session_state:
        st.session_state.sow_file = None
    if 'tasks' not in st.session_state:
        st.session_state.tasks = None
    if 'team_members' not in st.session_state:
        st.session_state.team_members = None
    if 'execution_started' not in st.session_state:
        st.session_state.execution_started = False
    if 'execution_completed' not in st.session_state:
        st.session_state.execution_completed = False
    if 'log_file' not in st.session_state:
        st.session_state.log_file = None

def upload_sow_file():
    """Handle SOW file upload"""
    st.markdown("## 📄 Upload SOW Document")
    uploaded_file = st.file_uploader("Choose a SOW file", type=['docx'])
    
    if uploaded_file is not None:
        try:
            # Create a unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir)
            file_path = os.path.join(docs_dir, f'sow_file_{timestamp}.docx')
            
            # Save the uploaded file
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.sow_file = file_path
            st.success("SOW file uploaded successfully!")
            return True
            
        except PermissionError:
            st.error("Error: Cannot save the file. Please make sure the file is not open in another program and you have write permissions.")
            return False
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")
            return False
    return False

def analyze_sow():
    """Analyze SOW and generate tasks"""
    if st.session_state.sow_file and isinstance(st.session_state.sow_file, str):
        with st.spinner("Analyzing SOW and generating tasks..."):
            try:
                # Load team data
                team_members = load_team_data()
                st.session_state.team_members = team_members
                
                # Extract text from SOW
                sow_text = extract_text_from_docx(st.session_state.sow_file)
                
                # Initialize analyzer and generate tasks
                analyzer = SOWAnalyzer(sow_text, team_members)
                tasks = analyzer.analyze_and_generate_tasks()
                # Check if tasks were generated successfully
                if not tasks or not any(tasks.values()):
                    st.error("❌ Failed to generate tasks. ")
                    st.session_state.tasks = None  # Clear any partial tasks
                    return False
                st.session_state.tasks = tasks
                
                st.success("Analysis completed!")
                return True
            except Exception as e:
                st.error(f"Error analyzing SOW: {str(e)}")
                return False
    return False

def display_tasks_and_controls():
    """Display tasks for each team member (collapsed by default) and control buttons, always at the top."""
    if st.session_state.tasks:
        st.markdown("## 📋 Task Distribution")
        for role, role_tasks in st.session_state.tasks.items():
            with st.expander(f"Tasks for {role}", expanded=False):
                for i, task in enumerate(role_tasks, 1):
                    st.markdown(f"{i}. {task}")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.button(
                "Start Team Execution",
                type="primary",
                disabled=st.session_state.execution_started,
                key="start_team_execution_btn",
                on_click=lambda: setattr(st.session_state, "execution_started", True)
            )
        with col2:
            st.button(
                "Stop Team Execution",
                type="secondary",
                disabled=not st.session_state.execution_started,
                key="stop_team_execution_btn",
                on_click=stop_team_execution
            )
        # Add a single, modern log toggle button below the control buttons
        if 'show_logs' not in st.session_state:
            st.session_state.show_logs = False
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        if st.button("Show Logs" if not st.session_state.show_logs else "Hide Logs", key="toggle_logs_btn"):
            st.session_state.show_logs = not st.session_state.show_logs

def stop_team_execution():
    """Stop the team execution and reset relevant state."""
    st.session_state.execution_started = False
    st.session_state.execution_completed = False


def execute_team_tasks():
    """Execute team tasks and display live updates"""
    if st.session_state.execution_started and not st.session_state.execution_completed:
        # Setup logging
        log_file = setup_logging()
        st.session_state.log_file = log_file

        # Create a container for detailed logs
        logs_expander = st.expander("📝 Detailed Execution Logs", expanded=False)
        with logs_expander:
            log_placeholder = st.empty()
        
        # Create main container for the execution view
        execution_container = st.container()
        
        # Create two columns for the layout
        col1, col2 = execution_container.columns([2, 1])
        
        with col1:
            st.markdown("### 🤖 Team Activity")
            activity_container = st.container()
            activity_placeholder = activity_container.empty()
        
        with col2:
            st.markdown("### 📊 Team Status")
            status_container = st.container()
            status_placeholder = status_container.empty()
        
        # Initialize activity tracking
        current_activity = []
        current_logs = []
        team_status = {role: {"status": "⏳ Waiting", "current_task": None} for role in st.session_state.tasks.keys()}
        
        # Custom logging handler
        class StreamlitLogHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                current_logs.append(log_entry)
                
                # Parse the log message to update team status
                if "Created agent for" in record.msg:
                    role = record.msg.split("Created agent for ")[1].split(":")[0]
                    team_status[role]["status"] = "✅ Ready"
                elif "Assigned task to" in record.msg:
                    role = record.msg.split("Assigned task to ")[1].split(":")[0]
                    task = record.msg.split(": ")[1]
                    team_status[role]["status"] = "🔄 Working"
                    team_status[role]["current_task"] = task
                elif "completed task" in record.msg.lower():
                    role = record.msg.split()[0]
                    team_status[role]["status"] = "✅ Task Completed"
                
                # Add to activity log
                current_activity.append({
                    "role": role if "role" in locals() else "System",
                    "action": record.msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                update_display()
        
        # Add the custom handler
        logger = logging.getLogger()
        streamlit_handler = StreamlitLogHandler()
        streamlit_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(streamlit_handler)
        
        try:
            # Execute team
            with st.spinner("Executing team tasks..."):
                execution_results = execute_team(
                    st.session_state.team_members,
                    st.session_state.tasks
                )
            
            st.session_state.execution_completed = True
            
        except Exception as e:
            st.error(f"Error during execution: {str(e)}")
            st.session_state.execution_completed = False
        finally:
            logger.removeHandler(streamlit_handler)

def main():
    """Main application function"""
    st.title("🤖 AI Team Manager")
    
    # Initialize session state
    initialize_session_state()
    
    # Step 1: Upload SOW
    if not st.session_state.sow_file:
        upload_sow_file()
    
    # Step 2: Analyze SOW
    if st.session_state.sow_file and not st.session_state.tasks:
        analyze_sow()
    
    # Step 3: Always display tasks and control buttons at the top
    if st.session_state.tasks:
        display_tasks_and_controls()
    
    # Step 4: Execute Team (if started) - only activity/status, no tasks/buttons/logs
    if st.session_state.execution_started:
        execute_team_tasks()

if __name__ == "__main__":
    main() 