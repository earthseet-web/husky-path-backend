"""Husky Path backend: the AI course-planning assistant for UW ECE (demo prototype).

Run:  uvicorn app:app --reload        (from the backend/ folder)
Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).parent / ".env")

import ai  # noqa: E402  (load .env before reading keys)
import checks  # noqa: E402

app = FastAPI(title="Husky Path backend", version="0.1.0",
              description="Demo prototype. Course data from the UW catalog; always confirm in MyPlan and with an adviser.")

# The front end may be opened straight from a file (origin "null") or another port, so allow all origins.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------------------------------------------------------------- request shapes

class Profile(BaseModel):
    name: str | None = None
    major: str | None = None
    quarter: str | None = None
    credits: int | float | str | None = 15
    completed: Any = Field(default="", description="'CSE 121, MATH 124 3.5' or a list of codes / {code, grade}")
    in_progress: Any = ""
    goals: str | None = None
    english_comp_done: bool | None = None


class ChatRequest(BaseModel):
    message: str
    profile: Profile = Profile()
    preferences: list[str] = []
    plan: list[str] = Field(default=[], description="Course codes in the student's draft for the target quarter")
    history: list[dict] = Field(default=[], description="Earlier turns: [{role: 'user'|'assistant', text: '...'}]")


class CheckRequest(BaseModel):
    profile: Profile = Profile()
    plan: list[str] = []


# ---------------------------------------------------------------- helpers

QUARTERS = {"A": "Autumn", "W": "Winter", "Sp": "Spring", "S": "Summer"}


def quarters_text(code: str | None) -> str:
    return ", ".join(QUARTERS[q] for q in re.findall(r"Sp|A|W|S", code or ""))


def course_card(code: str, reason: str, student: checks.Student) -> dict:
    c = checks.COURSES[code]
    st = checks.prereq_status(code, student)
    fits, warns = [], []
    label = checks.requirement_label(code)
    if label != "Not a listed ECE requirement":
        fits.append(f"Counts toward: {label}")
    if code in student.completed:
        warns.append("You've already completed this course.")
    elif st["status"] == "met":
        fits.append("Prerequisites met (based on what you entered)")
    elif st["status"] == "no_prereqs":
        fits.append("No prerequisites listed")
    else:
        warns.append("Prerequisites not met yet: " + "; ".join(st["missing"]))
    note = checks.timing_note(code, student)
    if note:
        warns.insert(0, note)
    warns += st["notes"]
    warns.append(f"Usually offered: {quarters_text(c['offered'])} (not confirmed for a specific quarter)" if c.get("offered")
                 else "Quarters offered not listed in the catalog; check MyPlan")
    credits = c["credits"] if c["credits"] == c["credits_max"] else f"{c['credits']}-{c['credits_max']}"
    return {"code": code, "title": c["title"], "credits": credits, "reason": reason, "reqLabel": label,
            "description": c["description"], "prereq_text": c["prereq_text"], "url": c["url"],
            "offered": c.get("offered"), "fits": fits, "warns": warns}


def shape_reply(raw: dict, student: checks.Student, source: str) -> dict:
    """Validate the AI's answer: keep only real course codes from our data, attach checked facts."""
    cards, dropped = [], []
    for item in (raw.get("courses") or [])[:6]:
        if not isinstance(item, dict):
            continue
        code = checks.normalize_code(item.get("code", ""))
        if code in checks.COURSES and all(cd["code"] != code for cd in cards):
            cards.append(course_card(code, str(item.get("reason", ""))[:400], student))
        elif item.get("code"):
            dropped.append(str(item.get("code")))
    intro = str(raw.get("intro", ""))[:1200]
    if dropped:
        intro += f" (Removed {', '.join(dropped)}: not in our verified course data.)"
    follow = [str(f)[:120] for f in (raw.get("follow") or []) if f][:3]
    return {"title": str(raw.get("title", "Here's what I found."))[:200], "intro": intro, "cards": cards,
            "follow": follow, "source": source,
            "disclaimer": "Demo prototype. Confirm requirements in DARS/MyPlan and with an ECE adviser."}


# ---------------------------------------------------------------- endpoints

@app.get("/health")
def health():
    return {"ok": True, "courses": len(checks.COURSES),
            "ai_connected": bool(os.getenv("GEMINI_API_KEY", "").strip()),
            "model": os.getenv("GEMINI_MODEL", ai.DEFAULT_MODEL)}


@app.get("/courses")
def list_courses(search: str = ""):
    q = search.lower().strip()
    out = [{"code": c["code"], "title": c["title"], "credits": c["credits"], "label": checks.requirement_label(c["code"])}
           for c in checks.COURSES.values()
           if not q or q in c["code"].lower() or q in c["title"].lower() or q in c["description"].lower()]
    return {"count": len(out), "courses": out}


@app.get("/courses/{code}")
def get_course(code: str):
    norm = checks.normalize_code(code)
    if norm not in checks.COURSES:
        raise HTTPException(404, f"{code} is not in our ECE course data.")
    return {**checks.COURSES[norm], "requirement": checks.requirement_label(norm)}


@app.post("/check")
def check(req: CheckRequest):
    s = checks.student_from_profile(req.profile.model_dump())
    return {"placement": checks.placement_progress(s),
            "graduation": checks.graduation_progress(s),
            "eligible_next": checks.eligible_next(s),
            "plan": checks.check_plan(s, req.plan) if req.plan else None}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Please type a question.")
    profile = req.profile.model_dump()
    s = checks.student_from_profile(profile)
    plan = [c for c in (checks.normalize_code(p) for p in req.plan) if c]
    context = ai.build_context(req.message, profile, s, req.preferences, plan)
    started = time.monotonic()
    try:
        raw = ai.call_model(ai.build_prompt(req.message, context, req.history))
        source = "ai"
    except ai.AIUnavailable as e:
        raw = ai.fallback_reply(req.message, context, str(e))
        source = "fallback"
    reply = shape_reply(raw, s, source)
    reply["seconds"] = round(time.monotonic() - started, 1)
    if raw.get("ai_error"):
        reply["ai_error"] = raw["ai_error"]  # for debugging; the front end doesn't need to show it
    reply["placement"] = {"done": context["placement_progress"]["done"], "total": context["placement_progress"]["total"]}
    total = sum(checks.credits_of(cd["code"]) for cd in reply["cards"])
    reply["total_credits"] = total
    if reply["cards"] and total > s.target_credits + 2:
        reply["workload_warning"] = (f"These courses add up to {total} credits, more than your ~{s.target_credits}-credit "
                                     "target. Pick the ones that matter most for placement.")
    return reply


# Optional: serve the front end from the same address (set FRONTEND_DIR in .env).
_frontend = os.getenv("FRONTEND_DIR", "").strip()
if _frontend and Path(_frontend).is_dir():
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")
