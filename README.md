 🤖 AI Team Manager – Automate Task Execution from SOW Documents

An AI-powered team coordination platform for automating task execution from a structured Statement of Work (SOW) document.  
This system leverages an AI agent team, orchestrated through MCP (Model Context Protocol), with a modern web UI and detailed activity tracking.

---

## 🚀 Overview

AI Team Manager automates the parsing of SOW documents, generates tasks based on the content, and dynamically distributes them across a team of AI agents (e.g., Architect, Developer, PM).  
The system includes both a command-line backend and a full-featured Streamlit-based UI for live monitoring and control.

---

## 💡 Key Features

- 📄 **SOW Upload** – Upload and process a `.docx` file containing structured work statements
- 🧠 **AI Task Parsing** – Automatically extract tasks and assign them to appropriate AI roles
- 🧑‍💻 **Agent Execution** – Assign tasks to AI agents by predefined roles (Architect, Developer, PM - config by prompt)
- 📊 **Live Dashboard** – Track agent activity, logs, and status in real time via the Streamlit UI
- 📁 **Logging System** – Logs are saved per run in timestamped folders for traceability

---

## 📦 Project Structure

```
├── app/
│   ├── execute_sowFile_byTeam.py   # Script for CLI execution
│   └── AI_Team_App.py              # Streamlit UI
│
├── config/
│   └── team.json                   # Team roles and agents config
│
├── docs/
│   └── SOW_sample.docx            # Sample SOW file (optional)
│
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .env                            # API keys (not tracked by Git)
└── .gitignore                      # Ignore cache, env, and secrets
```

---

## ⚙️ Prerequisites

- Python 3.9 or higher
- An OpenAI API key
- A Zapier Webhook endpoint for MCP (optional for automation)

---

## 🔧 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-team-manager.git
cd ai-team-manager
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Activate (Windows)
.env\Scriptsctivate
# or (Mac/Linux)
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a file named `.env` in the root directory and add:

```env
OPENAI_API_KEY=your_openai_api_key_here
ZIPEER_MCP_ENDPOINT=your_zapier_webhook_url
```

✅ `.env` is already excluded from Git via `.gitignore`

---

## 🧪 Running the Backend (No UI)
> 🛠 **Important:** When running the backend (non-UI mode), make sure you manually create the following before execution:
>
> 1. A folder named `docs` inside the root directory (if it doesn't exist).
> 2. Inside `docs/`, place your SOW input file named exactly:
>
> ```
> sow_file.docx
> ```
>
> The system will look for the file at: `./docs/sow_file.docx` by default.


To run the full SOW processing pipeline from the terminal (headless mode):

> Make sure there's a file named `sow.docx` in the root folder.

```bash
python app/execute_sowFile_byTeam.py
```

---

## 🖥️ Running the Web UI (Streamlit)

Launch the full interface:

```bash
streamlit run app/AI_Team_App.py
```

- The UI will open at: [http://localhost:8501](http://localhost:8501)
- Upload an SOW file → Review & confirm tasks → Start execution
- All logs and agent statuses are displayed live

---

## 📁 Logs

Each run creates a log folder under `/logs/YYYY-MM-DD_HH-MM-SS`  
This includes agent messages, errors, task outputs, and progress tracking.

---

## 📣 Questions / Issues?

Feel free to:
- Open an issue on GitHub
- Submit a pull request
- Contact the project maintainers

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE)

---

## 🙌 Contributions Welcome

If you’d like to contribute, fork the repository and submit a pull request with improvements or new features!
