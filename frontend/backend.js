/* Husky Path: connects Adeline's front end to the Husky Path backend (POST /chat, /check).
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
  prefs = ['~15 credits', 'No Friday classes', 'Interested in robotics'];
  D.suggestedPrefs = ['~12 credits', 'Mornings preferred', 'In-person only', 'Interested in machine learning',
    'Interested in embedded systems', 'Interested in energy systems', 'Balance technical and writing-heavy courses'];

  const prevSync = syncProfile;
  syncProfile = function () {
    prevSync();
    $('topbarQuarter').textContent = `${studentProfile.quarter} · UW ECE catalog data`;
  };

  /* ---------- real courses from the backend, stored alongside the sample ones ---------- */
  function upsert(card) {
    const real = {
      code: card.code, title: card.title, credits: parseInt(card.credits, 10) || 0, creditsText: String(card.credits),
      reqLabel: card.reqLabel, reason: card.reason, description: card.description, prereq: card.prereq_text,
      url: card.url, offered: card.offered, lecture: null, quiz: null, tags: [], real: true
    };
    const i = D.courses.findIndex(c => c.code === card.code);
    if (i >= 0) D.courses[i] = real; else D.courses.push(real);
  }

  const prevCard = cardHTML;
  cardHTML = function (card) {
    const c = course(card.code);
    if (!c || !c.real) return prevCard(card);
    const inPlan = plan.includes(c.code);
    const when = c.offered ? `Usually ${quarters(c.offered)}` : 'Quarters: check MyPlan';
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
      <p class="sample-banner">Section times, instructors, seats and syllabi aren't part of this prototype. Check the UW Time Schedule or MyPlan.</p>
      <p class="detail-text"><a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">Open in the UW course catalog ↗</a></p>
      <button class="primary" data-add="${esc(c.code)}">${plan.includes(c.code) ? '✓ Added to plan' : '＋ Add to plan'}</button>`, true);
  };

  /* ---------- plan panel and weekly schedule ---------- */
  renderPlan = function () {
    $('emptyPlan').classList.toggle('hidden', plan.length > 0);
    $('planItems').innerHTML = plan.map(code => {
      const c = course(code); if (!c) return '';
      const sections = c.real ? '<div class="sect none">Section times: check MyPlan (not in this prototype)</div>'
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
    const realInPlan = plan.map(course).filter(c => c && c.real);
    $('scheduleCourseList').querySelectorAll('.schedule-list-item').forEach(item => {
      const c = course(item.querySelector('[data-details]')?.dataset.details);
      if (c && c.real) {
        const small = item.querySelector('small');
        if (small) small.textContent = `${c.creditsText} credits · section times not in prototype, check MyPlan`;
        item.querySelector('.rmp-strip')?.remove();
      }
    });
    if (realInPlan.length) $('scheduleAlerts').insertAdjacentHTML('beforeend',
      `<div class="calendar-note">${realInPlan.map(c => esc(c.code)).join(', ')} ${realInPlan.length === 1 ? 'is a' : 'are'} real UW course${realInPlan.length === 1 ? '' : 's'} without section times in this prototype, so ${realInPlan.length === 1 ? 'it isn\'t' : 'they aren\'t'} drawn on the calendar.</div>`);
  };

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
