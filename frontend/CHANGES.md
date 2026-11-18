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
- **Course details:** real UW courses show the catalog description, credits, prerequisites, usual quarters
  and a catalog link. Fictional section times, instructors and syllabi aren't shown for real courses.
- **Plan and weekly schedule:** real courses can be added to the plan and count toward the credit total.
  They aren't drawn on the calendar because real section times aren't in the prototype; a note says so.
- **Degree progress:** calculated by `POST /check` from the student's courses against UW ECE requirements,
  replacing the fictional Computer Science audit (still available if the backend is down).
- **Starting student:** a fictional first-year Engineering Undeclared student aiming for ECE, unless the
  student has already saved their own profile in the browser.

## Known gaps

- `index.html` loads `taste.css`, which isn't in Adeline's repo (the browser shows a harmless 404).
- Transcript import still needs internet for PDFs (it loads a PDF reader from a CDN); pasted text works offline.
