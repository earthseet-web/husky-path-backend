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
- **Section times, instructors, seats:** not in the catalog. The backend doesn't provide them.
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
