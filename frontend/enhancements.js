/* Optional client-only transcript review and professor lookup. No server uploads. */
(() => {
  const $ = id => document.getElementById(id);
  const safe = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const RMP_SCHOOL = 'https://www.ratemyprofessors.com/search/professors/1530';
  const facultyKey = 'huskyPath.verifiedFaculty.v1';
  let faculty = {};
  try { faculty = JSON.parse(localStorage.getItem(facultyKey) || '{}') || {}; } catch {}
  const isFictional = name => !name || /fictional|sample|TBA|unknown|staff/i.test(name);
  const getFaculty = c => {
    const override = faculty[c.code];
    if (override && override.trim()) return override.trim();
    const original = c.lecture?.instructor || '';
    return isFictional(original) ? '' : original;
  };
  const rmpLink = name => `${RMP_SCHOOL}?q=${encodeURIComponent(name)}`;
  const courseRmp = c => {
    const name = getFaculty(c);
    if (!name) return `<div class="rmp-strip"><span class="rmp-star">☆</span><div><strong>Professor not confirmed</strong><small>UW instructor assignment needed before matching Rate My Professors.</small></div><span class="rmp-muted">RMP —</span></div>`;
    return `<div class="rmp-strip"><span class="rmp-star">★</span><div><strong>${safe(name)}</strong><small>Search UW Seattle profiles · rating not verified</small></div><a href="${safe(rmpLink(name))}" target="_blank" rel="noopener noreferrer">View on RMP ↗</a></div>`;
  };
  // Attach directly beneath the recommended course description/tags on every newly generated card.
  const originalCard = cardHTML;
  cardHTML = function(card) {
    const html = originalCard(card), c = course(card.code);
    return html.replace('<div class="rec-actions">', `${courseRmp(c)}<div class="rec-actions">`);
  };
  const originalCourse = openCourse;
  openCourse = function(code) {
    originalCourse(code);
    const c = course(code);
    const body = $('modalBody');
    const panel = document.createElement('section');
    panel.className = 'professor-detail';
    panel.innerHTML = `<h3>Professor & Rate My Professors</h3>${courseRmp(c)}<form class="professor-form" id="professorForm"><label for="facultyName">Instructor for this section (from official UW schedule)</label><div><input id="facultyName" maxlength="100" value="${safe(getFaculty(c))}" placeholder="Enter verified instructor name" autocomplete="off"/><button type="submit" class="primary">Update</button></div><p>Updates are stored only in your browser. RMP is an external search, not an independently verified rating or professor-course match.</p></form>`;
    body.appendChild(panel);
    panel.querySelector('form').addEventListener('submit', e => {
      e.preventDefault();
      const name = $('facultyName').value.trim();
      if (name) faculty[code] = name; else delete faculty[code];
      try { localStorage.setItem(facultyKey, JSON.stringify(faculty)); } catch {}
      const updated = courseRmp(c);
      panel.querySelector('.rmp-strip').outerHTML = updated;
      // Existing cards can be updated in place, without restarting the chat.
      document.querySelectorAll('.recommendation').forEach(el => {
        if (el.querySelector(`[data-details="${CSS.escape(code)}"]`)) {
          const old = el.querySelector('.rmp-strip');
          if (old) old.outerHTML = updated;
        }
      });
      notify('Professor reference updated locally');
    });
  };
  // Also place RMP information next to the relevant course in the draft timetable list.
  const originalTimetable = renderTimetable;
  renderTimetable = function() {
    originalTimetable();
    $('scheduleCourseList').querySelectorAll('.schedule-list-item').forEach(item => {
      const code = item.querySelector('[data-details]')?.dataset.details;
      const c = code && course(code);
      if (c) item.insertAdjacentHTML('beforeend', courseRmp(c));
    });
  };
  // Transcript parsing: use locally extracted text only and require explicit review.
  let pending = [];
  const parseTranscript = text => {
    const rows = [];
    const re = /\b([A-Z][A-Z&]{1,7})\s*[- ]?\s*(\d{3}[A-Z]?)\b/g;
    for (const line of text.split(/\r?\n/)) {
      const matches = [...line.toUpperCase().matchAll(re)];
      if (!matches.length) continue;
      const m = matches[0], code = `${m[1]} ${m[2]}`;
      // Accept only credit numbers in a plausible position after the course code.
      const remainder = line.slice(m.index + m[0].length);
      const parts = remainder.match(/\b(?:[1-9](?:\.0)?|10(?:\.0)?)\b/g) || [];
      const credit = parts.length ? Number(parts[0]) : null;
      if (!rows.some(r => r.code === code)) rows.push({code, credit, grade:'Unverified', include:true});
    }
    return rows;
  };
  function review(text) {
    pending = parseTranscript(text);
    $('importStatus').textContent = pending.length ? `${pending.length} candidate course(s) detected. Review before importing.` : 'No courses detected. Try pasted text with one course per line (e.g. CSE 122 4.0).';
    $('importReview').classList.toggle('hidden', !pending.length);
    $('detectedSummary').textContent = `${pending.length} possible matches`;
    $('detectedRows').innerHTML = pending.map((r,i) => `<tr><td><input aria-label="Include ${safe(r.code)}" type="checkbox" data-include="${i}" checked></td><td><input aria-label="Course code" value="${safe(r.code)}" data-code="${i}"></td><td><input aria-label="Credits" type="number" step="0.5" min="0" max="30" value="${r.credit ?? ''}" data-credit="${i}" placeholder="Check"></td><td><span>Review transcript</span></td></tr>`).join('');
  }
  $('parsePasted').addEventListener('click', () => review($('transcriptPaste').value));
  $('transcriptFile').addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 10*1024*1024) { $('importStatus').textContent = 'File exceeds the 10 MB limit.'; return; }
    try {
      let text = '';
      if (/\.txt$/i.test(file.name) || file.type === 'text/plain') text = await file.text();
      else if (/\.pdf$/i.test(file.name) || file.type === 'application/pdf') {
        if (!window.pdfjsLib) throw new Error('PDF reader unavailable. Check your connection or paste text.');
        const pdf = await pdfjsLib.getDocument({data: new Uint8Array(await file.arrayBuffer())}).promise;
        for (let p=1;p<=pdf.numPages;p++) {
          const page = await pdf.getPage(p), content = await page.getTextContent();
          // PDF text chunks may be reordered; extraction must be reviewed.
          let previousY = null;
          for (const item of content.items) {
            const y = item.transform?.[5];
            if (previousY !== null && y !== undefined && Math.abs(y - previousY) > 2) text += '\n';
            text += item.str + ' ';
            if (y !== undefined) previousY = y;
          }
          text += '\n';
        }
      } else throw new Error('Use a .pdf or .txt file.');
      review(text);
      if (!pending.length && /\.pdf$/i.test(file.name)) $('importStatus').textContent += ' Scanned PDFs or multi-column layouts may not parse; try pasting selectable text.';
    } catch(err) { $('importStatus').textContent = err.message; }
    finally { e.target.value = ''; }
  });
  $('cancelTranscript').addEventListener('click', () => { pending=[]; $('importReview').classList.add('hidden'); $('importStatus').textContent='Import cancelled.'; });
  $('confirmTranscript').addEventListener('click', () => {
    const codes = [];
    let creditTotal = 0;
    for (let i=0;i<pending.length;i++) {
      if (!$(`detectedRows`).querySelector(`[data-include="${i}"]`).checked) continue;
      const code = $('detectedRows').querySelector(`[data-code="${i}"]`).value.trim().toUpperCase().replace(/\s+/g,' ');
      const cr = Number($('detectedRows').querySelector(`[data-credit="${i}"]`).value);
      if (!/^[A-Z&]{2,8} \d{3}[A-Z]?$/.test(code)) continue;
      codes.push(code);
      if (cr > 0 && cr <= 30) creditTotal += cr;
    }
    const old = $('studentCompleted').value.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean);
    $('studentCompleted').value = [...new Set([...old, ...codes])].join(', ');
    $('importStatus').textContent = `Added ${codes.length} course code(s) to the form; ${creditTotal} detected credits (unverified). Click Save profile to confirm. Grades, transfer credits, repeats, and degree applicability are not assessed.`;
    $('importReview').classList.add('hidden'); pending=[];
  });
  renderTimetable();
})();
