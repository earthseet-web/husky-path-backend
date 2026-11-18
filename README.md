# Husky Path backend (demo prototype)

The backend for **Husky Path**, a student-built AI assistant that helps UW students plan courses for
**Electrical and Computer Engineering (ECE)**. It answers from a fixed set of UW course data instead of
searching the web, so it doesn't pick up last year's or wrong information.

> **Prototype for demo day (Dec 3).** Course data was collected from the public UW catalog on 2026-11-16.
> It is not connected to MyPlan, DARS or registration. Students should confirm everything with an adviser.

## How it works

1. The front end sends the student's question and profile (completed courses, credits wanted, goals).
2. **Code** (not AI) checks prerequisites, ECE placement progress and credit totals (`checks.py`).
3. **Gemini** writes the answer using only our course list and those check results (`ai.py`).
4. The backend removes any course the AI names that isn't in our data, then sends back course cards.
5. If the AI isn't connected or fails, a rule-based answer is returned instead, so the demo keeps working.

## Run it (Mac)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then open .env and paste your Gemini key
uvicorn app:app --reload
```

Then open **http://127.0.0.1:8000** for the full Husky Path app (Adeline's front end connected to this backend),
or **http://127.0.0.1:8000/docs** to try each endpoint directly.

On Windows with Smart App Control, run tools through Python: `python -m pip ...`, `python -m pytest -q`,
`python -m uvicorn app:app --reload`.

**Getting a Gemini key (free):** go to https://aistudio.google.com/apikey, sign in, click
**Create API key**, and paste it after `GEMINI_API_KEY=` in `backend/.env`. Never commit `.env`.

**Check it's connected:** open http://127.0.0.1:8000/health. `"ai_connected": true` means the key was found.
If chat answers say *"The AI isn't connected right now"*, the response's `ai_error` field says why
(for example a wrong key, or a model that stopped answering). Run `python tools/test_gemini.py` to test which models work with your key and set the fastest as `GEMINI_MODEL` in `.env`. Tested on 2026-11-17: `gemini-3.1-flash-lite` answers in under a second.

**Run the tests:** `pytest -q` inside `backend/`. They use a fake AI, so no key is needed.

**The front end** lives in `frontend/` and is served at http://127.0.0.1:8000/ automatically. See
`frontend/CHANGES.md` for what changed from Adeline's version. If the backend is off, the page still opens
from `frontend/index.html` and falls back to her scripted demo replies.

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Is it running, how many courses, is the AI key set |
| GET | `/courses?search=` | Search courses by code, title or description |
| GET | `/courses/{code}` | One course (`ee215`, `E E 215` and `EE 215` all work) |
| POST | `/check` | Placement progress, graduation progress, courses you're ready for, and a draft-quarter check |
| POST | `/chat` | Ask a question; returns `title`, `intro`, `cards`, `follow`, `source` (`ai` or `fallback`) |

Example `/chat` request:

```json
{
  "message": "What should I take next quarter?",
  "profile": {
    "major": "Engineering Undeclared, aiming for ECE",
    "completed": "MATH 124 3.5, CHEM 142, ENGR 101",
    "in_progress": "MATH 125, CSE 121, ENGL 131",
    "credits": 15,
    "goals": "robotics"
  },
  "preferences": ["No Friday classes"],
  "plan": [],
  "history": []
}
```

Each card has `code`, `title`, `credits`, `reason` (from the AI), `reqLabel`, `description`,
`prereq_text`, `url`, `offered`, `fits` and `warns` (from our checks).

## Files

| File | Purpose |
| --- | --- |
| `frontend/` | Adeline's Husky Path front end, connected to the backend by `frontend/backend.js` |
| `backend/app.py` | The API (also serves `frontend/`) |
| `backend/checks.py` | Prerequisite, placement, requirement and credit checks (no AI) |
| `backend/ai.py` | The only file that talks to Gemini; swap providers here |
| `backend/data/ece_courses.json` | 118 courses: all E E courses plus required MATH, PHYS, CHEM, CSE, STAT, IND E, BIOL, ENGR |
| `backend/data/ece_requirements.json` | ECE placement and graduation requirements (Autumn 2025+ rules) |
| `backend/data/ece_sample_plan.json` | Official sample four-year plan for Engineering Undeclared students |
| `backend/tools/build_data.py` | Rebuilds the three data files; edit course facts here |
| `backend/test_checks.py` | Tests |
| `DATA_GAPS.md` | What the sources didn't say, and what to verify |

## Sources

- [ECE degree requirements and sample four-year plan (College of Engineering)](https://www.engr.washington.edu/current/academics/4-year-plans/ece-degree-requirements)
- [BSECE degree requirements (UW ECE)](https://www.ece.uw.edu/academics/bachelor-of-science/bsece/degree-requirements/)
- [UW course catalog](https://www.washington.edu/students/crscat/): E E, MATH, AMATH, PHYS, CHEM, CSE, STAT, IND E, BIOL, ENGR
