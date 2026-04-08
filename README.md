# Browser GUI Agent

A browser automation agent that uses **LangGraph** state machines, **Playwright**, and **GPT-4o Vision** to complete structured navigation tasks on live websites — without any hard-coded selectors or scripts.

---

## How It Works

1. The agent navigates to a URL and takes a screenshot.
2. GPT-4o analyzes the screenshot + task goal and returns a structured JSON action.
3. Playwright executes the action (click, fill, scroll, navigate, etc.).
4. The loop repeats until the task is complete or the step limit is reached.

```
observe (screenshot + GPT-4o) → act (Playwright) → [loop or done]
```

State is managed as a typed dict passed through a compiled LangGraph graph.

---

## Project Structure

```
browser-gui-agent/
├── agent/
│   ├── graph.py        # LangGraph state machine (observe → act nodes)
│   ├── browser.py      # Playwright controller (click, fill, scroll, etc.)
│   └── vision.py       # GPT-4o vision layer — screenshot → structured action
├── tasks/
│   └── definitions.py  # Task definitions with goals, URLs, and success checks
├── eval/
│   ├── harness.py      # Eval runner — scores output, measures latency
│   └── results/        # JSON results per task (auto-generated)
├── screenshots/        # Per-step screenshots (auto-generated)
├── replay/             # GIF and HTML replays of agent runs (auto-generated)
├── main.py             # Entry point — run all tasks or a single task by ID
├── requirements.txt
└── .env                # API key (not committed)
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/your-username/browser-gui-agent.git
cd browser-gui-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

> The agent uses your **locally installed Chrome** (`channel="chrome"`). Make sure Chrome is installed.

### 3. Set your OpenAI API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...your-key-here...
```

---

## Running

### Run all 3 tasks

```bash
python main.py
```

### Run a single task by ID

```bash
python main.py --task cheapest_car
python main.py --task first_golf_specs
python main.py --task bmw_filter_count
```

---

## Tasks

All tasks run against [AutoScout24](https://www.autoscout24.de), a live German automotive listings site.

### Baseline tasks

| Task ID | Goal | Success Criteria |
|---|---|---|
| `cheapest_car` | Find the make, model, and price of the cheapest used car under €20,000 | Output contains a euro price |
| `first_golf_specs` | Click the first VW Golf listing and return mileage and year | Output contains `km` and a 4-digit year |
| `bmw_filter_count` | Find the total number of BMW results under €15,000 | Output contains a number |

### Multi-step interaction tasks

| Task ID | Goal | What makes it harder |
|---|---|---|
| `ui_polo_price_filter` | Apply a max price filter of €10,000 via the UI filter panel on the VW Polo results page, then return the result count | Agent must interact with filter dropdowns/inputs and trigger a search — no pre-built URL shortcut |
| `contact_form_fill` | Open the first VW Golf listing, find the contact form, fill in name/email/phone/message, and return the dealer name — without submitting | Multi-step navigation + real form filling across multiple input types; agent must know when to stop |

Results are saved to `eval/results/<task_id>.json` after each run.

---

## Sample Output

```
========================================================================
TASK                   SUCCESS   STEPS   LATENCY    FAILURE MODE
------------------------------------------------------------------------
cheapest_car           PASS      4       18.3
first_golf_specs       PASS      5       22.1
bmw_filter_count       PASS      3       14.8
ui_polo_price_filter   PASS      7       31.2
contact_form_fill      PASS      9       38.5
========================================================================

Success rate : 5/5
Avg steps    : 5.6
Avg latency  : 25.0s
Results saved: eval/results/
```

---

## Key Design Decisions

- **No hard-coded selectors** — the agent decides what to interact with purely from the screenshot.
- **Stealth mode** — `playwright-stealth` patches browser fingerprints to avoid bot detection.
- **Loop detection** — if the last 3 actions are identical, the agent aborts to avoid infinite loops.
- **GDPR handling** — consent banners are dismissed automatically before the agent loop starts.
- **Structured JSON output** — GPT-4o is constrained to a JSON schema via `response_format`, so parsing never fails on format issues.

---

## Requirements

- Python 3.11+
- Google Chrome (installed locally)
- OpenAI API key with GPT-4o access
