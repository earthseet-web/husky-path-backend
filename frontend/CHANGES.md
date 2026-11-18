# Front end: what changed from Adeline's version

This folder is Adeline's Husky Path front end
([Adelinezou/uw-schedule-chatbot-ai-collective-project](https://github.com/Adelinezou/uw-schedule-chatbot-ai-collective-project), commit `9ad8d7b`).
The first commit that added this folder is her code unchanged, so `git diff` against it shows every change.

## Files

| File | Change |
| --- | --- |
| `chat.js`, `data.js`, `enhancements.js`, `chat.css`, `enhancements.css` | **Unchanged** |
| `backend.js` | **New.** Connects the page to the backend (see below) |
| `backend.css` | **New.** Styles for the new parts (prerequisite line, source line, degree progress list) |
| `index.html` | Loads the two new files; text changed from the Computer Science sample to ECE; new "Courses in progress" field on the profile form |

## What `backend.js` does

- **Chat:** sends the question, profile, preferences, draft plan and recent conversation to `POST /chat`,
  and shows the AI's answer as course cards with prerequisites, warnings and a catalog link.
  If the backend can't be reached, it shows Adeline's scripted reply instead, with a note saying so.
- **Course details:** real UW courses show the catalog description, credits, prerequisites, usual quarters,
  a catalog link, and a Winter 2027 sections table (SLN, time, instructor, Rate My Professors link).
- **Plan and weekly schedule:** real courses use Winter 2027 sections (team data from the Time Schedule).
  Adding a course picks a section that doesn't overlap the rest of the plan; "Switch section" tries another.
  Her calendar, time-conflict warnings and Rate My Professors links work with the real times and instructors.
  Courses with no Winter section in the data say so and aren't drawn on the calendar.
- **Degree progress:** calculated by `POST /check` from the student's courses against UW ECE requirements,
  replacing the fictional Computer Science audit (still available if the backend is down).
- **Starting student:** a fictional first-year Engineering Undeclared student aiming for ECE, unless the
  student has already saved their own profile in the browser.

## Known gaps

- `index.html` loads `taste.css`, which isn't in Adeline's repo (the browser shows a harmless 404).
- Transcript import still needs internet for PDFs (it loads a PDF reader from a CDN); pasted text works offline.
