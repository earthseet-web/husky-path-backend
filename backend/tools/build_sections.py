"""Builds data/sections_winter2027.json from the team's file (data/source/team_ece_winter2027.json).

Times like "MWF 9:30-10:20" are parsed into days and minutes after midnight. UW times have no AM/PM:
hours 7-11 are morning, 12 is noon, and 1-6 are afternoon.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import checks  # noqa: E402

SRC = HERE / "data" / "source" / "team_ece_winter2027.json"
OUT = HERE / "data" / "sections_winter2027.json"
DAY_RE = re.compile(r"Th|M|T|W|F")


def minutes(hhmm: str) -> int:
    h, m = (int(x) for x in hhmm.split(":"))
    if h < 7:
        h += 12
    return h * 60 + m


def parse(time: str):
    m = re.match(r"^\s*([MTWThF]+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*$", time)
    if not m:
        raise ValueError(f"Can't read time: {time!r}")
    days = DAY_RE.findall(m.group(1))
    start, end = minutes(m.group(2)), minutes(m.group(3))
    if end <= start:
        end += 12 * 60
    return days, start, end


def main():
    src = json.loads(SRC.read_text())
    out = []
    for s in src["sections"]:
        code = checks.normalize_code(s["code"])
        if code not in checks.COURSES:
            raise SystemExit(f"Section for unknown course {s['code']}")
        days, start, end = parse(s["time"])
        out.append({"code": code, "quarter": "Winter 2027", "section": s["section"], "sln": s["line_number"],
                    "days": days, "start": start, "end": end, "time": s["time"], "instructor": s["instructor"]})
    short = {"Autumn": "A", "Winter": "W", "Spring": "Sp", "Summer": "S"}
    offered_fill = {}
    for c in src["courses"]:
        code = checks.normalize_code(c["code"])
        if code in checks.COURSES and not checks.COURSES[code].get("offered") and c.get("offered"):
            offered_fill[code] = "".join(short[q] for q in c["offered"] if q in short)
    OUT.write_text(json.dumps({
        "source": "Team-provided Winter 2027 sections (from the UW Time Schedule), received 2026-11-17. "
                  "Not independently verified: the Time Schedule requires a UW NetID.",
        "quarter": "Winter 2027", "sections": out,
        "offered_fill": offered_fill,
        "offered_fill_note": "Usual quarters from the team's file, used only where the UW catalog lists none."}, indent=1) + "\n")
    print(f"wrote {len(out)} sections for {len({s['code'] for s in out})} courses to {OUT.name}")


if __name__ == "__main__":
    main()
