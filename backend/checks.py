"""Rule checks that have a right answer: prerequisites, credits, placement and requirement progress.

No AI here. The AI only explains results that this file computes.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text())


COURSES: dict[str, dict] = {c["code"]: c for c in _load("ece_courses.json")["courses"]}
REQUIREMENTS: dict = _load("ece_requirements.json")
SAMPLE_PLAN: dict = _load("ece_sample_plan.json")

# Department prefixes that are written with a space inside them at UW.
_SPACED_DEPTS = {"EE": "E E", "INDE": "IND E", "GENST": "GEN ST", "BBIO": "B BIO", "TBIOL": "T BIOL", "CHEME": "CHEM E"}
_CODE_RE = re.compile(r"^([A-Z&][A-Z& ]{0,9}?)\s*(\d{3}[A-Z]?)$")


def normalize_code(raw: str) -> str | None:
    """'ee215', 'EE 215', 'E E 215' -> 'E E 215'. Returns None if it doesn't look like a course code."""
    s = re.sub(r"\s+", " ", str(raw).upper().strip())
    m = _CODE_RE.match(s)
    if not m:
        return None
    dept = m.group(1).strip()
    squashed = dept.replace(" ", "")
    dept = _SPACED_DEPTS.get(squashed, dept)
    return f"{dept} {m.group(2)}"


# ---------------------------------------------------------------- student input

@dataclass
class Student:
    completed: dict[str, float | None] = field(default_factory=dict)  # code -> grade (None = not given)
    in_progress: set[str] = field(default_factory=set)
    english_comp_done: bool = False
    target_credits: int = 15
    in_major: bool = False  # admitted/placed into ECE (otherwise: working toward placement)

    def has(self, code: str, min_grade: float | None = None, include_in_progress: bool = False) -> bool:
        if code in self.completed:
            grade = self.completed[code]
            return min_grade is None or grade is None or grade >= min_grade
        return include_in_progress and code in self.in_progress

    def grade_unknown(self, code: str) -> bool:
        return code in self.completed and self.completed[code] is None


def _parse_course_list(value) -> list[tuple[str, float | None]]:
    """Accepts 'CSE 121, MATH 124 3.5' or [{'code': 'CSE 121', 'grade': 3.5}] or ['CSE 121']."""
    out: list[tuple[str, float | None]] = []
    if not value:
        return out
    if isinstance(value, str):
        value = [p for p in re.split(r"[,;\n]+", value) if p.strip()]
    for item in value:
        grade = None
        if isinstance(item, dict):
            raw, grade = item.get("code", ""), item.get("grade")
        else:
            raw = str(item)
            m = re.match(r"^(.*?\d{3}[A-Z]?)\s+([0-4](?:\.\d)?)\s*$", raw.strip(), re.I)
            if m:
                raw, grade = m.group(1), float(m.group(2))
        code = normalize_code(raw)
        if code:
            out.append((code, float(grade) if grade not in (None, "") else None))
    return out


def student_from_profile(profile: dict | None) -> Student:
    profile = profile or {}
    s = Student()
    for code, grade in _parse_course_list(profile.get("completed")):
        s.completed[code] = grade
    s.in_progress = {c for c, _ in _parse_course_list(profile.get("in_progress"))} - set(s.completed)
    comp = profile.get("english_comp_done")
    s.english_comp_done = bool(comp) or "ENGL 131" in s.completed
    try:
        s.target_credits = int(float(profile.get("credits") or 15))
    except (TypeError, ValueError):
        s.target_credits = 15
    major = str(profile.get("major") or "").lower()
    says_ece = bool(re.search(r"\bece\b|electrical", major))
    not_yet = any(w in major for w in ("undeclared", "aiming", "pre-", "intended", "want"))
    s.in_major = s.has("E E 215", include_in_progress=True) or (says_ece and not not_yet)
    return s


# ---------------------------------------------------------------- prerequisites

def _option_met(option, s: Student, planned: set[str], conc_ok: bool, min_grade):
    codes = option if isinstance(option, list) else [option]
    for c in codes:
        if s.has(c, min_grade):
            continue
        if conc_ok and (c in planned or c in s.in_progress):
            continue
        return False
    return True


def _option_text(option) -> str:
    return " + ".join(option) if isinstance(option, list) else option


def prereq_status(code: str, s: Student, planned: set[str] | None = None) -> dict:
    """Is the student ready to take `code` next quarter?

    In-progress courses count as done (they finish before next quarter). Courses in `planned`
    (the same quarter) only count where the catalog allows taking them concurrently.
    """
    planned = set(planned or ())
    course = COURSES.get(code)
    if not course:
        return {"code": code, "status": "unknown_course", "missing": [], "notes": [
            f"{code} is not in our ECE dataset, so its prerequisites can't be checked."]}
    future = Student(completed=dict(s.completed), in_progress=set(),
                     english_comp_done=s.english_comp_done, target_credits=s.target_credits)
    for c in s.in_progress:
        future.completed.setdefault(c, None)

    missing, notes = [], []
    for group in course["prereq"]:
        if any(_option_met(o, future, planned, group["concurrent_ok"], group["min_grade"]) for o in group["any_of"]):
            # Met. Flag grades we couldn't verify.
            if group["min_grade"]:
                for o in group["any_of"]:
                    for c in (o if isinstance(o, list) else [o]):
                        if future.grade_unknown(c):
                            notes.append(f"Needs a minimum grade of {group['min_grade']} in {c}; grade not provided.")
            continue
        text = " or ".join(_option_text(o) for o in group["any_of"])
        if group["min_grade"]:
            text += f" (minimum grade {group['min_grade']})"
        if group["concurrent_ok"]:
            text += " (may be taken at the same time)"
        if group.get("alt"):
            text += f"; or {group['alt']}"
        missing.append(text)
    if course.get("recommended"):
        notes.append(f"Recommended first: {course['recommended']}.")
    if course.get("notes"):
        notes.append(course["notes"])
    status = "no_prereqs" if not course["prereq"] else ("met" if not missing else "not_met")
    return {"code": code, "status": status, "missing": missing, "notes": notes,
            "prereq_text": course["prereq_text"]}


# ---------------------------------------------------------------- requirements

def _item_status(item: dict, s: Student) -> dict:
    t = item["type"]
    mg = item.get("min_grade")
    result = {"id": item["id"], "label": item["label"], "status": "missing", "detail": ""}
    if t == "one_of":
        done = [c for c in item["courses"] if s.has(c, mg)]
        ip = [c for c in item["courses"] if c in s.in_progress]
        low = [c for c in item["courses"] if c in s.completed and not s.has(c, mg)]
        if done:
            result.update(status="done", detail=f"Completed {done[0]}")
        elif ip:
            result.update(status="in_progress", detail=f"{ip[0]} in progress")
        elif low:
            result.update(status="missing", detail=f"{low[0]} grade is below the {mg} minimum")
    elif t == "all":
        left = [c for c in item["courses"] if not s.has(c, mg)]
        ip = [c for c in left if c in s.in_progress]
        if not left:
            result.update(status="done")
        elif len(ip) == len(left):
            result.update(status="in_progress", detail=", ".join(ip) + " in progress")
        else:
            result["detail"] = "Still needs " + ", ".join(c for c in left if c not in ip)
    elif t == "sequence":
        best = None
        for opt in item["options"]:
            left = [c for c in opt if not s.has(c)]
            if best is None or len(left) < len(best[1]):
                best = (opt, left)
        opt, left = best
        ip = [c for c in left if c in s.in_progress]
        if not left:
            result.update(status="done", detail="Completed " + ", ".join(opt))
        elif len(ip) == len(left) and len(left) < len(opt):
            result.update(status="in_progress", detail=", ".join(ip) + " in progress")
        else:
            result["detail"] = "Still needs " + ", ".join(c for c in left if c not in ip)
            if len(left) < len(opt):
                result["status"] = "partial"
    elif t == "category":
        if item.get("category") == "english_comp" and s.english_comp_done:
            result.update(status="done")
        elif item.get("category") == "english_comp" and any(c in s.in_progress for c in item.get("known_courses", [])):
            result.update(status="in_progress")
        else:
            result.update(status="not_tracked", detail="Check your DARS audit; this demo doesn't track gen-ed categories.")
    elif t in ("electives", "advisor"):
        result.update(status="not_tracked", detail="Plan this with an ECE adviser.")
    return result


def placement_progress(s: Student) -> dict:
    p = REQUIREMENTS["placement"]
    items = [_item_status(i, s) for i in p["items"]]
    done = sum(i["status"] == "done" for i in items)
    return {"label": p["label"], "deadline": p["deadline"], "note": p["min_grade_note"],
            "done": done, "total": len(items), "items": items}


def graduation_progress(s: Student) -> list[dict]:
    return [{"group": grp["group"], "items": [_item_status(i, s) for i in grp["items"]]}
            for grp in REQUIREMENTS["graduation"]]


# ---------------------------------------------------------------- planning helpers

def _plan_order() -> dict[str, int]:
    order, n = {}, 0
    for yr in SAMPLE_PLAN["years"]:
        for q in ("autumn", "winter", "spring"):
            for entry in yr[q]:
                for code in re.findall(r"[A-Z][A-Z ]*?\s\d{3}", entry["item"]):
                    order.setdefault(code.strip(), n)
            n += 1
    return order


PLAN_ORDER = _plan_order()


def _requirement_courses() -> dict[str, str]:
    """Courses that satisfy a placement/graduation item -> a short label for the card."""
    out = {}
    for grp in REQUIREMENTS["graduation"]:
        label = grp["group"].split(" (")[0]
        for item in grp["items"]:
            for c in item.get("courses", []):
                out.setdefault(c, label)
            for opt in item.get("options", []):
                for c in opt:
                    out.setdefault(c, label)
    for item in REQUIREMENTS["placement"]["items"]:
        for c in item.get("courses", []):
            out[c] = "ECE placement" if c not in out or out[c] in ("Sciences", "Mathematics") else out[c]
    return out


REQ_LABEL = _requirement_courses()


def requirement_label(code: str) -> str:
    if code in REQ_LABEL:
        return REQ_LABEL[code]
    if code.startswith("E E ") and int(code.split()[-1][:3]) >= 300:
        return "Advanced ECE elective"
    return "Not a listed ECE requirement"


def _level(code: str) -> int:
    try:
        return int(code.split()[-1][:3])
    except ValueError:
        return 0


def eligible_next(s: Student, limit: int = 12) -> list[dict]:
    """Placement and required courses the student still needs and is ready for next quarter,
    in sample-plan order (placement first)."""
    in_major = s.in_major
    items = [("ECE placement", i) for i in REQUIREMENTS["placement"]["items"]]
    items += [(grp["group"].split(" (")[0], i) for grp in REQUIREMENTS["graduation"] for i in grp["items"]]
    candidates = []
    for group_label, item in items:
        if item["type"] not in ("one_of", "all", "sequence"):
            continue
        if _item_status(item, s)["status"] in ("done", "in_progress"):
            continue
        if group_label in ("Advanced ECE Electives", "Capstone"):
            continue  # electives and capstone are planned with an adviser, later in the degree
        placement_first = 0 if group_label == "ECE placement" else 1
        if item["type"] == "sequence":
            # follow the option the student has started (or the first, standard one)
            opt = max(item["options"], key=lambda o: sum(s.has(c, include_in_progress=True) for c in o))
            pool = [next((c for c in opt if not s.has(c, include_in_progress=True)), None)] if opt else []
            pool = [c for c in pool if c]
        else:
            pool = item.get("courses", [])
        for code in pool:
            if code in s.completed or code in s.in_progress or code not in COURSES:
                continue
            if not in_major and (_level(code) >= 300 or code.startswith("E E ")):
                continue  # E E and upper-division courses come after placement into the major
            st = prereq_status(code, s)
            if st["status"] in ("met", "no_prereqs"):
                candidates.append((placement_first, PLAN_ORDER.get(code, 99), code, f"{group_label}: {item['label']}"))
                if item["type"] == "one_of":
                    break  # one option per requirement is enough
    candidates = [(p, o, c, l) for p, o, c, l in sorted(candidates)]
    candidates = [(c[1], c[2], c[3]) for c in candidates]
    seen, out = set(), []
    for _, code, label in candidates:
        if code not in seen:
            seen.add(code)
            out.append({"code": code, "requirement": label})
    return out[:limit]


def plan_year(code: str) -> int | None:
    """Year of the official sample plan in which this course appears (1-4), if it does."""
    idx = PLAN_ORDER.get(code)
    return idx // 3 + 1 if idx is not None else None


def timing_note(code: str, s: Student) -> str | None:
    """A gentle warning when a course is far ahead of where the student is."""
    if s.in_major:
        return None
    year = plan_year(code)
    if code.startswith("E E ") or _level(code) >= 300:
        when = f"year {year}" if year else "later in the degree"
        return f"The official ECE plan schedules this in {when}, after placement into ECE. Focus on placement courses first."
    return None


def credits_of(code: str) -> int:
    c = COURSES.get(code)
    return int(c["credits"]) if c else 0


def check_plan(s: Student, planned: list[str]) -> dict:
    """Check a proposed quarter: prerequisites for each course + total credits vs target."""
    codes = [c for c in (normalize_code(p) for p in planned) if c]
    pset = set(codes)
    results, total, unknown = [], 0, []
    for code in codes:
        st = prereq_status(code, s, planned=pset - {code})
        st["credits"] = credits_of(code)
        st["already_taken"] = code in s.completed
        total += st["credits"]
        if code not in COURSES:
            unknown.append(code)
        results.append(st)
    target = s.target_credits
    if total > target + 2:
        load = f"{total} credits is above your ~{target}-credit target."
    elif total < max(12, target - 3):
        load = f"{total} credits is below your ~{target}-credit target" + (" and under 12 (full-time)." if total < 12 else ".")
    else:
        load = f"{total} credits fits your ~{target}-credit target."
    return {"courses": results, "total_credits": total, "target_credits": target,
            "workload": load, "unknown_courses": unknown}
