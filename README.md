# Autonomous Agent — Document Builder

A Python autonomous AI agent that takes a natural-language request, plans its
own execution steps, orchestrates tools for real supporting data, drafts a
professional business document, and returns a polished Microsoft Word file —
end to end, through a single API call and a live demo UI.

Built for the **Python AI Engineer – Autonomous Agents** 60-minute build
challenge.

---

## Architecture

```
User request
     │
     ▼
[Guardrails]  ── validates length / blocks disallowed patterns
     │
     ▼
[Planner]  ── Gemini decides: document type, title, assumptions, and a
               4–6 step execution plan (with a tool assigned per step
               where useful)
     │
     ▼
[Executor]  ── walks the plan:
               - calls the tool the plan specified (real Python function)
               - feeds the tool's real data into Gemini to draft that section
               - catches and recovers from any tool/LLM failure per step
     │
     ▼
[Reflection] ── one-line self-check: does the draft plausibly satisfy
                the original request?
     │
     ▼
[Document Generator] ── python-docx builds a styled .docx (title page,
                         request summary, stated assumptions, sections)
     │
     ▼
Response: task list + execution log + engineering note + download link
```

All requests and execution steps are also logged to a local **SQLite**
database (`data.db`) — no external database required.

---

## The Mandatory Engineering Improvement: Tool Orchestration

The planner doesn't just draft text — for each step it decides **which tool
to call and with what arguments** from a small registry
(`app/agent/tools.py`):

- `get_mock_financial_data` — budget, ROI, timeline, risk
- `get_mock_market_trends` — industry growth rate, competitive pressure
- `get_mock_team_data` — a project team roster
- `get_current_datetime` — real timestamp

The executor (`app/agent/executor.py`) actually calls those Python functions,
and feeds their real output back into the LLM prompt for that section —
so figures in the final document come from executed code, not from the
model just making numbers up. If a tool call fails, the step degrades
gracefully (logged as `failed`, execution continues) instead of crashing
the whole request — a bit of error handling & recovery layered on top.

---

## Setup

### 1. Create and activate a virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Add your free Gemini API key
Get one at https://aistudio.google.com/app/apikey (no credit card needed).

Copy `.env.example` to `.env` and fill it in:
```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

### 4. Run the server
```powershell
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000/agent
- Live demo UI: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health

### 5. Try it via the UI
Open http://127.0.0.1:8000/ in a browser, type a request (or click one of the
example chips), and click **Run Agent**. Watch the task list and execution
log populate, then download the generated `.docx`.

### 6. Or run the two required test cases from a second terminal
```powershell
python tests/test_case_1_standard.py
python tests/test_case_2_complex.py
```

---

## Project Structure

```
NewProject/
├── app/
│   ├── main.py                # FastAPI app, POST /agent route
│   ├── config.py              # env vars & settings
│   ├── schemas.py              # Pydantic request/response models
│   ├── agent/
│   │   ├── llm_client.py      # Gemini wrapper (text + strict-JSON calls, retries)
│   │   ├── planner.py         # autonomous task/TODO list generation
│   │   ├── executor.py        # runs each step, calls tools, drafts sections
│   │   ├── tools.py           # tool registry + mock-data tool implementations
│   │   ├── guardrails.py      # request validation & sanitization
│   │   └── reflection.py      # bonus self-check pass
│   ├── document/
│   │   └── doc_generator.py   # python-docx: builds the final .docx
│   └── db/
│       ├── database.py        # SQLite engine/session setup
│       └── models.py          # RequestLog, ExecutionLog, AgentMemory tables
├── frontend/
│   ├── index.html
│   ├── style.css               # custom animations, gradients, responsive
│   └── script.js
├── tests/
│   ├── test_case_1_standard.py
│   └── test_case_2_complex.py
├── outputs/                    # generated .docx files land here
├── data.db                     # auto-created SQLite file
├── .env / .env.example
├── requirements.txt
└── README.md
```

---

## Design Notes for the Demo Video

**Debugging insight talking point:** Gemini occasionally wraps JSON
responses in ` ```json ` fences despite instructions not to — `llm_client.py`
strips those fences before parsing, and retries with a stricter prompt if
parsing still fails.

**Tradeoff talking point:** *Autonomous planning vs. deterministic
workflows.* The planner is free to choose section count, titles, and tool
usage per request, which handles ambiguous inputs gracefully (test case 2)
but means output structure varies run to run — a stricter, hardcoded
template would be more predictable but far less flexible for varied
requests.

---

## Safety & Cost

- 100% free: Gemini free tier + local SQLite, no paid services.
- Secrets stay local: `.env` is git-ignored, never committed.
- Guardrails reject empty/oversized/prompt-injection-style input before any
  API call is made.
- Content written into the `.docx` is sanitized to strip non-printable
  characters.
