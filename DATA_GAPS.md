# Data gaps and things to verify

The data was collected from public UW pages on 2026-11-16. Where a source didn't say something,
it was left blank instead of guessed. Please check these before demo day.

## Please spot-check (about 10 courses)

Course descriptions are short summaries. Prerequisites were copied from the catalog, but compare a few
against MyPlan, especially: E E 215, E E 242, E E 280, PHYS 122, MATH 126, CSE 123, E E 271, E E 331,
E E 418, E E 475.

## Not in the sources

- **E E 393 alternatives:** the department accepts a "department-approved alternative" but doesn't list any.
- **Pathways:** 13 ECE pathways exist (Machine Learning, Embedded Systems, and others), but the pathways page
  lists no courses. Not included in this demo.
- **Quarters offered:** most E E courses don't list offered quarters in the catalog. Cards say
  "check MyPlan" instead of guessing.
- **Winter 2027 sections** (37 sections for 25 courses: SLN, days, times, instructor) come from our team's file
  (`backend/data/source/team_ece_winter2027.json`). We couldn't verify them ourselves because the Time Schedule
  requires a UW NetID. The app labels them and tells students to confirm SLNs and seats in MyPlan.
  No locations, seats, quiz sections, or other quarters. Most 300/400-level E E courses have no Winter section in
  the file, so the app says "not in our Winter 2027 section list" for them.
- **English Composition:** only ENGL 131 is recognized automatically. Students can set
  `english_comp_done: true` in their profile for other approved courses.
- **Gen-ed categories (A&H, SSc, DIV, W):** not tracked; the app tells students to check DARS.
- **Exam and placement scores** (AP, chemistry placement, Guided Self-Placement): shown in prerequisite text,
  but the checker can't verify them.
- **Credit for AP courses:** students should enter UW equivalents (e.g. `MATH 124`) themselves.

## Courses named in prerequisites but not in our data

Students can still list them as completed, and the checker will count them, but the app can't describe them:
AMATH 301, AMATH 342, B BIO 200, BIOEN 460, BIOL 162, BIOL 200, CHEM 110, CSE 311, CSE 369, CSE 469,
CSE 474, E E 235, E E 341, E E 472, E E 485, MATH 307, MATH 308, MATH 394, MSE 351, PHYS 143, PHYS 324,
STAT 394, T BIOL 140. Also GEN ST 199 and ENGL 131 (requirements only).

## Conflicts between sources (what the app does)

| Topic | Conflict | App uses |
| --- | --- | --- |
| Placement deadline | July 15 (Autumn 2026 page) vs July 1 (older plan and DARS) | July 15 |
| E E 215 prerequisites | Plan page is shorter than the catalog | Catalog |
| Elective credits | 39 (admitted Autumn 2025+) vs 36 (earlier) | 39 |
| Gen-ed total | Header says 41 cr; NSc row says "to reach 45" | Shows both, refers to adviser |

## Where the team's Winter 2027 file disagrees with the UW catalog

The app uses the catalog for prerequisites and only takes **sections** (and "usually offered" quarters where the
catalog lists none: ENGR 101, CSE 163, E E 215, E E 241, E E 271, E E 393) from the team's file.
Please check these with the department:

| Course | Team file | UW catalog (used by the app) |
| --- | --- | --- |
| E E 280 | Offered Spring only | Autumn, Winter, Spring |
| E E 241 | CSE 121 counts as a prerequisite | CSE 122, 123, 142, 143, or 160 |
| MATH 208 | Requires MATH 126 | No prerequisite listed |
| CSE 122, CSE 123 | Require CSE 121, CSE 122 | Recommended, not required |
| CHEM 142 | No prerequisite | CHEM 110, placement exam, or AP Chemistry |
| IND E 315 | MATH 207 or AMATH 351 | Also MATH 135 or MATH 136 |
| E E 215 | MATH 126 + PHYS 122 + MATH 207 (concurrent) | Also allows MATH 136, MATH 307, AMATH 351, PHYS 142 |

The team's first file (25 mostly Computer Science courses) wasn't used: it's cut off mid-file, and its
prerequisites can't express "or".
