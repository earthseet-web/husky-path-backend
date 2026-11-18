/* Husky Path prototype UI. Sample data lives in data.js. Replies are scripted — no AI, no network. */
const D = window.HP_DATA;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const course = code => D.courses.find(c => c.code === code);
const DAY = { M: 'Mon', T: 'Tue', W: 'Wed', Th: 'Thu', F: 'Fri' };

let prefs = [...D.defaultPrefs];
let plan = [];            // course codes in the draft plan
let lastFocus = null;
const demo = new URLSearchParams(location.search).get('demo');   // screenshot/walkthrough preset

/* ---------- mock recommendation logic (deterministic, no rendering) ---------- */
const meetings = c => [c.lecture && { ...c.lecture, label: `${c.code} lecture ${c.lecture.id}` },
  c.quiz && { ...c.quiz, label: `${c.code} ${c.quiz.type.toLowerCase()} ${c.quiz.id}` }].filter(Boolean);
const fmt = m => `${((Math.floor(m / 60) + 11) % 12) + 1}:${String(m % 60).padStart(2, '0')}`;
function overlap(a, b) {
  const out = [];
  meetings(a).forEach(x => meetings(b).forEach(y => {
    const days = x.days.filter(d => y.days.includes(d)), s = Math.max(x.s, y.s), e = Math.min(x.e, y.e);
    if (days.length && s < e) out.push(`${x.label} and ${y.label} both meet ${days.map(d => DAY[d]).join(' and ')} between ${fmt(s)} and ${fmt(e)}`);
  }));
  return out;
}
function planConflicts(codes) {
  const out = [];
  codes.forEach((a, i) => codes.slice(i + 1).forEach(b => out.push(...overlap(course(a), course(b)))));
  return out;
}
const meetsFriday = c => meetings(c).some(m => m.days.includes('F'));

function recommend(text) {
  const q = text.toLowerCase();
  const noFri = prefs.some(p => /friday/i.test(p)) || /friday/.test(q);
  const allTags = [...new Set(D.courses.flatMap(c => c.tags))];
  const interests = allTags.filter(t => q.includes(t) || prefs.some(p => p.toLowerCase().includes(t)) || studentProfile.goals.toLowerCase().includes(t));
  const usedPrefs = prefs.filter(p => /friday/i.test(p) || allTags.some(t => p.toLowerCase().includes(t)) || (/credit/i.test(p) && /balanced|quarter/.test(q)));
  const notedPrefs = prefs.filter(p => !usedPrefs.includes(p));

  let list = D.courses.filter(c => !completedSet().has(c.code));
  if (/a&h|humanit|\barts\b/.test(q)) list = list.filter(c => c.req === 'ah');
  else if (/major|core|cse|computer/.test(q)) list = list.filter(c => c.req === 'core' || c.req === 'elective');
  const cr = q.match(/(\d)\s*(?:or|-|to)\s*(\d)\s*-?\s*credit/);
  if (cr) list = list.filter(c => c.credits >= +cr[1] && c.credits <= +cr[2]);
  if (/no quiz|without (a )?quiz/.test(q)) list = list.filter(c => !c.quiz);
  if (/light/.test(q)) list = list.filter(c => c.credits <= 4);

  const cards = list.map(c => {
    const fits = [], warns = [];
    const hit = c.tags.filter(t => interests.includes(t));
    let score = c.priority + hit.length * 2;
    if (hit.length) fits.push(`Matches interest: ${hit.join(', ')}`);
    if (noFri) { if (meetsFriday(c)) { score -= 5; warns.push('Meets on Friday — does not fit your “no Friday” preference'); } else fits.push('No Friday meetings'); }
    if (!c.quiz && /quiz/.test(q)) fits.push('No quiz section');
    plan.filter(p => p !== c.code).forEach(p => overlap(c, course(p)).forEach(o => { score -= 3; warns.push(`Time conflict with your draft: ${o}`); }));
    warns.push(c.caveat);
    return { code: c.code, score, fits, warns };
  }).sort((a, b) => b.score - a.score);

  let picked = cards.slice(0, 3), intro;
  if (/balanced|15|quarter/.test(q) && !cr) {
    const target = Number(studentProfile.credits) || 15;
    picked = []; let total = 0;
    cards.forEach(card => {
      const c = course(card.code);
      if (picked.length < 3 && total + c.credits <= target + 1 && !picked.some(p => overlap(c, course(p.code)).length)) { picked.push(card); total += c.credits; }
    });
    intro = `Here is one sample combination with no time conflicts between the courses: ${total} credits against your ~${target}-credit target.`;
  } else if (!picked.length) {
    return { title: 'No sample courses match that yet.', intro: 'The small sample catalog has nothing that fits all of those constraints. Try relaxing one, or remove a preference.', cards: [], follow: ['Find a course that counts for A&H', 'Help me make progress on my major'] };
  } else if (/a&h|humanit|\barts\b/.test(q)) intro = 'Here are sample options related to the Arts & Humanities goal, with the reason each may fit and what to verify.';
  else intro = 'Based on the sample degree progress, here are a few directions to discuss. Requirement fit and schedule checks are shown separately so you can verify each one.';

  if (usedPrefs.length) intro += ` Applied from your preferences: ${usedPrefs.join(', ')}.`;
  if (notedPrefs.length) intro += ` Noted but not used by this scripted demo: ${notedPrefs.join(', ')}.`;
  return { title: 'Here are a few options to explore.', intro, cards: picked,
    follow: [noFri ? 'Show lighter workload options' : 'Keep Fridays open', 'Find a 3 or 4 credit course with no quiz sections', 'Build a balanced 15-credit quarter'] };
}

/* ---------- conversational academic advisor (demo-safe) ---------- */
function advisorResponse(text) {
  const q = text.toLowerCase();
  const asksMissing = /graduat|remaining|still need|need to take|degree requirements|finish my degree|还差|毕业|要求/.test(q);
  const asksWhen = /when (is|are|does|do)|offer|available|quarter|什么时候|哪一季|开课/.test(q);
  const asksSequence = /order|sequence|roadmap|pathway|first|next quarter|先修|顺序|先上|几年|规划/.test(q);
  if (!asksMissing && !asksWhen && !asksSequence) return null;

  const isDemoCS = /computer science/i.test(studentProfile.major);
  const factNote = `<p class="advisor-caveat">Demo only: the degree audit is a fictional Computer Science example. Course offering quarters are not verified, and the schedule contains sample sections only. Confirm requirements in DARS and offerings in UW MyPlan.</p>`;
  if (!isDemoCS) return {
    title: 'I can help you plan a path — first we need your program requirements.',
    html: `<p class="advisor-paragraph">Your profile says <b>${esc(studentProfile.major)}</b>, but this prototype only has a fictional Computer Science degree audit. I cannot calculate your remaining graduation requirements from your completed-course list alone.</p><div class="advisor-step"><b>What I need</b><span>Your program's requirement list or a reviewed DARS audit, plus verified prerequisites and quarter offerings. Once those are available, I can identify gaps and build a quarter-by-quarter sequence.</span></div>${factNote}`,
    follow: ['Show me a sample CS graduation roadmap', 'Help me choose courses from the demo catalog']
  };
  const groups = D.degree.groups.map(g => {
    const already = g.taken.reduce((n,t)=>n+t[1],0);
    const missing = Math.max(0,g.required-already);
    return { ...g, missing, examples: g.remaining.join(', ') };
  }).filter(g => g.missing > 0);
  let html = '';
  if (asksMissing) {
    html += `<p class="advisor-paragraph">Using the <b>fictional CS audit</b>, these are the requirement groups still incomplete. This is not a determination of what <i>you</i> need to graduate.</p><div class="advisor-requirements">` + groups.map(g => `<div><b>${esc(g.name)}</b><span>${g.missing} credits not yet completed${g.examples ? ` · sample examples: ${esc(g.examples)}` : ''}</span></div>`).join('') + '</div>';
  }
  if (asksSequence || asksMissing) {
    html += `<h3 class="advisor-section-title">Suggested study order (illustrative)</h3><div class="advisor-roadmap">
      <div class="advisor-step"><b>1 · Verify the starting point</b><span>Confirm that completed courses and the fictional audit agree. Check prerequisites and enrollment restrictions before choosing the next core course.</span></div>
      <div class="advisor-step"><b>2 · Take prerequisite-building courses first</b><span>In this sample catalog, CSE 311 lists CSE 123 and MATH 126 as prerequisite checks. Treat those as <i>unverified example requirements</i>, not UW registration advice.</span></div>
      <div class="advisor-step"><b>3 · Complete later core courses and electives</b><span>Sample audit lists CSE 312, 331, 332, 341, and 344 as remaining. Their prerequisite dependencies are not in this dataset, so the app cannot reliably order them yet.</span></div>
      <div class="advisor-step"><b>4 · Fit general education courses around the core</b><span>Use A&amp;H, Social Sciences, and science requirements to balance workload across quarters after verifying how courses count toward your degree.</span></div></div>`;
  }
  if (asksWhen || asksSequence) {
    html += `<h3 class="advisor-section-title">When are these courses offered?</h3><p class="advisor-paragraph">This dataset has <b>no verified Autumn/Winter/Spring/Summer offering history</b>. It only models fictional Winter 2027 meeting times for ${D.courses.length} sample courses. I should not claim that a course is offered in a specific quarter.</p><div class="advisor-step"><b>Next step</b><span>Check the <a target="_blank" rel="noopener noreferrer" href="https://myplan.uw.edu/">UW MyPlan</a> schedule for your target quarter. When verified quarter offerings are added to the dataset, this assistant can place courses into an actual multi-quarter roadmap.</span></div>`;
  }
  html += factNote;
  return { title: asksMissing ? 'Here is what the sample audit still shows as incomplete.' : asksSequence ? 'Here is a possible sequence and what needs verification.' : 'Quarter availability has not been verified yet.', html,
    follow: ['What do I still need to graduate?', 'Which quarter are these courses offered?', 'What order should I take my remaining courses?'] };
}

/* ---------- rendering ---------- */
function notify(text) { const t = $('toast'); t.textContent = text; t.classList.remove('hidden'); clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => t.classList.add('hidden'), 2200); }

function cardHTML(card) {
  const c = course(card.code), inPlan = plan.includes(c.code);
  return `<article class="recommendation"><div class="rec-top"><b>${c.code} · ${esc(c.title)}</b><small>${c.credits} credits</small></div>
    <p class="rec-why">${esc(c.reason)}</p>
    <div class="rec-tags"><span>${c.reqLabel}</span><span>Lec ${c.lecture.id} · ${c.lecture.time}</span>${c.quiz ? `<span>${c.quiz.type} ${c.quiz.id} · ${c.quiz.time}</span>` : '<span>No quiz section</span>'}<span class="seat">${c.seats} · demo</span></div>
    <ul class="rec-notes">${card.fits.map(f => `<li class="fit">✓ ${esc(f)}</li>`).join('')}${card.warns.map(w => `<li class="warn">⚠ ${esc(w)}</li>`).join('')}</ul>
    <div class="rec-actions"><span><button data-add="${c.code}">${inPlan ? '✓ Added to plan' : '＋ Add to plan'}</button><button data-details="${c.code}">View details</button></span><span class="source">Sample data · verify in MyPlan</span></div></article>`;
}

function addMessage(html, who) {
  const el = document.createElement('div');
  el.className = `message ${who}` + (who === 'assistant' ? ' assistant-answer' : '');
  el.innerHTML = who === 'user' ? `<div class="bubble user-bubble"></div><div class="user-avatar">J</div>` : `<div class="assistant-avatar">✳</div><div class="bubble assistant">${html}</div>`;
  if (who === 'user') el.firstChild.textContent = html;   // user text is never treated as HTML
  $('thread').appendChild(el);
  if (!demo) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  return el;
}

function send(text = $('messageInput').value.trim(), instant) {
  if (!text) { $('messageInput').focus(); return; }
  addMessage(text, 'user');
  $('messageInput').value = ''; $('messageInput').style.height = 'auto';
  const loading = addMessage('<p class="answer-intro loading">Checking sample courses…</p>', 'assistant');
  const reply = () => {
    loading.remove();
    const a = advisorResponse(text);
    if (a) {
      addMessage(`<b>${esc(a.title)}</b>${a.html}<div class="followup">Ask a follow-up:<br>${a.follow.map(f => `<button data-follow="${esc(f)}">${esc(f)}</button>`).join('')}</div>`, 'assistant');
    } else {
      const r = recommend(text);
      addMessage(`<b>${esc(r.title)}</b><p class="answer-intro">${esc(r.intro)}</p>${r.cards.map(cardHTML).join('')}<div class="followup">What next?<br>${r.follow.map(f => `<button data-follow="${esc(f)}">${esc(f)}</button>`).join('')}</div>`, 'assistant');
    }
  };
  instant ? reply() : setTimeout(reply, 450);
}

function renderPrefs() {
  $('prefChips').innerHTML = prefs.map((p, i) => `<span class="pref-chip">${esc(p)}<button data-unpref="${i}" aria-label="Remove preference: ${esc(p)}">×</button></span>`).join('') || '<p class="mini-note">No preferences yet.</p>';
}

function sectionLine(kind, s) { return `<div class="sect ${kind}"><i>${kind === 'lec' ? 'LEC' : s.type.toUpperCase().slice(0, 4)} ${s.id}</i><span>${s.time}<br>${esc(s.location)} · ${esc(s.instructor)}</span></div>`; }

function renderPlan() {
  $('emptyPlan').classList.toggle('hidden', plan.length > 0);
  $('planItems').innerHTML = plan.map(code => { const c = course(code); return `<div class="plan-course"><div class="plan-item"><b>${c.code}</b><span>${c.credits} cr</span><button data-details="${c.code}">View details</button><button data-remove="${c.code}" aria-label="Remove ${c.code}">×</button></div>${sectionLine('lec', c.lecture)}${c.quiz ? sectionLine('quiz', c.quiz) : '<div class="sect none">No quiz/discussion section (sample)</div>'}</div>`; }).join('');
  const conflicts = planConflicts(plan), total = plan.reduce((n, code) => n + course(code).credits, 0);
  $('planSummary').innerHTML = plan.length ? `<div class="plan-total">Draft total <b>${total} credits</b></div>` + conflicts.map(c => `<div class="conflict" role="alert"><b>⚠ Time conflict</b>${esc(c)}. You could not attend both — remove one or look for another section in MyPlan.</div>`).join('') : '';
  document.querySelectorAll('[data-add]').forEach(b => { b.textContent = plan.includes(b.dataset.add) ? '✓ Added to plan' : '＋ Add to plan'; });
}

/* ---------- modal (reused for course details, preferences, degree progress) ---------- */
function openModal(html, wide) {
  lastFocus = document.activeElement;
  $('modalBody').innerHTML = html;
  $('modal').firstElementChild.classList.toggle('wide', !!wide);
  $('modal').classList.remove('hidden');
  ($('modalBody').querySelector('input') || $('closeModal')).focus();
}
function closeModal() { $('modal').classList.add('hidden'); if (lastFocus) lastFocus.focus(); }

function openCourse(code) {
  const c = course(code);
  const row = (kind, s) => `<tr><th scope="row">${kind} ${s.id}</th><td>${s.time}</td><td>${esc(s.location)}</td><td>${esc(s.instructor)}</td></tr>`;
  openModal(`<span class="eyebrow">COURSE DETAILS</span><h2 id="modalTitle">${c.code} · ${esc(c.title)}</h2>
    <p class="sample-banner">Sample data — fictional description, sections, and instructors. Not from MyPlan.</p>
    <p class="detail-text">${esc(c.description)}</p>
    <p class="detail-text"><b>${c.credits} credits</b> · May support: ${c.reqLabel} · ${c.seats} (demo)</p>
    <table class="sections"><caption>Sections (sample)</caption><thead><tr><th>Section</th><th>Time</th><th>Location</th><th>Instructor</th></tr></thead><tbody>${row('Lecture', c.lecture)}${c.quiz ? row(c.quiz.type, c.quiz) : '<tr><td colspan="4">No quiz/discussion section in this sample.</td></tr>'}</tbody></table>
    <h3>Syllabus preview <small>(sample)</small></h3><ul class="syllabus">${c.syllabus.map(s => `<li>${esc(s)}</li>`).join('')}</ul>
    <p class="detail-text"><a href="#" data-placeholder>Open full syllabus ↗</a> <small>placeholder link — no real syllabus is connected</small></p>
    <p class="detail-text warn-text">⚠ ${esc(c.caveat)} Eligibility, seats, and degree applicability must be confirmed with UW.</p>
    <p class="disclaimer">${D.asOf}</p>
    <button class="primary" data-add="${c.code}">${plan.includes(c.code) ? '✓ Added to plan' : '＋ Add to plan'}</button>`, true);
}

function openPrefs() {
  openModal(`<span class="eyebrow">YOUR PREFERENCES</span><h2 id="modalTitle">Add a preference</h2>
    <form id="prefForm" class="pref-form"><label for="prefInput">Type your own</label><div><input id="prefInput" autocomplete="off" placeholder="e.g. No Friday classes"><button class="primary">Add</button></div></form>
    <p class="detail-text">Or pick a suggestion:</p><div class="starter-prompts">${D.suggestedPrefs.filter(s => !prefs.includes(s)).map(s => `<button class="prompt" data-pref="${esc(s)}">＋ ${esc(s)}</button>`).join('')}</div>
    <p class="disclaimer">Preferences shape the next scripted suggestion in this demo (for example “No Friday classes” or an interest). They are not saved and do not change official MyPlan settings.</p>`);
}
function addPref(p) { p = p.trim(); if (!p) return; if (!prefs.includes(p)) prefs.push(p); renderPrefs(); closeModal(); notify(`Preference added: ${p}`); }

function openDegree() {
  let done = 0, prog = 0, planned = 0, left = 0;
  const groups = D.degree.groups.map(g => {
    const mine = plan.map(course).filter(c => c.req === g.id);
    const d = g.taken.filter(t => t[2] === 'completed').reduce((n, t) => n + t[1], 0), ip = g.taken.filter(t => t[2] !== 'completed').reduce((n, t) => n + t[1], 0);
    const pl = mine.reduce((n, c) => n + c.credits, 0), rem = Math.max(0, g.required - d - ip - pl);
    done += d; prog += ip; planned += pl; left += rem;
    const li = (cls, label, items) => items.length ? `<h4 class="${cls}">${label}</h4><ul>${items.join('')}</ul>` : '';
    return `<details ${g.id === 'core' || g.id === 'ah' ? 'open' : ''}><summary><b>${g.name}</b><span>${d + ip + pl} of ${g.required} credits · ${rem} remaining</span><div class="bar"><i class="b-done" style="width:${d / g.required * 100}%"></i><i class="b-prog" style="width:${ip / g.required * 100}%"></i><i class="b-plan" style="width:${Math.min(pl, g.required - d - ip) / g.required * 100}%"></i></div></summary>
      ${li('s-done', 'Completed', g.taken.filter(t => t[2] === 'completed').map(t => `<li>${t[0]} · ${t[1]} cr <small>${t[3]}</small></li>`))}
      ${li('s-prog', 'In progress', g.taken.filter(t => t[2] !== 'completed').map(t => `<li>${t[0]} · ${t[1]} cr <small>${t[3]}</small></li>`))}
      ${li('s-plan', 'Planned (from your draft)', mine.map(c => `<li>${c.code} · ${c.credits} cr <small>Winter 2027 draft</small></li>`))}
      ${li('s-left', 'Remaining', rem ? g.remaining.filter(r => !mine.some(c => r.startsWith(c.code))).map(r => `<li>${r}</li>`) : [])}
      <p class="disclaimer">Counted here by fictional sample rules. Official applicability must be confirmed by UW (DARS or your adviser).</p></details>`;
  }).join('');
  openModal(`<span class="eyebrow">DEGREE PROGRESS</span><h2 id="modalTitle">${D.degree.major}</h2>
    <p class="sample-banner">Fictional sample audit for “Jordan Lee”. Not connected to MyPlan or DARS.</p>
    <div class="stats"><div class="s-done"><b>${done}</b>Completed credits</div><div class="s-prog"><b>${prog}</b>In progress</div><div class="s-plan"><b>${planned}</b>Planned (draft)</div><div class="s-left"><b>${left}</b>Remaining (shown groups)</div></div>
    ${groups}
    <div class="import-box"><b>Import DARS (local only)</b><p>Placeholder in this demo. The intended design: you choose your own saved audit file, it is read only in this browser tab for the current session, and it is <b>never uploaded or sent to an AI model</b>. You would review the extracted courses and could remove them at any time.</p><button id="importDars">Import DARS (local only)</button> <button disabled title="Needs an authorized UW integration">Sync from MyPlan — unavailable</button><p class="disclaimer hidden" id="importNote" role="status">File import is not implemented in this fast-pass demo — no file was opened or read. Parsing a real audit locally is deferred work.</p></div>`, true);
}

/* ---------- events ---------- */
document.addEventListener('click', event => {
  const t = event.target.closest('button, a'); if (!t) return;
  if (t.dataset.add) { const code = t.dataset.add; plan = plan.includes(code) ? plan.filter(p => p !== code) : [...plan, code]; renderPlan(); notify(plan.includes(code) ? `${code} added to draft` : `${code} removed from draft`); }
  else if (t.dataset.details) openCourse(t.dataset.details);
  else if (t.dataset.remove) { plan = plan.filter(p => p !== t.dataset.remove); renderPlan(); }
  else if (t.dataset.follow) send(t.dataset.follow);
  else if (t.dataset.unpref) { const [gone] = prefs.splice(+t.dataset.unpref, 1); renderPrefs(); notify(`Preference removed: ${gone}`); }
  else if (t.dataset.pref) addPref(t.dataset.pref);
  else if (t.id === 'importDars') $('importNote').classList.remove('hidden');
  else if (t.hasAttribute('data-placeholder')) { event.preventDefault(); notify('Placeholder link — no syllabus is connected'); }
  else if (t.classList.contains('prompt')) send(t.textContent);
});
document.addEventListener('submit', event => { if (event.target.id === 'prefForm') { event.preventDefault(); addPref($('prefInput').value); } });
$('sendMessage').addEventListener('click', () => send());
$('messageInput').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } });
$('messageInput').addEventListener('input', e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px'; });
$('addPref').addEventListener('click', openPrefs);
$('openDegree').addEventListener('click', openDegree);
$('navDegree').addEventListener('click', openDegree);
$('closeModal').addEventListener('click', closeModal);
$('modal').addEventListener('click', event => { if (event.target.id === 'modal') closeModal(); });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && !$('modal').classList.contains('hidden')) closeModal(); });
$('newChat').addEventListener('click', () => { $('thread').innerHTML = ''; plan = []; renderPlan(); notify('Started a new sample conversation'); });
$('clearPlan').addEventListener('click', () => { plan = []; renderPlan(); notify('Draft plan cleared'); });

renderPrefs(); renderPlan();

/* ---------- Student profile, navigation, and weekly timetable ---------- */
const PROFILE_KEY = 'huskyPath.studentProfile.v1';
const defaultProfile = {
  name: 'Jordan Lee', major: 'Computer Science', quarter: 'Winter 2027',
  credits: 15, completed: 'CSE 121, CSE 122, CSE 123', goals: 'Interaction design and software engineering'
};
function readProfile() {
  try {
    const stored = JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null');
    return stored && typeof stored === 'object' ? { ...defaultProfile, ...stored } : { ...defaultProfile };
  } catch { return { ...defaultProfile }; }
}
let studentProfile = readProfile();
let currentView = 'chat';
const profileField = {
  name: 'studentName', major: 'studentMajor', quarter: 'studentQuarter',
  credits: 'studentCredits', completed: 'studentCompleted', goals: 'studentGoals'
};
function completedSet() {
  return new Set(studentProfile.completed.toUpperCase().split(/[,;\n]+/).map(x => x.trim().replace(/\s+/g,' ')).filter(Boolean));
}
function syncProfile() {
  for (const [key, id] of Object.entries(profileField)) $(id).value = studentProfile[key] ?? '';
  $('profileName').textContent = studentProfile.name;
  $('profileInitial').textContent = (studentProfile.name.trim()[0] || '?').toUpperCase();
  $('contextMajor').textContent = studentProfile.major;
  $('contextQuarter').textContent = studentProfile.quarter;
  $('topbarQuarter').textContent = `${studentProfile.quarter} · Demo course data`;
  $('scheduleQuarter').textContent = studentProfile.quarter;
  document.querySelector('.term').firstChild.textContent = `◷ ${studentProfile.quarter} `;
  document.querySelector('.welcome .bubble b').textContent = `Hi ${studentProfile.name.split(/\s+/)[0]}! What would you like help with?`;
}
function showView(view) {
  currentView = view;
  const isChat = view === 'chat';
  document.querySelector('.workspace').classList.toggle('view-extra', !isChat);
  document.querySelector('.conversation').classList.toggle('hidden', !isChat);
  document.querySelector('.context').classList.toggle('hidden', !isChat);
  $('profilePage').classList.toggle('hidden', view !== 'profile');
  $('schedulePage').classList.toggle('hidden', view !== 'schedule');
  document.querySelectorAll('[data-view]').forEach(b => {
    const active = b.dataset.view === view;
    b.classList.toggle('selected', active);
    if (active) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  $('topbarTitle').textContent = view === 'profile' ? 'Student profile' : view === 'schedule' ? 'Weekly schedule' : 'Planning assistant';
  if (view === 'schedule') renderTimetable();
  if (view === 'profile') syncProfile();
  window.scrollTo(0, 0);
}

const WEEK_DAYS = [{ key: 'M', label: 'Monday' }, { key: 'T', label: 'Tuesday' }, { key: 'W', label: 'Wednesday' }, { key: 'Th', label: 'Thursday' }, { key: 'F', label: 'Friday' }];
const START = 8 * 60, END = 19 * 60, HOUR_HEIGHT = 64;
function clock(t) {
  const hour = Math.floor(t / 60);
  return `${hour % 12 || 12}:${String(t % 60).padStart(2, '0')}${hour < 12 ? 'a' : 'p'}`;
}
function renderTimetable() {
  const chosen = plan.map(course).filter(Boolean);
  const total = chosen.reduce((n,c) => n + c.credits, 0);
  $('scheduleTotal').textContent = `${total} credits · ${chosen.length} course${chosen.length === 1 ? '' : 's'} · target ~${studentProfile.credits}`;
  const problems = planConflicts(plan);
  const creditWarning = chosen.length && Math.abs(total - Number(studentProfile.credits)) > 2;
  $('scheduleAlerts').innerHTML = [
    ...problems.map(t => `<div class="conflict" role="alert"><b>⚠ Time conflict</b>${esc(t)}</div>`),
    ...(creditWarning ? [`<div class="calendar-note">Your draft has ${total} credits versus your ${studentProfile.credits}-credit preference.</div>`] : [])
  ].join('');
  const events = [];
  chosen.forEach(c => meetings(c).forEach((m, index) => m.days.forEach(day => {
    events.push({ c, m, day, kind: index === 0 ? 'lec' : 'quiz' });
  })));
  let html = '<div class="time-header">PST · DEMO</div>' + WEEK_DAYS.map(d => `<div class="day-header">${d.label}</div>`).join('');
  html += '<div class="times-col">';
  for (let h = 8; h <= 19; h++) html += `<div class="time-label" style="top:${(h * 60 - START) / 60 * HOUR_HEIGHT}px">${clock(h*60)}</div>`;
  html += '</div>';
  WEEK_DAYS.forEach(d => {
    html += '<div class="day-column">';
    for (let h = 8; h <= 19; h++) html += `<div class="hour-line" style="top:${(h*60-START)/60*HOUR_HEIGHT}px"></div>`;
    const dayEvents = events.filter(e => e.day === d.key);
    dayEvents.forEach(e => {
      const otherConflict = dayEvents.some(other => other !== e && e.m.s < other.m.e && other.m.s < e.m.e);
      const top = (Math.max(START, e.m.s) - START) / 60 * HOUR_HEIGHT;
      const height = Math.max(22, (Math.min(END,e.m.e)-Math.max(START,e.m.s)) / 60 * HOUR_HEIGHT);
      html += `<button type="button" class="calendar-event ${e.kind} ${otherConflict?'is-conflict':''}" style="top:${top}px;height:${height}px" data-details="${e.c.code}" title="${esc(e.c.code)} ${esc(e.m.time)}"><b>${esc(e.c.code)}</b><small>${e.kind === 'lec' ? 'Lecture' : esc(e.m.type)} · ${clock(e.m.s)}–${clock(e.m.e)}</small></button>`;
    });
    html += '</div>';
  });
  $('timetable').innerHTML = html;
  $('scheduleCourseList').innerHTML = chosen.length ? chosen.map(c => `<div class="schedule-list-item"><div><b>${esc(c.code)}</b> <span>${esc(c.title)}</span><small>${c.credits} credits · fictional section</small></div><div><button class="secondary-action" data-details="${c.code}">Details</button><button class="remove-course" data-remove="${c.code}" aria-label="Remove ${c.code}">Remove</button></div></div>`).join('') : '<div class="schedule-empty">No courses added yet. Open the AI Assistant, ask for suggestions, then select “Add to plan.”</div>';
}

$('studentForm').addEventListener('submit', event => {
  event.preventDefault();
  const next = {};
  for (const [key, id] of Object.entries(profileField)) next[key] = $(id).value.trim();
  next.credits = Math.max(1, Math.min(25, Number(next.credits) || 15));
  studentProfile = next;
  try { localStorage.setItem(PROFILE_KEY, JSON.stringify(studentProfile)); } catch { /* private browsing may block storage */ }
  syncProfile();
  renderTimetable();
  $('profileSaved').textContent = '✓ Profile updated';
  notify('Profile saved for this browser');
});
document.querySelectorAll('[data-view]').forEach(el => el.addEventListener('click', () => showView(el.dataset.view)));
$('topbarProfile').addEventListener('click', () => showView('profile'));
$('backToChat').addEventListener('click', () => showView('chat'));
$('scheduleToChat').addEventListener('click', () => showView('chat'));
$('homeLogo').addEventListener('click', event => { event.preventDefault(); showView('chat'); });
const originalRenderPlan = renderPlan;
renderPlan = function () { originalRenderPlan(); renderTimetable(); };
syncProfile();
renderTimetable();

/* Demo presets for walkthroughs/screenshots: index.html?demo=chat | degree | plan */
if (demo) {
  send('Find a course that counts for A&H', true);
  if (demo !== 'chat') { plan = ['CSE 311', 'DESIGN 166']; renderPlan(); }
  if (demo === 'degree') openDegree();
  if (demo === 'plan') openCourse('CSE 311');
}

