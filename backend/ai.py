"""The only file that talks to the AI provider (Google Gemini).

To switch providers later, replace `call_model()` and keep the same input/output.
"""
from __future__ import annotations

import json
import os
import re

import httpx

import checks

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.1-flash-lite"

SYSTEM_RULES = """You are Husky Path, a course-planning assistant for University of Washington students
who want to study Electrical and Computer Engineering (ECE). This is a student demo, not an official UW tool.

Rules:
1. Use ONLY the courses and requirements given to you below. Never invent course codes, titles,
   credits, prerequisites, quarters offered, instructors or links.
2. Prerequisite and placement results were computed by code and are correct. Use them; do not recompute.
3. Only recommend courses from the "Eligible next" list or that the student asked about by name.
   If a course they ask about is not eligible yet, say what is missing.
4. If something is not in the data (a course outside this list, section times, seats, transfer credit,
   whether a course counts for graduation in an unusual case), say you don't have it and point the student
   to MyPlan, their DARS audit, or an adviser (undergradece@uw.edu for ECE; engradv@uw.edu for Engineering advising).
5. Quarters offered come from the catalog and are not a promise. Say "usually offered" at most.
6. If the student is NOT yet placed in ECE ("in_major": false), focus on ECE placement courses and
   math/science/programming. Do not recommend E E courses unless they ask about one by name; if they ask
   about their interests (e.g. robotics), you may name relevant E E courses as "later" options in the intro text only.
7. A quarter plan should add up to about the student's target credits (never more than target + 2).
   Recommend 2-4 courses, and say the total in the intro.
8. Keep it short and friendly: a one-line title, 1-3 sentences of intro, and a one-sentence reason per course
   tied to the student's goals and requirements.
9. "follow" = 2-3 short questions THE STUDENT might ask you next (written as the student), e.g.
   "Can I take PHYS 122 in spring?" Never questions addressed to the student.

Reply with JSON only, in exactly this shape:
{"title": "...", "intro": "...", "courses": [{"code": "E E 215", "reason": "..."}], "follow": ["short follow-up question", "..."]}
"""

CODE_IN_TEXT = re.compile(r"\b([A-Za-z]{1,6}(?:\s?[A-Za-z]{1,2})?)\s?(\d{3})\b")


def mentioned_codes(text: str) -> list[str]:
    found = []
    for m in CODE_IN_TEXT.finditer(text or ""):
        code = checks.normalize_code(f"{m.group(1)} {m.group(2)}")
        if code and code in checks.COURSES and code not in found:
            found.append(code)
    return found


def _catalog_lines() -> str:
    lines = []
    for c in checks.COURSES.values():
        cr = c["credits"] if c["credits"] == c["credits_max"] else f"{c['credits']}-{c['credits_max']}"
        off = f" | usually offered: {c['offered']}" if c.get("offered") else ""
        lines.append(f"{c['code']} | {c['title']} | {cr} cr | prereq: {c['prereq_text']}{off} | {c['description']}")
    return "\n".join(lines)


CATALOG_TEXT = _catalog_lines()


def _requirements_text() -> str:
    r = checks.REQUIREMENTS
    p = r["placement"]
    lines = [f"Program: {r['program']}. {r['applies_to']}. Total {r['total_credits']} credits.",
             f"{p['label']}: " + "; ".join(i["label"] for i in p["items"]) + f". {p['deadline']}. {p['min_grade_note']}"]
    for grp in r["graduation"]:
        parts = []
        for i in grp["items"]:
            t = i["label"]
            if i.get("rules"):
                t += " (" + "; ".join(i["rules"]) + ")"
            parts.append(t)
        lines.append(f"{grp['group']}: " + "; ".join(parts))
    lines.append("Grade rules: " + "; ".join(f"{k}: {v}" for k, v in r["grade_rules"].items()))
    return "\n".join(lines)


REQUIREMENTS_TEXT = _requirements_text()


def build_context(message: str, profile: dict, student: checks.Student, prefs: list[str], plan: list[str]) -> dict:
    asked = mentioned_codes(message)
    return {
        "student": {
            "name": (profile or {}).get("name"),
            "major_or_goal": (profile or {}).get("major") or "Engineering Undeclared, aiming for ECE",
            "target_quarter": (profile or {}).get("quarter"),
            "target_credits": student.target_credits,
            "in_major": student.in_major,
            "goals_and_interests": (profile or {}).get("goals"),
            "completed": [f"{c}" + (f" ({g})" if g is not None else "") for c, g in student.completed.items()],
            "in_progress": sorted(student.in_progress),
            "preferences": prefs,
            "draft_plan": plan,
        },
        "placement_progress": checks.placement_progress(student),
        "eligible_next": checks.eligible_next(student),
        "asked_about": [checks.prereq_status(c, student) for c in asked],
        "draft_plan_check": checks.check_plan(student, plan) if plan else None,
    }


def build_prompt(message: str, context: dict, history: list[dict] | None) -> str:
    convo = ""
    for turn in (history or [])[-6:]:
        who = "Student" if turn.get("role") == "user" else "Assistant"
        convo += f"{who}: {str(turn.get('text', ''))[:600]}\n"
    return (
        f"{SYSTEM_RULES}\n\n=== ECE REQUIREMENTS (summary) ===\n{REQUIREMENTS_TEXT}\n\n"
        f"=== COURSE CATALOG (only these courses exist for you) ===\n{CATALOG_TEXT}\n\n"
        f"=== STUDENT AND CHECK RESULTS (computed by code) ===\n{json.dumps(context, separators=(',', ':'))}\n\n"
        f"=== RECENT CONVERSATION ===\n{convo or '(none)'}\n"
        f"=== STUDENT'S NEW MESSAGE ===\n{message}\n"
    )


class AIUnavailable(Exception):
    pass


def call_model(prompt: str) -> dict:
    """Send the prompt to Gemini and return the parsed JSON reply."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise AIUnavailable("No GEMINI_API_KEY set")
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    timeout = float(os.getenv("GEMINI_TIMEOUT", "90") or 90)
    config = {"temperature": 0.3, "responseMimeType": "application/json",
              "thinkingConfig": {"thinkingLevel": "low"}}  # quick answers; set by model generation
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": config}
    url = GEMINI_URL.format(model=model)
    headers = {"x-goog-api-key": key}
    try:
        r = httpx.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code == 400 and "thinking" in r.text.lower():
            # Older models don't accept thinkingLevel: retry without it.
            config.pop("thinkingConfig")
            r = httpx.post(url, headers=headers, json=body, timeout=timeout)
    except httpx.TimeoutException as e:
        raise AIUnavailable(f"Gemini took longer than {timeout:.0f} seconds (timeout). "
                            "Try again, or set GEMINI_MODEL to a faster model in .env") from e
    except httpx.HTTPError as e:
        raise AIUnavailable(f"Could not reach Gemini: {e.__class__.__name__}") from e
    if r.status_code != 200:
        try:
            msg = r.json().get("error", {}).get("message", "")
        except ValueError:
            msg = r.text[:200]
        raise AIUnavailable(f"Gemini returned {r.status_code}: {msg[:300]}")
    try:
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        data = json.loads(text)
    except (KeyError, IndexError, ValueError) as e:
        raise AIUnavailable("Gemini reply was not valid JSON") from e
    if not isinstance(data, dict):
        raise AIUnavailable("Gemini reply had the wrong shape")
    return data


def fallback_reply(message: str, context: dict, reason: str) -> dict:
    """Rule-based answer used when the AI isn't connected or fails. Still uses the real checks."""
    asked = context["asked_about"]
    if asked:
        courses = [{"code": a["code"], "reason": (
            "Prerequisites look met based on what you entered." if a["status"] in ("met", "no_prereqs")
            else "Not yet: " + "; ".join(a["missing"]))} for a in asked]
        intro = "Here is what our prerequisite check says about the course(s) you mentioned."
        title = "Prerequisite check"
    else:
        p = context["placement_progress"]
        courses = [{"code": e["code"], "reason": f"Counts toward {e['requirement']}, and you meet its prerequisites."}
                   for e in context["eligible_next"][:4]]
        intro = (f"You've finished {p['done']} of {p['total']} ECE placement requirements. "
                 "These required courses are ones you're ready for next.")
        title = "Courses you're ready for next"
    return {"title": title, "intro": intro + " (The AI isn't connected right now, so this answer comes from rule checks only.)",
            "ai_error": reason,
            "courses": courses,
            "follow": ["What do I still need for ECE placement?", "Can I take E E 215 next quarter?",
                       "Build a balanced 15-credit quarter"]}
