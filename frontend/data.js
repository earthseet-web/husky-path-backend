/* Husky Path prototype — ALL DATA IN THIS FILE IS FICTIONAL SAMPLE DATA.
   Not real UW course, section, instructor, or student information. */
window.HP_DATA = {
  asOf: 'Sample data · as of Nov 10, 2026 (demo timestamp)',
  defaultPrefs: ['~15 credits', 'No Friday classes', 'Interested in design'],
  suggestedPrefs: ['No Friday classes', '~12 credits', 'Mornings preferred', 'In-person only',
    'Interested in history', 'Interested in music', 'Balance technical and writing-heavy courses'],

  // Times are minutes after midnight so conflicts can be checked. s = start, e = end.
  courses: [
    { code: 'CSE 311', title: 'Foundations of Computing I', credits: 4, req: 'core', reqLabel: 'CSE core', priority: 3, tags: ['logic', 'theory'],
      reason: 'Listed as a remaining CSE core course in the sample degree audit, and later core courses build on it.',
      caveat: 'Prerequisite check needed (sample: CSE 123 and MATH 126).',
      seats: 'Sample section open',
      description: 'Sample description: logic, set theory, induction, and the basics of formal reasoning used throughout computer science.',
      lecture: { id: 'A', days: ['M', 'W', 'F'], s: 810, e: 860, time: 'Mon · Wed · Fri, 1:30–2:20 PM', location: 'Cascade Hall 120', instructor: 'Dr. Imani Okafor (fictional)' },
      quiz: { id: 'AA', type: 'Quiz', days: ['Th'], s: 750, e: 800, time: 'Thu, 12:30–1:20 PM', location: 'Alder Lab 015', instructor: 'TA Priya N. (fictional)' },
      syllabus: ['Weeks 1–3: propositional and predicate logic', 'Weeks 4–6: proofs and induction', 'Weeks 7–10: sets, relations, finite automata', 'Grading (sample): homework 50%, midterm 20%, final 30%'] },
    { code: 'CSE 340', title: 'Interaction Programming', credits: 4, req: 'elective', reqLabel: 'CSE elective', priority: 2, tags: ['design', 'interfaces'],
      reason: 'May count toward the sample CSE elective credits and connects to an interest in design.',
      caveat: 'Majors-only restriction may apply (sample).',
      seats: 'Sample section open',
      description: 'Sample description: building interactive interfaces, event-driven programming, layout, and accessibility basics.',
      lecture: { id: 'A', days: ['T', 'Th'], s: 600, e: 680, time: 'Tue · Thu, 10:00–11:20 AM', location: 'Harbor Hall 105', instructor: 'Dr. Kofi Brandt (fictional)' },
      quiz: null,
      syllabus: ['Weeks 1–3: events, layout, and drawing', 'Weeks 4–7: input, undo, and accessibility', 'Weeks 8–10: final interface project', 'Grading (sample): projects 70%, reflections 30%'] },
    { code: 'DESIGN 166', title: 'Design Foundations', credits: 5, req: 'ah', reqLabel: 'Arts & Humanities', priority: 2, tags: ['design', 'studio'],
      reason: 'Could support the 9 remaining sample Arts & Humanities credits and matches an interest in design.',
      caveat: 'Studio course; materials fee may apply (sample).',
      seats: 'Sample section open',
      description: 'Sample description: studio introduction to visual design principles, composition, colour, and critique.',
      lecture: { id: 'A', days: ['M', 'W'], s: 750, e: 860, time: 'Mon · Wed, 12:30–2:20 PM', location: 'Foundry Studio 2', instructor: 'Prof. Mara Lindqvist (fictional)' },
      quiz: null,
      syllabus: ['Weeks 1–3: form and composition', 'Weeks 4–6: colour and typography', 'Weeks 7–10: portfolio project and critique', 'Grading (sample): studio projects 80%, participation 20%'] },
    { code: 'HSTAS 254', title: 'Modern China: Three Revolutions', credits: 5, req: 'ah', reqLabel: 'Arts & Humanities', priority: 2, tags: ['history', 'writing'],
      reason: 'An alternative sample Arts & Humanities option with a Tuesday/Thursday lecture pattern.',
      caveat: 'May count for A&H or Social Sciences, not both (sample rule).',
      seats: 'Sample section open',
      description: 'Sample description: survey of political, social, and cultural change in twentieth-century China.',
      lecture: { id: 'A', days: ['T', 'Th'], s: 630, e: 740, time: 'Tue · Thu, 10:30 AM–12:20 PM', location: 'Lakeview Hall 301', instructor: 'Dr. Wen Castellanos (fictional)' },
      quiz: { id: 'AA', type: 'Discussion', days: ['W'], s: 930, e: 980, time: 'Wed, 3:30–4:20 PM', location: 'Lakeview Hall 112', instructor: 'TA Jonah R. (fictional)' },
      syllabus: ['Weeks 1–4: late empire and republic', 'Weeks 5–7: revolution and reform', 'Weeks 8–10: contemporary legacies', 'Grading (sample): two essays 60%, discussion 15%, final 25%'] },
    { code: 'MUSIC 120', title: 'Survey of Music', credits: 3, req: 'ah', reqLabel: 'Arts & Humanities', priority: 1, tags: ['music'],
      reason: 'A lighter 3-credit sample option toward Arts & Humanities with no quiz section.',
      caveat: 'Hybrid format in this sample section.',
      seats: 'Sample section open',
      description: 'Sample description: listening-based introduction to musical styles and how to describe them.',
      lecture: { id: 'A', days: ['T', 'Th'], s: 810, e: 890, time: 'Tue · Thu, 1:30–2:50 PM', location: 'Rainier Hall 210', instructor: 'Dr. Elio Farrow (fictional)' },
      quiz: null,
      syllabus: ['Weeks 1–3: listening vocabulary', 'Weeks 4–7: styles and periods', 'Weeks 8–10: concert report', 'Grading (sample): listening quizzes 40%, reports 60%'] }
  ],

  // Fictional degree audit for the sample student "Jordan Lee".
  degree: {
    major: 'Computer Science (sample audit)',
    groups: [
      { id: 'intro', name: 'Introductory programming', required: 12,
        taken: [['CSE 121', 4, 'completed', 'Autumn 2025'], ['CSE 122', 4, 'completed', 'Winter 2026'], ['CSE 123', 4, 'completed', 'Spring 2026']],
        remaining: [] },
      { id: 'core', name: 'CSE core courses', required: 32,
        taken: [['CSE 351', 4, 'completed', 'Spring 2026'], ['CSE 333', 4, 'in progress', 'Autumn 2026']],
        remaining: ['CSE 311 (4)', 'CSE 312 (4)', 'CSE 331 (4)', 'CSE 332 (4)', 'CSE 341 (4)', 'CSE 344 (4)'] },
      { id: 'elective', name: 'CSE electives', required: 16,
        taken: [],
        remaining: ['16 credits of approved CSE electives'] },
      { id: 'math', name: 'Math & science', required: 33,
        taken: [['MATH 124', 5, 'completed', 'Autumn 2025'], ['MATH 125', 5, 'completed', 'Winter 2026'], ['MATH 126', 5, 'completed', 'Spring 2026'], ['PHYS 121', 5, 'completed', 'Spring 2026'], ['MATH 208', 4, 'in progress', 'Autumn 2026']],
        remaining: ['STAT 390 (4)', '5 credits of natural science'] },
      { id: 'ah', name: 'Arts & Humanities', required: 20,
        taken: [['DRAMA 101', 5, 'completed', 'Autumn 2025'], ['PHIL 120', 5, 'completed', 'Winter 2026'], ['ART H 100', 1, 'in progress', 'Autumn 2026']],
        remaining: ['9 credits of A&H-designated courses'] },
      { id: 'ssc', name: 'Social Sciences', required: 20,
        taken: [['ECON 200', 5, 'completed', 'Winter 2026'], ['PSYCH 101', 5, 'completed', 'Spring 2026'], ['GEOG 123', 5, 'in progress', 'Autumn 2026']],
        remaining: ['5 credits of Social Sciences courses'] }
    ]
  }
};
