/* Husky Path: connects Adeline's front end to the Husky Path backend (POST /chat, /check),
   including Winter 2027 sections (times, SLNs, instructors) on the calendar and in the plan.
   Loaded after chat.js and enhancements.js. Her scripted replies stay as the fallback when the
   backend can't be reached. Real UW courses come from the backend; the fictional sample courses in
   data.js are only used by that fallback. */
(() => {
  // Same address when the backend serves this page; otherwise assume it runs locally.
  const API = location.protocol.startsWith('http') ? '' : 'http://127.0.0.1:8000';
  const QUARTER = { A: 'Autumn', W: 'Winter', Sp: 'Spring', S: 'Summer' };
  const quarters = code => (code || '').match(/Sp|A|W|S/g)?.map(q => QUARTER[q]).join(', ') || '';
  const history = [];

  /* ---------- ECE starting point (only when the student hasn't saved their own profile) ---------- */
  Object.assign(defaultProfile, {
    name: 'Jordan Lee', major: 'Engineering Undeclared, aiming for ECE', quarter: 'Winter 2027', credits: 15,
    completed: 'MATH 124, CHEM 142, ENGR 101', in_progress: 'MATH 125, CSE 121, ENGL 131',
    goals: 'Robotics and embedded systems'
  });
  profileField.in_progress = 'studentInProgress';
  studentProfile = readProfile();
  prefs = ['~15 credits', 'Interested in robotics'];
  D.suggestedPrefs = ['No Friday classes', '~12 credits', 'Mornings preferred', 'In-person only', 'Interested in machine learning',
    'Interested in embedded systems', 'Interested in energy systems', 'Balance technical and writing-heavy courses'];

  const prevSync = syncProfile;
  syncProfile = function () {
    prevSync();
    $('topbarQuarter').textContent = `${studentProfile.quarter} · UW ECE catalog data`;
  };

  /* ---------- Winter 2027 sections (team data from the Time Schedule) ---------- */
  const DAYNAME = { M: 'Mon', T: 'Tue', W: 'Wed', Th: 'Thu', F: 'Fri' };
  const clock12 = m => `${(Math.floor(m / 60) + 11) % 12 + 1}:${String(m % 60).padStart(2, '0')}`;
  const half = m => (m < 12 * 60 ? 'AM' : 'PM');
  const timeText = s => `${s.days.map(d => DAYNAME[d]).join(' · ')}, ${clock12(s.start)}${half(s.start) === half(s.end) ? '' : ' ' + half(s.start)}–${clock12(s.end)} ${half(s.end)}`;
  const toMeeting = s => ({ id: s.section, days: s.days, s: s.start, e: s.end, sln: s.sln,
    time: timeText(s), location: `SLN ${s.sln}`, instructor: s.instructor });
  const RMP = 'https://www.ratemyprofessors.com/search/professors/1530?q=';
  const isStaff = name => !name || /^(staff|tba)$/i.test(name.trim());
  const rmpLink = name => isStaff(name) ? '' : `<a href="${RMP}${encodeURIComponent(name.split(',')[0].trim())}" target="_blank" rel="noopener noreferrer">Rate My Professors ↗</a>`;
  const chosen = {};   // course code -> chosen section letter
  const noFriday = () => prefs.some(p => /friday/i.test(p));

  function setSection(c, letter) {
    const sec = (c.sections || []).find(x => x.section === letter) || (c.sections || [])[0];
    c.lecture = sec ? toMeeting(sec) : null;
    if (sec) chosen[c.code] = sec.section;
  }

  // Pick a section that doesn't overlap anything already in the plan (and avoids Friday if preferred).
  function autoPick(c) {
    if (!c.sections || !c.sections.length) { c.lecture = null; return; }
    if (chosen[c.code]) return setSection(c, chosen[c.code]);
    const others = plan.filter(code => code !== c.code).map(course).filter(Boolean).flatMap(meetings);
    const clash = x => others.some(m => m.days.some(d => x.days.includes(d)) && x.start < m.e && m.s < x.end);
    const order = [...c.sections].sort((a, b) => (noFriday() && a.days.includes('F')) - (noFriday() && b.days.includes('F')));
    setSection(c, (order.find(x => !clash(x)) || order[0]).section);
  }

  /* ---------- real courses from the backend, stored alongside the sample ones ---------- */
  function upsert(card) {
    const real = {
      code: card.code, title: card.title, credits: parseInt(card.credits, 10) || 0, creditsText: String(card.credits),
      reqLabel: card.reqLabel, reason: card.reason, description: card.description, prereq: card.prereq_text,
      url: card.url, offered: card.offered, sections: card.sections || [], lecture: null, quiz: null, tags: [], real: true
    };
    if (chosen[real.code]) setSection(real, chosen[real.code]);
    const i = D.courses.findIndex(c => c.code === card.code);
    if (i >= 0) D.courses[i] = real; else D.courses.push(real);
  }

  const prevCard = cardHTML;
  cardHTML = function (card) {
    const c = course(card.code);
    if (!c || !c.real) return prevCard(card);
    const inPlan = plan.includes(c.code);
    const when = c.sections.length ? `Winter 2027 · ${c.sections.length} section${c.sections.length > 1 ? 's' : ''}`
      : c.offered ? `Usually ${quarters(c.offered)}` : 'Quarters: check MyPlan';
    return `<article class="recommendation real-course"><div class="rec-top"><b>${esc(c.code)} · ${esc(c.title)}</b><small>${esc(c.creditsText)} credits</small></div>
      <p class="rec-why">${esc(card.reason || c.reason || '')}</p>
      <div class="rec-tags"><span>${esc(c.reqLabel)}</span><span>${esc(when)}</span></div>
      <ul class="rec-notes"><li class="prereq">Prerequisites: ${esc(c.prereq)}</li>
        ${(card.fits || []).map(f => `<li class="fit">✓ ${esc(f)}</li>`).join('')}${(card.warns || []).map(w => `<li class="warn">⚠ ${esc(w)}</li>`).join('')}</ul>
      <div class="rec-actions"><span><button data-add="${esc(c.code)}">${inPlan ? '✓ Added to plan' : '＋ Add to plan'}</button><button data-details="${esc(c.code)}">View details</button></span><span class="source">UW catalog · verify in MyPlan</span></div></article>`;
  };

  /* ---------- chat: ask the backend, fall back to the scripted demo ---------- */
  const profilePayload = () => ({
    name: studentProfile.name, major: studentProfile.major, quarter: studentProfile.quarter,
    credits: Number(studentProfile.credits) || 15, completed: studentProfile.completed || '',
    in_progress: studentProfile.in_progress || '', goals: studentProfile.goals || ''
  });

  async function askBackend(text) {
    const res = await fetch(`${API}/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, profile: profilePayload(), preferences: prefs, plan, history: history.slice(-6) })
    });
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);
    return res.json();
  }

  const followHTML = (label, items) => items && items.length
    ? `<div class="followup">${label}<br>${items.map(f => `<button data-follow="${esc(f)}">${esc(f)}</button>`).join('')}</div>` : '';

  function renderBackendReply(r) {
    r.cards.forEach(upsert);
    const source = r.source === 'ai'
      ? `Answered by AI from UW catalog data (${r.seconds}s). ${r.disclaimer}`
      : `AI is offline, so this answer comes from rule checks on UW catalog data. ${r.disclaimer}`;
    return `<b>${esc(r.title)}</b><p class="answer-intro">${esc(r.intro)}</p>`
      + (r.workload_warning ? `<p class="advisor-caveat">⚠ ${esc(r.workload_warning)}</p>` : '')
      + r.cards.map(c => cardHTML({ code: c.code, reason: c.reason, fits: c.fits, warns: c.warns })).join('')
      + `<p class="source-line">${esc(source)}</p>` + followHTML('Ask a follow-up:', r.follow);
  }

  function scriptedReply(text) {   // Adeline's original replies, used when the backend is unreachable
    const a = advisorResponse(text);
    if (a) return `<b>${esc(a.title)}</b>${a.html}${followHTML('Ask a follow-up:', a.follow)}`;
    const r = recommend(text);
    return `<b>${esc(r.title)}</b><p class="answer-intro">${esc(r.intro)}</p>${r.cards.map(cardHTML).join('')}${followHTML('What next?', r.follow)}`;
  }

  send = function (text = $('messageInput').value.trim()) {
    if (!text) { $('messageInput').focus(); return; }
    addMessage(text, 'user');
    $('messageInput').value = ''; $('messageInput').style.height = 'auto';
    const loading = addMessage('<p class="answer-intro loading">Checking UW ECE courses and requirements…</p>', 'assistant');
    askBackend(text).then(r => {
      loading.remove();
      history.push({ role: 'user', text }, { role: 'assistant', text: `${r.title}. ${r.intro}` });
      addMessage(renderBackendReply(r), 'assistant');
    }).catch(() => {
      loading.remove();
      addMessage(`<p class="advisor-caveat">The Husky Path backend isn't reachable, so this is the scripted demo reply using fictional sample courses.</p>${scriptedReply(text)}`, 'assistant');
    });
  };

  /* ---------- course details ---------- */
  const prevOpenCourse = openCourse;
  openCourse = function (code) {
    const c = course(code);
    if (!c || !c.real) return prevOpenCourse(code);
    openModal(`<span class="eyebrow">COURSE DETAILS · UW CATALOG</span><h2 id="modalTitle">${esc(c.code)} · ${esc(c.title)}</h2>
      <p class="detail-text">${esc(c.description)}</p>
      <p class="detail-text"><b>${esc(c.creditsText)} credits</b> · Counts toward: ${esc(c.reqLabel)}</p>
      <p class="detail-text"><b>Prerequisites:</b> ${esc(c.prereq)}</p>
      <p class="detail-text"><b>Usually offered:</b> ${esc(quarters(c.offered) || 'not listed in the catalog')} (not a promise for a specific quarter)</p>
      ${c.sections.length ? `<table class="sections"><caption>Winter 2027 sections</caption><thead><tr><th>Section</th><th>SLN</th><th>Time</th><th>Instructor</th></tr></thead><tbody>${c.sections.map(x => `<tr><th scope="row">${esc(x.section)}</th><td>${esc(x.sln)}</td><td>${esc(timeText(x))}</td><td>${esc(x.instructor)} ${rmpLink(x.instructor)}</td></tr>`).join('')}</tbody></table>
        <p class="sample-banner">Winter 2027 sections from the UW Time Schedule, provided by our team. Confirm the SLN and seats in MyPlan before registering. Syllabi aren't part of this prototype.</p>`
        : `<p class="sample-banner">No Winter 2027 section in our data for this course. Check the UW Time Schedule or MyPlan. Syllabi aren't part of this prototype.</p>`}
      <p class="detail-text"><a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">Open in the UW course catalog ↗</a></p>
      <button class="primary" data-add="${esc(c.code)}">${plan.includes(c.code) ? '✓ Added to plan' : '＋ Add to plan'}</button>`, true);
  };

  /* ---------- plan panel and weekly schedule ---------- */
  renderPlan = function () {
    $('emptyPlan').classList.toggle('hidden', plan.length > 0);
    $('planItems').innerHTML = plan.map(code => {
      const c = course(code); if (!c) return '';
      if (c.real) autoPick(c);
      const sections = c.real
        ? (c.lecture ? sectionLine('lec', c.lecture) + (c.sections.length > 1 ? `<button class="switch-section" data-switch="${esc(c.code)}">Switch section (${c.sections.length} options)</button>` : '')
          : '<div class="sect none">No Winter 2027 section in our data · check the Time Schedule</div>')
        : sectionLine('lec', c.lecture) + (c.quiz ? sectionLine('quiz', c.quiz) : '<div class="sect none">No quiz/discussion section (sample)</div>');
      return `<div class="plan-course"><div class="plan-item"><b>${esc(c.code)}</b><span>${esc(c.creditsText || c.credits)} cr</span><button data-details="${esc(c.code)}">View details</button><button data-remove="${esc(c.code)}" aria-label="Remove ${esc(c.code)}">×</button></div>${sections}</div>`;
    }).join('');
    const conflicts = planConflicts(plan), total = plan.reduce((n, code) => n + (course(code)?.credits || 0), 0);
    $('planSummary').innerHTML = plan.length ? `<div class="plan-total">Draft total <b>${total} credits</b></div>`
      + conflicts.map(c => `<div class="conflict" role="alert"><b>⚠ Time conflict</b>${esc(c)}.</div>`).join('') : '';
    document.querySelectorAll('[data-add]').forEach(b => { b.textContent = plan.includes(b.dataset.add) ? '✓ Added to plan' : '＋ Add to plan'; });
    renderTimetable();
  };

  const prevTimetable = renderTimetable;
  renderTimetable = function () {
    prevTimetable();
    const realInPlan = plan.map(course).filter(c => c && c.real && !c.lecture);
    $('scheduleCourseList').querySelectorAll('.schedule-list-item').forEach(item => {
      const c = course(item.querySelector('[data-details]')?.dataset.details);
      if (!c || !c.real) return;
      const small = item.querySelector('small');
      if (small) small.textContent = c.lecture
        ? `${c.creditsText} credits · Winter 2027 section ${c.lecture.id} · ${c.lecture.time} · SLN ${c.lecture.sln}`
        : `${c.creditsText} credits · no Winter 2027 section in our data, check the Time Schedule`;
      if (!c.lecture) item.querySelector('.rmp-strip')?.remove();
    });
    if (realInPlan.length) $('scheduleAlerts').insertAdjacentHTML('beforeend',
      `<div class="calendar-note">${realInPlan.map(c => esc(c.code)).join(', ')} ${realInPlan.length === 1 ? 'is a' : 'are'} course${realInPlan.length === 1 ? '' : 's'} with no Winter 2027 section in our data, so ${realInPlan.length === 1 ? 'it isn\'t' : 'they aren\'t'} drawn on the calendar.</div>`);
  };

  document.addEventListener('click', event => {
    const b = event.target.closest('[data-switch]'); if (!b) return;
    const c = course(b.dataset.switch); if (!c || !c.sections.length) return;
    const i = c.sections.findIndex(x => x.section === chosen[c.code]);
    setSection(c, c.sections[(i + 1) % c.sections.length].section);
    renderPlan();
    notify(`${c.code}: section ${c.lecture.id} · ${c.lecture.time}`);
  });

  /* ---------- degree progress from the backend's ECE requirement checks ---------- */
  const ICON = { done: '✓', in_progress: '◐', partial: '◐', missing: '○', not_tracked: '…' };
  const STATUS = { done: 'Done', in_progress: 'In progress', partial: 'Partly done', missing: 'Still needed', not_tracked: 'Check DARS' };
  const itemRow = i => `<li class="req-${i.status}"><span class="req-icon">${ICON[i.status] || '○'}</span><b>${esc(i.label)}</b> <small>${STATUS[i.status] || ''}${i.detail ? ' · ' + esc(i.detail) : ''}</small></li>`;

  async function openDegreeReal() {
    openModal('<span class="eyebrow">DEGREE PROGRESS</span><h2 id="modalTitle">Checking ECE requirements…</h2>', true);
    try {
      const res = await fetch(`${API}/check`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profilePayload(), plan }) });
      if (!res.ok) throw new Error();
      const d = await res.json(), p = d.placement;
      const groups = d.graduation.map(g => {
        const done = g.items.filter(i => i.status === 'done').length;
        return `<details ${g.items.some(i => i.status === 'missing' || i.status === 'partial') ? 'open' : ''}><summary><b>${esc(g.group)}</b><span>${done} of ${g.items.length} done</span></summary><ul class="req-list">${g.items.map(itemRow).join('')}</ul></details>`;
      }).join('');
      $('modalBody').innerHTML = `<span class="eyebrow">DEGREE PROGRESS · ESTIMATE</span><h2 id="modalTitle">B.S. Electrical &amp; Computer Engineering</h2>
        <p class="sample-banner">Calculated from the courses in your profile against UW ECE requirements (Autumn 2025+ rules). This is a planning estimate, not your DARS audit. Confirm with an ECE adviser.</p>
        <details open><summary><b>${esc(p.label)}</b><span>${p.done} of ${p.total} done · ${esc(p.deadline)}</span></summary><ul class="req-list">${p.items.map(itemRow).join('')}</ul><p class="disclaimer">${esc(p.note)}</p></details>
        ${groups}`;
    } catch {
      $('modalBody').innerHTML = '<span class="eyebrow">DEGREE PROGRESS</span><h2 id="modalTitle">Backend not reachable</h2><p class="detail-text">Start the Husky Path backend to see ECE progress. The fictional sample audit is shown instead.</p><button class="primary" id="showSampleAudit">Show sample audit</button>';
      $('showSampleAudit').addEventListener('click', prevOpenDegree);
    }
  }
  const prevOpenDegree = openDegree;
  openDegree = openDegreeReal;
  ['openDegree', 'navDegree'].forEach(id => {   // replace the buttons so they lose the old listeners
    const old = $(id), fresh = old.cloneNode(true);
    old.replaceWith(fresh);
    fresh.addEventListener('click', openDegreeReal);
  });

  syncProfile(); renderPrefs(); renderPlan();
})();
