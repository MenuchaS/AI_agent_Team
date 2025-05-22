from docx import Document
import json
import os
from openai import OpenAI
from typing import List, Dict, Any, Optional, Type
import time
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import logging
from dotenv import load_dotenv
import sys

# Load environment variables from .env 
load_dotenv()

# Get environment variables with error handling
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ZIPEER_MCP_ENDPOINT = os.getenv("ZIPEER_MCP_ENDPOINT")

# Check if required environment variables are set
if not OPENAI_API_KEY or not ZIPEER_MCP_ENDPOINT:
    print("Error: Missing required environment variables!")
    print("Please create a .env file with the following variables:")
    print("OPENAI_API_KEY=your_api_key_here")
    print("ZIPEER_MCP_ENDPOINT=your_endpoint_here")
    sys.exit(1)

# Set environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["ZIPEER_MCP_ENDPOINT"] = ZIPEER_MCP_ENDPOINT

# File paths
TEAM_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'team.json')
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
SOW_FILE = os.path.join(DOCS_DIR, 'sow_file.docx')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Create logs directory
        log_dir = os.path.join(current_dir, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"Created log directory at: {log_dir}")
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'agent_actions_{timestamp}.log')
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8', mode='w'),
                logging.StreamHandler()
            ]
        )
        
        # Test logging
        logging.info("=== Logging System Initialized ===")
        logging.info(f"Log file created at: {log_file}")
        
        # Verify file was created
        if os.path.exists(log_file):
            print(f"✅ Log file created successfully at: {log_file}")
        else:
            print(f"❌ Failed to create log file at: {log_file}")
        
        return log_file
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

# Define custom tools as BaseTool instances
class CursorTool(BaseTool):
    name: str = "Cursor"
    description: str = "IDE tool for code editing and development"
    
    def _run(self, query: str) -> str:
        return f"Using Cursor IDE for: {query}"

class GitHubTool(BaseTool):
    name: str = "GitHub"
    description: str = "Version control and code repository management"
    
    def _run(self, query: str) -> str:
        return f"Using GitHub for: {query}"

class PostmanTool(BaseTool):
    name: str = "Postman"
    description: str = "API testing and development tool"
    
    def _run(self, query: str) -> str:
        return f"Using Postman for: {query}"

class PythonSDKTool(BaseTool):
    name: str = "Python SDK"
    description: str = "Python development tools and libraries"
    
    def _run(self, query: str) -> str:
        return f"Using Python SDK for: {query}"

class NodeSDKTool(BaseTool):
    name: str = "Node.js SDK"
    description: str = "Node.js development tools and libraries"
    
    def _run(self, query: str) -> str:
        return f"Using Node.js SDK for: {query}"

# Define tool mapping
TOOL_MAPPING = {
    "Cursor": CursorTool(),
    "GitHub": GitHubTool(),
    "Postman": PostmanTool(),
    "Python SDK": PythonSDKTool(),
    "Node.js SDK": NodeSDKTool()
}

class TeamMember:
    def __init__(self, role: str, name: str, description: str, objectives: List[str], tools: List[str]):
        self.role = role
        self.name = name
        self.description = description
        self.objectives = objectives
        self.tools = [TOOL_MAPPING[tool] for tool in tools if tool in TOOL_MAPPING]
        self.tasks = []

class TeamAgentCreator:
    def __init__(self, team_members: List[TeamMember]):
        self.team_members = team_members
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, List[Task]] = {}

    def create_agent(self, member: TeamMember) -> Agent:
        """Create agent based on team member data"""
        agent = Agent(
            role=member.role,
            goal=f"Successfully complete all assigned tasks for the {member.role} role",
            backstory=f"{member.description}. My objectives are: {', '.join(member.objectives)}",
            tools=member.tools,
            verbose=True
        )
        logging.info(f"Created agent for {member.role}: {member.name}")
        return agent

    def create_agents(self) -> Dict[str, Agent]:
        """Create agents for each team member"""
        for member in self.team_members:
            agent = self.create_agent(member)
            self.agents[member.role] = agent
            print(f"✅Created agent for {member.role}: {member.name}")
        return self.agents

    def assign_tasks(self, tasks_by_role: Dict[str, List[str]]):
        """Assign tasks to each agent"""
        for role, task_descriptions in tasks_by_role.items():
            if role in self.agents:
                self.tasks[role] = []
                agent = self.agents[role]
                for task_desc in task_descriptions:
                    task = Task(
                        description=task_desc,
                        expected_output=f"Complete the task: {task_desc}",
                        agent=agent
                    )
                    self.tasks[role].append(task)
                    logging.info(f"Assigned task to {role}: {task_desc}")
                print(f"✅Assigned {len(task_descriptions)} tasks to {role} agent")

    def get_agent(self, role: str) -> Agent:
        """Get agent by role"""
        return self.agents.get(role)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks from all agents"""
        return [task for tasks in self.tasks.values() for task in tasks]

def create_required_directories():
    """Create required directories if they don't exist"""
    directories = [
        os.path.dirname(TEAM_FILE),  # config directory
        DOCS_DIR,  # docs directory
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')  # logs directory
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from a DOCX file"""
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"SOW file not found at: {docx_path}\nPlease make sure to place your SOW file in the 'docs' directory.")
    
    try:
        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        raise Exception(f"Error reading SOW file: {str(e)}")

def split_text_into_chunks(text: str, max_chunk_size: int = 8000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks with overlap to maintain context.
    
    Args:
        text: The text to split
        max_chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
        
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of the chunk
        end = start + max_chunk_size
        
        # If we're not at the end of the text, try to find a good breaking point
        if end < len(text):
            # Look for the last period or newline within the last 200 characters
            last_period = text.rfind('.', end - 200, end)
            last_newline = text.rfind('\n', end - 200, end)
            
            # Use the later of the two as the break point
            break_point = max(last_period, last_newline)
            if break_point > end - 200:  # Only use if it's within our search window
                end = break_point + 1
        
        # Add the chunk
        chunks.append(text[start:end])
        
        # Move the start point, accounting for overlap
        start = end - overlap
    
    return chunks

class SOWAnalyzer:
    def __init__(self, sow_text: str, team_members: List[TeamMember]):
        self.sow_text = sow_text
        self.team_members = team_members
        self.chunks = split_text_into_chunks(sow_text)

    def analyze_and_generate_tasks(self) -> Dict[str, List[str]]:
        """Analyze SOW and generate tasks for each team member"""
        tasks_by_role = {member.role: [] for member in self.team_members}
        
        # Prepare team members information
        team_info = "\n".join([
            f"Role: {member.role}\n"
            f"Name: {member.name}\n"
            f"Description: {member.description}\n"
            f"Objectives: {', '.join(member.objectives)}\n"
            f"Tools: {', '.join([tool.name for tool in member.tools])}\n"
            for member in self.team_members
        ])
        
        # Process each chunk
        for i, chunk in enumerate(self.chunks):
            print(f"✅Processing chunk {i+1}/{len(self.chunks)}")
            
            prompt = f"""
            Based on the following section of the SOW document, generate specific, actionable tasks for each team member.
            Focus on concrete, project-specific tasks rather than general responsibilities.
            
            Team Members Information:
            {team_info}
            
            SOW Content (Section {i+1} of {len(self.chunks)}):
            {chunk}
            
            Generate a JSON object where:
            - Keys are team member roles
            - Values are arrays of specific, actionable tasks for that role
            
            Each task should be concrete and measurable.
            
            Example of good tasks:
            - "Create database schema for committee members table with fields: id, name, role, contact_info"
            - "Implement API endpoint for submitting new tender requests"
            - "Design user interface for committee meeting agenda creation"
            
            Example of bad tasks (too general):
            - "Write code"
            - "Test the system"
            - "Document the project"
            
            Format the response as a JSON object like this:
            {{
                "Role1": ["task1", "task2", ...],
                "Role2": ["task1", "task2", ...],
                ...
            }}
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                
                # Parse the response and update tasks
                chunk_tasks = json.loads(response.choices[0].message.content)
                
                # Merge tasks from this chunk with existing tasks
                for role, tasks in chunk_tasks.items():
                    if role in tasks_by_role:
                        # Add new tasks to existing ones
                        tasks_by_role[role].extend(tasks)
                
            except json.JSONDecodeError as e:
                print(f"❌Error parsing tasks for chunk {i+1}: {str(e)}")
            except Exception as e:
                print(f"❌Error processing chunk {i+1}: {str(e)}")
        
        # Remove duplicates and update team members
        for member in self.team_members:
            if member.role in tasks_by_role:
                # Remove duplicates while preserving order
                unique_tasks = list(dict.fromkeys(tasks_by_role[member.role]))
                tasks_by_role[member.role] = unique_tasks
                member.tasks = unique_tasks
        
        return tasks_by_role

def load_team_data() -> List[TeamMember]:
    """Load team data from JSON file"""
    with open(TEAM_FILE, 'r', encoding='utf-8') as f:
        team_data = json.load(f)
    
    return [TeamMember(**member) for member in team_data]

def save_results_to_json(agents: Dict[str, Agent], tasks: Dict[str, List[str]], result: str):
    """Save results to JSON file"""
    output = {
        "agents": {
            role: {
                "name": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory,
                "tools": [tool.name for tool in agent.tools]
            }
            for role, agent in agents.items()
        },
        "tasks": tasks,
        "execution_result": result
    }
    
    output_file = os.path.join(os.path.dirname(__file__), 'result.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    print(f"✅Results saved to {output_file}")

def display_tasks_for_confirmation(tasks: Dict[str, List[str]]):
    """Display tasks and get user confirmation"""
    print("\n=== Task Distribution for Review ===")
    for role, role_tasks in tasks.items():
        print(f"\n{role}:")
        for i, task in enumerate(role_tasks, 1):
            print(f"{i}. {task}")
    
    while True:
        confirmation = input("\nDo you want to proceed with these tasks? (yes/no): ").lower()
        if confirmation in ['yes', 'y']:
            return True
        elif confirmation in ['no', 'n']:
            return False
    else:
            print("Please enter 'yes' or 'no'")

def execute_team(team_members: List[TeamMember], tasks: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Execute the team of agents with their assigned tasks
    
    Args:
        team_members: List of team members
        tasks: Dictionary of tasks by role
        
    Returns:
        Dictionary containing execution results
    """
    try:
        logging.info("Starting team execution...")
        
        # Create and initialize agents
        logging.info("Creating AI Agents...")
        agent_creator = TeamAgentCreator(team_members)
        agents = agent_creator.create_agents()
        
        # Assign tasks to agents
        logging.info("Assigning tasks to agents...")
        agent_creator.assign_tasks(tasks)
        
        # Create and run the crew
        logging.info("Initializing crew...")
        crew = Crew(
            agents=list(agents.values()),
            tasks=agent_creator.get_all_tasks(),
            process=Process.sequential,
            verbose=True,
            max_rpm=10,  # הגבלת בקשות לדקה
            max_tokens_per_agent=500,  # הגבלת טוקנים לכל agent
            max_input_tokens=1000  # הגבלת טוקנים בקלט
        )
        
        #run agents in parallel
        logging.info("Starting crew execution...")
        result = crew.kickoff()
        logging.info("Crew execution completed")
        
        # Prepare execution results
        execution_results = {
            "agents": {
                role: {
                    "name": agent.role,
                    "goal": agent.goal,
                    "backstory": agent.backstory,
                    "tools": [tool.name for tool in agent.tools],
                    "assigned_tasks": len(agent_creator.tasks.get(role, []))
                }
                for role, agent in agents.items()
            },
            "tasks": tasks,
            "execution_result": result
        }
        
        # Save results to JSON
        save_results_to_json(agents, tasks, result)
        
        # Log detailed results
        logging.info("\nTask Distribution:")
        for role, role_tasks in tasks.items():
            logging.info(f"\n{role}:")
            for task in role_tasks:
                logging.info(f"- {task}")
        
        logging.info("\nAgent Details:")
        for role, agent in agents.items():
            logging.info(f"\n{role}:")
            logging.info(f"Role: {agent.role}")
            logging.info(f"Goal: {agent.goal}")
            logging.info(f"Backstory: {agent.backstory}")
            logging.info(f"Tools: {', '.join([tool.name for tool in agent.tools])}")
            logging.info(f"Assigned Tasks: {len(agent_creator.tasks.get(role, []))}")
        
        logging.info(f"\nCrew Execution Result: {result}")
        
        return execution_results
        
    except Exception as e:
        error_msg = f"Error in team execution: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        raise

# For Running the Backend (No UI) 
def main():
    try:
        # Create required directories
        create_required_directories()
        
        # Setup logging
        log_file = setup_logging()
        if not log_file:
            print("Failed to setup logging system")
            return
            
        logging.info("Starting main function...")
        print(f"Log file created at: {log_file}")
        
        # Load team data
        print("Loading team data...")
        team_members = load_team_data()
        logging.info(f"Loaded {len(team_members)} team members")
        print(f"Loaded {len(team_members)} team members")
        
        # Load and analyze SOW
        print("Loading SOW file...")
        if not os.path.exists(SOW_FILE):
            print(f"\n❌ SOW file not found at: {SOW_FILE}")
            print("Please make sure to:")
            print("1. Create a 'docs' directory in your project root")
            print("2. Place your SOW file (sow_file.docx) in the 'docs' directory")
            return
            
        sow_text = extract_text_from_docx(SOW_FILE)
        logging.info(f"SOW text length: {len(sow_text)} characters")
        print(f"SOW text length: {len(sow_text)} characters")
        
        print("Initializing SOW analyzer...")
        analyzer = SOWAnalyzer(sow_text, team_members)
        
        print("Generating tasks...")
        tasks = analyzer.analyze_and_generate_tasks()
        logging.info("Generated tasks for all team members")
        
        # Display tasks and get user confirmation
        if not display_tasks_for_confirmation(tasks):
            logging.info("Task execution cancelled by user")
            print("Task execution cancelled by user.")
            return
        
        # Execute the team
        print("\nExecuting team...")
        execution_results = execute_team(team_members, tasks)
        
        # Print results to console
        print("\nTask Distribution:")
        for role, role_tasks in tasks.items():
            print(f"\n{role}:")
            for task in role_tasks:
                print(f"- {task}")
        
        print("\nAgent Details:")
        for role, agent_info in execution_results["agents"].items():
            print(f"\n{role}:")
            print(f"Role: {agent_info['name']}")
            print(f"Goal: {agent_info['goal']}")
            print(f"Backstory: {agent_info['backstory']}")
            print(f"Tools: {', '.join(agent_info['tools'])}")
            print(f"Assigned Tasks: {agent_info['assigned_tasks']}")
        
        print("\nCrew Execution Result:")
        print(execution_results["execution_result"])
            
    except Exception as e:
        error_msg = f"Error occurred: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        import traceback
        logging.error(traceback.format_exc())
        print(traceback.format_exc())

if __name__ == "__main__":
    print("🔄Script started")
    main()
    print("✅Script completed")
