# Device Health Agent

Device Health Agent is a lightweight system monitoring and self-healing assistant built with Streamlit.
It monitors CPU, RAM, disk usage, and battery state, detects anomalies, and decides whether to take an action such as clearing temporary files or stopping a high-CPU process.

## Features

- Real-time monitoring dashboard with Streamlit.
- System telemetry collection using psutil.
- Rule-based anomaly detection with configurable thresholds.
- AI-assisted action selection using Groq (optional).
- Safe fallback action policy when AI is unavailable.
- Quick process inspection panel for top CPU-consuming processes.

## Project Structure

```text
device-health-agent/
|- app.py
|- requirements.txt
|- test_actions.py
|- test_agent.py
|- test_analyzer.py
|- test_monitor.py
|- config/
|  |- settings.py
|- core/
|  |- actions.py
|  |- agent.py
|  |- analyzer.py
|  |- monitor.py
|- utils/
|  |- helpers.py
```

## How It Works

1. `core.monitor` collects system stats:
	- CPU usage
	- RAM usage
	- Disk usage
	- Battery status (if available)
2. `core.analyzer` compares stats against thresholds in `config/settings.py`.
3. `core.agent` chooses an action:
	- AI decision via Groq if `GROQ_API_KEY` is present.
	- Rule-based fallback if AI is unavailable or fails.
4. `core.actions` executes the selected action:
	- `clear_temp_files()`
	- `kill_high_cpu_process()`
5. `app.py` renders everything in a Streamlit dashboard and refreshes periodically.

## Threshold Configuration

Default thresholds in `config/settings.py`:

- `CPU_THRESHOLD = 85`
- `RAM_THRESHOLD = 80`
- `DISK_THRESHOLD = 90`
- `BATTERY_THRESHOLD = 20`

You can tune these values to match your device behavior.

## Setup

### 1. Clone and move into project directory

```powershell
git clone https://github.com/viswanadhapalli-sandhya/device-health-agent.git
cd device-health-agent
```

### 2. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
pip install python-dotenv
```

Note: `core/agent.py` uses `python-dotenv` (`load_dotenv`) but it is not currently listed in `requirements.txt`.

### 4. Configure environment variables (optional for AI mode)

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
# Optional fallback chain if GROQ_MODEL is not set
# GROQ_MODEL_CANDIDATES=llama-3.1-8b-instant,llama-3.3-70b-versatile
```

If `GROQ_API_KEY` is missing, the app automatically uses fallback rules.
If `GROQ_MODEL` is omitted, the app uses internal default model candidates.

## Run the App

```powershell
streamlit run app.py
```

Open the local URL shown in the terminal (usually `http://localhost:8501`).

## Utility Test Scripts

These are simple runnable scripts (not pytest test cases):

- `test_monitor.py` -> prints current system stats
- `test_analyzer.py` -> prints detected issues from current stats
- `test_agent.py` -> runs decision + action flow
- `test_actions.py` -> runs action helpers directly

Run any script with:

```powershell
python test_monitor.py
python test_analyzer.py
python test_agent.py
python test_actions.py
```

## Action Safety Notes

- `kill_high_cpu_process()` may terminate a process above threshold. Use with caution.
- Temporary file cleanup skips locked/system files and continues safely.
- You should avoid running this tool with elevated privileges unless needed.

## Tech Stack

- Python
- Streamlit
- psutil
- pandas
- matplotlib
- Groq Python SDK

## Known Limitations

- Disk usage path is currently `'/'`, which may not represent the intended drive on all Windows setups.
- `utils/helpers.py` is currently empty and reserved for shared helper functions.
- Auto-refresh interval in UI is fixed to 300 seconds in `app.py`.


