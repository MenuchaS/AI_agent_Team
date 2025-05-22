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
                    st.error("❌ Failed to generate tasks. There might be an issue with your OpenAI API key or it has run out of credit.")
                    st.info("Please check your API key at https://platform.openai.com/account/usage")
                    st.session_state.tasks = None  # Clear any partial tasks
                    return False
                
                st.session_state.tasks = tasks
                st.success("✅ Analysis completed successfully!")
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                if "insufficient_quota" in error_msg or "429" in error_msg:
                    st.error("❌ OpenAI API key has run out of credit")
                    st.info("Please check your account at https://platform.openai.com/account/usage")
                else:
                    st.error(f"❌ An error occurred: {str(e)}")
                
                st.session_state.tasks = None  # Clear any partial tasks
                return False
    return False

def display_tasks():
    """Display tasks for each team member"""
    if st.session_state.tasks and any(st.session_state.tasks.values()):
        st.markdown("## 📋 Task Distribution")
        
        for role, role_tasks in st.session_state.tasks.items():
            if role_tasks:  # Only show roles with tasks
                with st.expander(f"Tasks for {role}", expanded=True):
                    for i, task in enumerate(role_tasks, 1):
                        st.markdown(f"{i}. {task}")
        
        if st.button("Start Team Execution", type="primary"):
            st.session_state.execution_started = True
            return True
    else:
        st.warning("⚠️ No tasks available to display. Please ensure the analysis completed successfully.")
    return False

def execute_team_tasks():
    """Execute team tasks and display live updates"""
    if st.session_state.execution_started and not st.session_state.execution_completed:
        # Setup logging
        log_file = setup_logging()
        st.session_state.log_file = log_file
        
        # Create containers for live updates
        activity_container = st.container()
        log_container = st.container()
        
        # Execute team
        with st.spinner("Executing team tasks..."):
            try:
                # Create a placeholder for the activity log
                activity_placeholder = activity_container.empty()
                log_placeholder = log_container.empty()
                
                # Start with empty logs
                current_activity = []
                current_logs = []
                
                def update_display():
                    """Update the display with current activity and logs"""
                    # Display activity in a nice format
                    activity_text = "### 🤖 Team Activity\n\n"
                    for activity in current_activity:
                        activity_text += f"**{activity['role']}**: {activity['action']}\n\n"
                    activity_placeholder.markdown(activity_text)
                    
                    # Display logs in a code block
                    log_text = "### 📝 Detailed Logs\n```\n"
                    log_text += "\n".join(current_logs)
                    log_text += "\n```"
                    log_placeholder.markdown(log_text)
                
                # Custom logging handler to capture logs
                class StreamlitLogHandler(logging.Handler):
                    def emit(self, record):
                        log_entry = self.format(record)
                        current_logs.append(log_entry)
                        # Keep only last 100 logs
                        if len(current_logs) > 100:
                            current_logs.pop(0)
                        update_display()
                
                # Add the custom handler
                logger = logging.getLogger()
                streamlit_handler = StreamlitLogHandler()
                streamlit_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                logger.addHandler(streamlit_handler)
                
                # Execute team
                execution_results = execute_team(
                    st.session_state.team_members,
                    st.session_state.tasks
                )
                
                # Display execution results
                st.markdown("## 🎯 Execution Results")
                
                # Display agent interactions
                st.markdown("### 🤖 Agent Interactions")
                for role, agent_info in execution_results["agents"].items():
                    with st.expander(f"{role} - {agent_info['name']}", expanded=True):
                        st.markdown(f"**Goal:** {agent_info['goal']}")
                        st.markdown(f"**Tools:** {', '.join(agent_info['tools'])}")
                        st.markdown(f"**Tasks Completed:** {agent_info['assigned_tasks']}")
                
                # Display final result
                st.markdown("### 📝 Final Result")
                st.markdown(execution_results["execution_result"])
                
                st.session_state.execution_completed = True
                st.success("Team execution completed successfully!")
                
            except Exception as e:
                st.error(f"Error during execution: {str(e)}")
                st.session_state.execution_completed = False
            finally:
                # Remove the custom handler
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
    
    # Step 3: Display Tasks
    if st.session_state.tasks and not st.session_state.execution_started:
        display_tasks()
    
    # Step 4: Execute Team
    if st.session_state.execution_started:
        execute_team_tasks()

if __name__ == "__main__":
    main() 