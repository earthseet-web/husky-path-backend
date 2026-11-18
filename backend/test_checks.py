"""Run with:  pytest -q   (from the backend/ folder)"""
from fastapi.testclient import TestClient

import ai
import app as app_module
import checks

FIRST_YEAR = {"completed": "MATH 124 3.5, CHEM 142, ENGR 101", "in_progress": "MATH 125, CSE 121, ENGL 131", "credits": 15}


def student(profile):
    return checks.student_from_profile(profile)


# ---------- input parsing

def test_normalize_codes():
    assert checks.normalize_code("ee215") == "E E 215"
    assert checks.normalize_code("EE 215") == "E E 215"
    assert checks.normalize_code("inde 315") == "IND E 315"
    assert checks.normalize_code("math124") == "MATH 124"
    assert checks.normalize_code("hello") is None


def test_grades_parsed():
    s = student({"completed": "MATH 124 3.5, CHEM 142"})
    assert s.completed == {"MATH 124": 3.5, "CHEM 142": None}


# ---------- prerequisites

def test_ee215_blocked_without_physics():
    s = student({"completed": "MATH 124, MATH 125, MATH 126, MATH 207"})
    r = checks.prereq_status("E E 215", s)
    assert r["status"] == "not_met"
    assert any("PHYS 122" in m for m in r["missing"])


def test_ee215_ok_with_concurrent_math207():
    # MATH 207 may be taken at the same time as E E 215
    s = student({"completed": "MATH 126, PHYS 122"})
    assert checks.prereq_status("E E 215", s, planned={"MATH 207"})["status"] == "met"
    assert checks.prereq_status("E E 215", s)["status"] == "not_met"


def test_in_progress_counts_for_next_quarter():
    s = student({"completed": "PHYS 121", "in_progress": "MATH 125"})
    assert checks.prereq_status("PHYS 122", s)["status"] == "met"


def test_minimum_grade_enforced():
    low = student({"completed": "MATH 124 1.5"})
    ok = student({"completed": "MATH 124 2.0"})
    assert checks.prereq_status("MATH 125", low)["status"] == "not_met"
    assert checks.prereq_status("MATH 125", ok)["status"] == "met"


def test_missing_grade_is_flagged_not_blocked():
    r = checks.prereq_status("MATH 125", student({"completed": "MATH 124"}))
    assert r["status"] == "met" and any("grade not provided" in n for n in r["notes"])


def test_unknown_course():
    assert checks.prereq_status("CSE 999", student({}))["status"] == "unknown_course"


# ---------- placement and planning

def test_placement_progress_first_year():
    p = checks.placement_progress(student(FIRST_YEAR))
    status = {i["id"]: i["status"] for i in p["items"]}
    assert status["engr101"] == "done" and status["chem"] == "done"
    assert status["calc2"] == "in_progress" and status["phys1"] == "missing"
    assert p["done"] == 3 and p["total"] == 8


def test_eligible_next_first_year_puts_placement_first():
    nxt = [e["code"] for e in checks.eligible_next(student(FIRST_YEAR))]
    assert nxt[:2] == ["MATH 126", "PHYS 121"]
    assert not any(c.startswith("E E 3") or c.startswith("E E 4") for c in nxt)


def test_check_plan_credits():
    r = checks.check_plan(student(FIRST_YEAR), ["MATH 126", "PHYS 121", "CSE 122"])
    assert r["total_credits"] == 14 and "fits" in r["workload"]


# ---------- API (with a fake AI so no key or network is needed)

client = TestClient(app_module.app)


def test_health_and_courses():
    assert client.get("/health").json()["courses"] > 100
    assert client.get("/courses/ee215").json()["code"] == "E E 215"
    assert client.get("/courses/CSE 999").status_code == 404


def test_chat_without_key_uses_rule_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post("/chat", json={"message": "What should I take next quarter?", "profile": FIRST_YEAR}).json()
    assert r["source"] == "fallback"
    assert [c["code"] for c in r["cards"]][:2] == ["MATH 126", "PHYS 121"]


def test_chat_drops_invented_courses(monkeypatch):
    def fake_model(prompt):
        assert "ONLY the courses" in prompt
        return {"title": "Plan", "intro": "Try these.",
                "courses": [{"code": "PHYS 121", "reason": "Placement."}, {"code": "E E 999", "reason": "Made up."}],
                "follow": ["Next?"]}
    monkeypatch.setattr(ai, "call_model", fake_model)
    r = client.post("/chat", json={"message": "help", "profile": FIRST_YEAR}).json()
    assert r["source"] == "ai"
    assert [c["code"] for c in r["cards"]] == ["PHYS 121"]
    assert "E E 999" in r["intro"]


def test_chat_card_warns_when_prereqs_missing(monkeypatch):
    monkeypatch.setattr(ai, "call_model", lambda p: {"title": "t", "intro": "i",
                                                      "courses": [{"code": "EE 215", "reason": "r"}]})
    card = client.post("/chat", json={"message": "Can I take EE 215?", "profile": FIRST_YEAR}).json()["cards"][0]
    assert any("Prerequisites not met" in w for w in card["warns"])


# ---------- Gemini call handling (httpx is faked; no network)

class _Resp:
    def __init__(self, code, payload):
        self.status_code, self._p = code, payload
        self.text = __import__("json").dumps(payload)

    def json(self):
        return self._p


def test_retries_without_thinking_if_model_rejects_it(monkeypatch):
    calls = []
    good = {"candidates": [{"content": {"parts": [{"text": '{"title":"t","intro":"i","courses":[]}'}]}}]}

    def fake_post(url, headers, json, timeout):
        calls.append("thinkingConfig" in json["generationConfig"])
        if json["generationConfig"].get("thinkingConfig"):
            return _Resp(400, {"error": {"message": "thinking_level is not supported"}})
        return _Resp(200, good)

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setattr(ai.httpx, "post", fake_post)
    assert ai.call_model("hi")["title"] == "t"
    assert calls == [True, False]


def test_timeout_gives_clear_message(monkeypatch):
    def slow(*a, **k):
        raise ai.httpx.ReadTimeout("slow")
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setattr(ai.httpx, "post", slow)
    try:
        ai.call_model("hi")
        assert False
    except ai.AIUnavailable as e:
        assert "longer than" in str(e)


# ---------- first-year guidance

def test_first_year_not_offered_ee_courses():
    s = student(FIRST_YEAR | {"major": "Engineering Undeclared, aiming for ECE"})
    assert not s.in_major
    assert not any(e["code"].startswith("E E") for e in checks.eligible_next(s))


def test_ece_major_gets_ee_core():
    s = student({"major": "Electrical and Computer Engineering",
                 "completed": "MATH 124, MATH 125, MATH 126, CHEM 142, PHYS 121, PHYS 122, CSE 121, CSE 122, MATH 207"})
    assert s.in_major
    assert any(e["code"].startswith("E E") for e in checks.eligible_next(s))


def test_card_warns_first_year_about_ee271_and_credit_total(monkeypatch):
    monkeypatch.setattr(ai, "call_model", lambda p: {"title": "t", "intro": "i", "courses": [
        {"code": "MATH 126", "reason": "r"}, {"code": "PHYS 121", "reason": "r"},
        {"code": "E E 271", "reason": "r"}, {"code": "MATH 207", "reason": "r"}]})
    r = client.post("/chat", json={"message": "plan", "profile": FIRST_YEAR | {"major": "Engineering Undeclared"}}).json()
    ee = next(c for c in r["cards"] if c["code"] == "E E 271")
    assert "year 3" in ee["warns"][0]
    assert r["total_credits"] == 19 and "workload_warning" in r


# ---------- review fixes (2026-11-17)

ALMOST_PLACED = {"major": "Engineering Undeclared, aiming for ECE",
                 "completed": "MATH 124 3.5, MATH 125 3.2, CHEM 142, ENGR 101, ENGL 131",
                 "in_progress": "MATH 126, PHYS 121, CSE 121", "credits": 15}
ML_STUDENT = {"major": "Electrical and Computer Engineering",
              "completed": "MATH 124, MATH 125, MATH 126, MATH 207, MATH 208, CHEM 142, PHYS 121, PHYS 122, "
                           "CSE 121, CSE 122, CSE 123, E E 215, E E 241",
              "in_progress": "E E 242, E E 271", "credits": 15}


def test_placement_summary_counts_cse121_as_enough():
    sm = checks.placement_summary(student(ALMOST_PLACED))
    assert sm["still_needed"] == []
    assert "will be complete once the in-progress courses finish" in sm["verdict"]


def test_in_progress_cards_flagged_and_not_counted(monkeypatch):
    monkeypatch.setattr(ai, "call_model", lambda p: {"title": "t", "intro": "i", "courses": [
        {"code": "MATH 126", "reason": "r"}, {"code": "PHYS 121", "reason": "r"},
        {"code": "CSE 121", "reason": "r"}, {"code": "PHYS 122", "reason": "r"}]})
    r = client.post("/chat", json={"message": "status", "profile": ALMOST_PLACED}).json()
    assert "You're taking this now." in r["cards"][0]["warns"]
    assert r["total_credits"] == 5 and "workload_warning" not in r


def test_ml_student_sees_ml_electives_now():
    codes = [e["code"] for e in checks.eligible_electives(student(ML_STUDENT))]
    assert "E E 344" in codes and "E E 345" in codes


def test_label_for_in_major_student_is_not_placement():
    s = student(ML_STUDENT)
    assert checks.requirement_label("PHYS 123", s) == "Sciences"
    assert checks.requirement_label("PHYS 123", student(FIRST_YEAR)) == "ECE placement"
