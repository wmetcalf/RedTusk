    // ── version ───────────────────────────────────────────────────
    // Host route is /v1/version returning JSON {version, allowed_engines} (the old
    // bespoke /version plaintext route wasn't ported).
    fetch('/v1/version').then(r=>r.json()).then(d=>{
      document.getElementById('version').textContent = d && d.version ? 'v'+d.version : '';
    }).catch(()=>{});

    // ── helpers ───────────────────────────────────────────────────
    function relativeTime(iso) {
      if (!iso) return '—';
      const d = (Date.now() - new Date(iso)) / 1000;
      if (d < 5)    return 'just now';
      if (d < 60)   return Math.floor(d) + 's ago';
      if (d < 3600) return Math.floor(d/60) + 'm ago';
      if (d < 86400)return Math.floor(d/3600) + 'h ago';
      return Math.floor(d/86400) + 'd ago';
    }
    function fmtMs(ms) {
      if (ms == null) return '—';
      const s = ms / 1000;
      return s < 60 ? s.toFixed(1)+'s' : Math.floor(s/60)+'m '+Math.floor(s%60)+'s';
    }
    function duration(job) {
      if (!job) return '—';
      const proc = job.processing_ms != null ? job.processing_ms : null;
      const queue = job.queue_ms != null ? job.queue_ms : null;
      if (proc == null && !job.started_at) return '—';
      // Fallback: compute from timestamps when pre-computed fields absent (old records)
      const procMs = proc != null ? proc : (() => {
        const end = job.completed_at ? new Date(job.completed_at) : new Date();
        return end - new Date(job.started_at);
      })();
      const qMs = queue != null ? queue : 0;
      const procStr = fmtMs(procMs);
      const qStr = qMs > 500 ? ' (q:'+fmtMs(qMs)+')' : '';
      return procStr + qStr;
    }
    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    function fmt_bytes(n) {
      if (!n) return '0 B';
      const units = ['B','KB','MB','GB'];
      let i = 0;
      while (n >= 1024 && i < units.length-1) { n/=1024; i++; }
      return n.toFixed(i?1:0)+' '+units[i];
    }
    // Append the scanner/limit toggles as host `params` form fields. Keys MUST be
    // UPPERCASE env-shaped (the dispatcher drops anything not ^[A-Z][A-Z0-9_]*$
    // before the allowlist); they must also be in BLASTBOX_ENGINE_REDTUSK_PARAM_KEYS.
    function appendJobParams(fd) {
      const qr      = document.getElementById('toggle-qr').checked;
      const ocr     = document.getElementById('toggle-ocr').checked;
      const thumbs  = document.getElementById('toggle-thumbnails').checked;
      const depth   = parseInt(document.getElementById('opt-depth').value) || 10;
      const entries = parseInt(document.getElementById('opt-entries').value) || 5000;
      fd.append('params', 'REDTUSK_ENABLE_QR=' + qr);
      fd.append('params', 'REDTUSK_ENABLE_OCR=' + ocr);
      fd.append('params', 'REDTUSK_ENABLE_THUMBNAILS=' + thumbs);
      fd.append('params', 'REDTUSK_MAX_RECURSION_DEPTH=' + depth);
      fd.append('params', 'REDTUSK_MAX_EMBEDDED_ENTRIES=' + entries);
    }

    // ── blastbox.host ⇄ UI adapter ────────────────────────────────
    // The UI was authored against RedTusk's bespoke API; on blastbox.host the
    // job shape differs (job_id/status/filename + epoch timestamps, and the
    // extraction tree lives behind a separate /rmeta fetch instead of inline
    // job.result). normalizeJob() maps a host job record into the shape the
    // rest of this file already speaks, so the rich viewer (buildJobView/
    // buildTree) is reused verbatim.
    const _BB_STATE = { done: 'succeeded', failed: 'failed', rejected: 'failed',
                        queued: 'queued', running: 'running' };
    // UI state-filter value → host `state` query param (inverse of _BB_STATE;
    // 'succeeded' collapses to host 'done').
    const _UI_TO_BB_STATE = { queued: 'queued', running: 'running',
                              succeeded: 'done', failed: 'failed' };
    const _epochToIso = (e) => {
      // Defensive: a single unparseable timestamp must not throw (RangeError from
      // new Date(NaN).toISOString()) and crash the whole job-list map.
      if (e == null) return null;
      const n = Number(e);
      if (Number.isNaN(n)) return null;
      try { return new Date(n * 1000).toISOString(); } catch { return null; }
    };

    function normalizeJob(j) {
      if (!j || j.id) return j;            // already normalized / not a host record
      const created = j.created_at, started = j.started_at, finished = j.finished_at;
      return {
        id: j.job_id,
        state: _BB_STATE[j.status] || j.status || 'queued',
        filename_hint: j.filename || '—',
        submitted_at: _epochToIso(created),
        started_at: _epochToIso(started),
        completed_at: _epochToIso(finished),
        processing_ms: (finished != null && started != null) ? (finished - started) * 1000 : null,
        queue_ms: (started != null && created != null) ? (started - created) * 1000 : null,
        error_detail: j.error || null,
        worker_runtime: j.worker_runtime || null,
        worker_tier: j.worker_tier || null,   // 'firecracker' | 'gvisor' for warm jobs
        // qr_count isn't in the host list summary; the detail view surfaces QR
        // per-entry from /rmeta. result stays null until the detail view fetches it.
        qr_count: null,
        result: null,
        _bb: j,
      };
    }

    // ── upload ────────────────────────────────────────────────────
    // The host is async-only (submit→dispatch→poll); the bespoke synchronous
    // /v1/convert path is not ported, so the UI queues every upload.
    async function uploadAsync() {
      const files = document.getElementById('file-input').files;
      if (!files.length) { setStatus('Select file(s) first.'); return; }
      setButtons(true); setStatus('Queuing '+files.length+' file(s)…');
      let ok=0, fail=0;
      for (const f of files) {
        try {
          // Host submit is multipart: file + engine + repeated `params` fields.
          const fd = new FormData();
          fd.append('file', f);
          fd.append('engine', 'redtusk');
          appendJobParams(fd);
          const r = await fetch('/v1/jobs', { method:'POST', body: fd });
          if (r.ok) ok++; else fail++;
        } catch { fail++; }
      }
      setStatus('Queued: '+ok+(fail?', failed: '+fail:''));
      setButtons(false); fetchJobs();
    }

    function setButtons(d) {
      const b = document.getElementById('queue-btn');
      if (b) b.disabled = d;
    }
    function setStatus(m) { document.getElementById('upload-status').textContent=m; }

    // ── shared metadata rendering ─────────────────────────────────
    const SECURITY_KEYS = new Set([
      'rtf_meta:emb_ole2link_url','rtf_meta:emb_source_path','rtf_meta:emb_label',
      'rtf_meta:emb_class','rtf_meta:emb_class_obfuscated','rtf_meta:emb_clsid',
      'rtf_meta:emb_topic','rtf_meta:emb_item','rtf_meta:objdata_decoy_count',
      'rtf_meta:hex_escape_in_objdata','rtf_meta:unicode_in_objdata',
      'rtf_meta:malformed_rtf_header','rtf_meta:template_url',
      'rtf_meta:unc_path','rtf_meta:url','rtf_meta:ip',
      'dc:title','dc:description','extended-properties:Template',
    ]);
    // Lazy expand: full values are kept here in JS memory (where they already
    // live in the parsed job JSON via jobCache), NOT eagerly serialized into
    // the DOM. On click, swap the truncated text for the full value — single
    // O(1) lookup, no round-trip, no DOM bloat per-render.
    const metaFullValues = new Map(); // dom-id -> full string
    let metaSeq = 0;

    function metaExpand(ev) {
      // Event is delegated from document, so currentTarget == document.
      // The clicked .meta-ellipsis is in ev.target.
      const ell = ev.target;
      const id = ell.dataset.metaId;
      if (!id) return;
      const cell = ell.closest('.meta-val');
      const full = metaFullValues.get(id);
      if (cell && full != null) {
        const node = cell.querySelector('.meta-truncated');
        if (node) {
          node.textContent = full;     // textContent handles XSS-safe insertion
        }
        cell.classList.add('expanded');
        ell.style.display = 'none';
        // Free the cached string once revealed — the DOM owns it now.
        metaFullValues.delete(id);
      }
      ev.stopPropagation();
    }

    // ── event delegation ──────────────────────────────────────────
    // CSP forbids inline event-handler attributes (no 'unsafe-inline' in
    // script-src), so all interactive elements declare a `data-act` (and
    // optional `data-arg`) attribute and are dispatched from here. Works for
    // any dynamically-inserted markup.
    // ── Job-detail view state: whitespace-collapse + raw-JSON toggles ──
    let _wsCollapse = false;     // collapse runs of h-ws + blank lines in shown text
    let _lastJobDetail = null;   // {id, job} cached so the ws toggle can re-render

    // Collapse extracted-text whitespace for readability — kept in EXACT sync
    // with types.py wsnorm(). Strips zero-width/invisible chars (U+200B-D,
    // U+2060, BOM U+FEFF); normalises CRLF/CR + Unicode line/para separators
    // (U+2028/9) to LF; collapses a run of horizontal whitespace (ASCII space/
    // tab + the Unicode Zs category: NBSP, ideographic, en/em/thin/hair, …) to
    // one char — a tab if the run held a tab ("whatever is longest"), else a
    // space; strips trailing h-ws; collapses 3+ newlines to one blank line.
    function collapseWs(s) {
      return String(s)
        .replace(/[\u200b\u200c\u200d\u2060\ufeff]/g, '')
        .replace(/\r\n|\r|\u2028|\u2029/g, '\n')
        .replace(/[ \t\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+/g, (m) => (m.indexOf('\t') >= 0 ? '\t' : ' '))
        .replace(/[ \t\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+\n/g, '\n')
        .replace(/\n{3,}/g, '\n\n');
    }

    function toggleRawJson(btn) {
      const pre = document.getElementById('raw-json-view');
      if (!pre) return;
      const show = pre.style.display === 'none';
      pre.style.display = show ? 'block' : 'none';
      btn.textContent = show ? '{ } hide JSON' : '{ } raw JSON';
    }

    const CLICK_ACTIONS = {
      'nav-list': () => navigateToList(),
      'nav-job': (el) => navigateToJob(el.dataset.arg),
      'upload-async': () => uploadAsync(),
      'clear-search': () => clearSearch(),
      'toggle-text': (el) => toggleText(el),
      'tree-toggle': (el) => treeToggle(el.dataset.arg),
      'go-page': (el) => goToPage(parseInt(el.dataset.arg, 10)),
      'set-state': (el) => setStateFilter(el.dataset.arg || null),
      'delete-job': (el) => deleteJobAndGoBack(el.dataset.arg),
      'toggle-raw': (el) => toggleRawJson(el),
      'toggle-ws': () => { _wsCollapse = !_wsCollapse; if (_lastJobDetail) renderJobDetail(_lastJobDetail.id, _lastJobDetail.job); },
    };

    document.addEventListener('click', (ev) => {
      const t = ev.target;
      if (t && t.classList && t.classList.contains('meta-ellipsis')) {
        metaExpand(ev);
        return;
      }
      if (t && t.classList && t.classList.contains('hash-link')) {
        ev.preventDefault();
        openSimilarPanel(t.dataset.hash, t.dataset.val);
        return;
      }
      // Generic data-act dispatch (closest so clicks on inner nodes still fire).
      const actEl = t && t.closest ? t.closest('[data-act]') : null;
      if (actEl) {
        const handler = CLICK_ACTIONS[actEl.dataset.act];
        if (handler) {
          if (actEl.dataset.prevent === '1') ev.preventDefault();
          handler(actEl);
        }
      }
    });

    // Delegated input handler for the search box (replaces inline oninput).
    document.addEventListener('input', (ev) => {
      const t = ev.target;
      if (t && t.id === 'search-input') onSearch(t.value);
    });

    // Delegated, capture-phase error handler for thumbnail <img> tags that
    // fail to load (replaces inline onerror). Capture phase is required —
    // 'error' events do not bubble.
    document.addEventListener('error', (ev) => {
      const t = ev.target;
      if (t && t.tagName === 'IMG' && t.dataset.onerror) {
        if (t.dataset.onerror === 'hide') {
          t.style.display = 'none';
        } else if (t.dataset.onerror === 'thumb') {
          thumbErr(t);
        }
      }
    }, true);

    // Theme-song link hover (replaces inline onmouseover/onmouseout).
    const themeLink = document.getElementById('theme-song');
    if (themeLink) {
      themeLink.addEventListener('mouseover', () => { themeLink.style.opacity = '1'; });
      themeLink.addEventListener('mouseout', () => { themeLink.style.opacity = '0.7'; });
    }

    // ── similarity panel ─────────────────────────────────────────────
    let _simCurrent = { kind: null, value: null };

    function openSimilarPanel(kind, value) {
      _simCurrent = { kind, value };
      const panel = document.getElementById('similar-panel');
      const title = document.getElementById('similar-title');
      const controls = document.getElementById('similar-controls');
      controls.style.display = (kind === 'phash') ? 'flex' : 'none';
      title.textContent = 'Similar by ' + kind + ': ' + value.slice(0, 16) + (value.length > 16 ? '…' : '');
      document.getElementById('similar-body').innerHTML = '<div class="similar-empty">Loading…</div>';
      panel.classList.add('show');
      panel.setAttribute('aria-hidden', 'false');
      fetchSimilar();
    }

    async function fetchSimilar() {
      const { kind, value } = _simCurrent;
      if (!kind || !value) return;
      const body = document.getElementById('similar-body');
      const countEl = document.getElementById('similar-count');
      const params = new URLSearchParams({ [kind]: value, limit: '50' });
      if (kind === 'phash') {
        const mh = document.getElementById('similar-max-hamming').value || '5';
        params.set('max_hamming', mh);
      }
      if (countEl) countEl.textContent = '…';
      try {
        const r = await fetch('/v1/similar?' + params.toString());
        if (!r.ok) {
          const err = await r.text();
          body.innerHTML = '<div class="similar-empty" style="color:#ef5350">' + esc(err) + '</div>';
          if (countEl) countEl.textContent = '';
          return;
        }
        const d = await r.json();
        const matches = d.matches || [];
        renderSimilarMatches(matches);
        // Match count next to the Refetch button — shows whether the result is
        // capped (we request limit=50) so users know to widen max_hamming when
        // 50 means "≥50 matches, refining would help".
        if (countEl) {
          const capped = matches.length >= 50;
          countEl.textContent = matches.length + (capped ? '+ matches' : ' match' + (matches.length === 1 ? '' : 'es'));
        }
      } catch (e) {
        body.innerHTML = '<div class="similar-empty" style="color:#ef5350">Network error: ' + esc(e.message) + '</div>';
        if (countEl) countEl.textContent = '';
      }
    }

    // Thumbnails on blastbox.host: the worker writes them under rmeta/ (root →
    // rmeta/thumbnail.jpg, embedded → rmeta/embedded/thumbnails/<rel>.jpg) and the
    // engine auto-declares them as artifacts. The host serves artifacts by *id*, so
    // we resolve a thumbnail's relative PATH to its declared id via _curArtMap
    // (built from the envelope's artifacts[] when the detail view loads).
    let _curArtMap = {};            // artifact path → id, for the job being rendered

    function _artUrl(jobId, path) {
      if (!jobId || !path) return null;
      // _curArtMap belongs to the CURRENTLY-loaded detail job only. For cross-job
      // lookups (e.g. the similarity panel's matches) we have no map, so resolve
      // nothing rather than mis-resolve against the active job's artifacts.
      if (!_lastJobDetail || _lastJobDetail.id !== jobId) return null;
      const id = _curArtMap[path];
      return id ? '/v1/jobs/' + jobId + '/artifacts/' + encodeURIComponent(id) : null;
    }

    function _entryThumbPath(entryPath) {
      if (!entryPath || entryPath === '/') return 'rmeta/thumbnail.jpg';
      const rel = entryPath.startsWith('/') ? entryPath.slice(1) : entryPath;
      return 'rmeta/embedded/thumbnails/' + rel + '.jpg';
    }

    function thumbUrlFor(jobId, entryPath) {
      // Same-job lookups resolve via the loaded artifact map. Cross-job matches
      // (the similarity panel) have no map here, so they render without a thumb.
      return _artUrl(jobId, _entryThumbPath(entryPath));
    }

    function renderSimilarMatches(matches) {
      const body = document.getElementById('similar-body');
      if (!matches.length) {
        body.innerHTML = '<div class="similar-empty">No matches.</div>';
        return;
      }
      let html = '';
      for (const m of matches) {
        const thumb = thumbUrlFor(m.job_id, m.entry_path);
        html += '<div class="similar-tile">';
        html += '<div class="top">';
        html += '<span class="fname">' + esc(m.filename || m.entry_path || '—') + '</span>';
        if (m.distance != null) html += '<span class="dist">Δ ' + m.distance + '</span>';
        html += '</div>';
        if (thumb) {
          html += '<img src="' + esc(thumb) + '" alt="" loading="lazy" ' +
                  'style="max-width:100%;max-height:160px;border:1px solid #30363d;' +
                  'border-radius:3px;margin-bottom:6px;display:block" ' +
                  'data-onerror="hide">';
        }
        html += '<div class="meta">';
        html += '<div>entry: <span style="color:#c9d1d9">' + esc(m.entry_path || '/') + '</span></div>';
        if (m.content_type) html += '<div>ct: <span style="color:#c9d1d9">' + esc(m.content_type) + '</span></div>';
        if (m.phash)        html += '<div>phash: ' + esc(m.phash) + '</div>';
        if (m.colorhash)    html += '<div>colorhash: ' + esc(m.colorhash) + '</div>';
        if (m.sha256)       html += '<div>sha256: ' + esc(m.sha256) + '</div>';
        html += '<div><a href="/jobs/' + esc(m.job_id) + '" data-act="nav-job" data-prevent="1" data-arg="' + esc(m.job_id) + '" style="font-family:\'Courier New\',monospace">Open job ' + esc(m.job_id) + '</a></div>';
        html += '</div></div>';
      }
      body.innerHTML = html;
    }

    document.getElementById('similar-close').addEventListener('click', () => {
      const panel = document.getElementById('similar-panel');
      panel.classList.remove('show');
      panel.setAttribute('aria-hidden', 'true');
    });
    document.getElementById('similar-refetch').addEventListener('click', fetchSimilar);
    // Escape closes the panel.
    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') {
        const p = document.getElementById('similar-panel');
        if (p.classList.contains('show')) {
          p.classList.remove('show');
          p.setAttribute('aria-hidden', 'true');
        }
      }
    });

    function renderMetaTable(meta) {
      const keys = Object.keys(meta).sort();
      if (!keys.length) return '';
      const groups = {};
      for (const k of keys) {
        const grp = k.includes(':') ? k.split(':')[0] : 'other';
        (groups[grp] = groups[grp]||[]).push(k);
      }
      const TRUNC = 200;
      let out = '<div class="meta-table">';
      for (const grp of Object.keys(groups).sort()) {
        for (const k of groups[grp]) {
          const raw = meta[k];
          // Multi-valued metadata arrives as a JS array — stringify uniformly.
          const v = Array.isArray(raw) ? raw.join('\n') : String(raw);
          const isSec = SECURITY_KEYS.has(k);
          if (v.length > TRUNC) {
            // Stash the full value in JS memory, NOT in the DOM.
            const id = 'm' + (++metaSeq);
            metaFullValues.set(id, v);
            const head = esc(v.slice(0, TRUNC));
            out += '<div class="meta-row'+(isSec?' meta-sec':'')+'">' +
                   '<span class="meta-key">'+esc(k)+'</span>' +
                   '<span class="meta-val truncatable">' +
                     '<span class="meta-truncated">'+head+'</span>' +
                     '<span class="meta-ellipsis" data-meta-id="'+id+'" ' +
                           'title="Click to expand ('+v.length+' chars)">…</span>' +
                   '</span></div>';
          } else {
            out += '<div class="meta-row'+(isSec?' meta-sec':'')+'">' +
                   '<span class="meta-key">'+esc(k)+'</span>' +
                   '<span class="meta-val">'+esc(v)+'</span></div>';
          }
        }
      }
      out += '</div>';
      return out;
    }

    // ── structured job view ───────────────────────────────────────
    function buildJobView(jobOrResult, jobId) {
      // Each new job view starts with a fresh lazy-expand cache so values
      // belonging to a previously-viewed job don't accumulate in memory.
      metaFullValues.clear();

      // Accept either a full job record or a bare result object.
      const isFullJob = jobOrResult && ('state' in jobOrResult || 'queue_ms' in jobOrResult);
      const job    = isFullJob ? jobOrResult : null;
      const result = isFullJob ? jobOrResult.result : jobOrResult;
      if (!result) return '<span style="color:#666">No result</span>';
      const ext = result.extraction || {};
      const entries = ext.entries || [];
      const inp = result.input || {};
      const sandbox = result.sandbox || {};

      const allQr = [];
      let fullText = '', fullTextNorm = '';
      for (const e of entries) {
        for (const c of (e.qr?.codes||[])) allQr.push({entry:e.path,...c});
        if (!fullText && e.text) {
          fullText = e.text.trim().replace(/\n{3,}/g, '\n\n');
          fullTextNorm = (e.text_wsnorm || '').trim();   // stored normalized form, if present
        }
      }
      // Always show expander when there's text — max-height CSS clips regardless of char count
      const hasMore = fullText.length > 0;

      let html = '<div class="job-sections">';

      // ── Summary ──
      html += '<div class="job-section"><div class="job-section-hdr">Summary</div><div class="job-section-body"><div class="kv-grid">';
      // Full job ID first — needed so users can copy/paste / quote in tickets
      // without hovering the row in the recent-jobs table. kvHash() applies
      // the monospace .hash style. Fall back to job.id if jobId wasn't passed
      // (some callers pass only the bare result object).
      html += kvHash('Job ID', jobId || (job && job.id) || '—');
      html += kv('Content-Type', ext.root_content_type||'—');
      html += kv('Language',     ext.root_language||'—');
      html += kv('Entries',      entries.length);
      html += kv('Parse time',  (ext.duration_ms||0)+'ms');
      if (job && job.queue_ms != null)      html += kv('Queue time',  fmtMs(job.queue_ms));
      if (job && job.pool_wait_ms != null)  html += kv('Pool wait',   fmtMs(job.pool_wait_ms));
      if (job && job.processing_ms != null) html += kv('Worker time', fmtMs(job.processing_ms));
      // Dispatcher tier that ran the job (distinct from the in-VM Sandbox below): the two warm
      // backends (FC microVM vs gVisor C/R) both report worker_runtime="warm" — worker_tier
      // disambiguates them.
      if (job && job.worker_runtime) {
        const rt = job.worker_runtime, tier = job.worker_tier;
        html += kv('Worker tier', rt === 'warm'
          ? (tier === 'firecracker' ? 'warm · Firecracker microVM'
             : tier === 'gvisor' ? 'warm · gVisor C/R' : 'warm')
          : rt);
      }
      if (job && job.parse_ms != null)      html += kv('Tika parse',  fmtMs(job.parse_ms));
      if (result.truncated) html += kv('Truncated', result.truncated.reason+' ('+result.truncated.observed+'/'+result.truncated.limit+')');
      if ((result.warnings||[]).length) html += kv('Warnings', result.warnings.length);
      html += '</div></div></div>';

      // ── Input / Hashes ──
      html += '<div class="job-section"><div class="job-section-hdr">Input &amp; Hashes</div><div class="job-section-body"><div class="kv-grid">';
      html += kv('Filename',    inp.filename_hint||'—');
      html += kv('Size',        fmt_bytes(inp.size_bytes));
      html += kvHash('SHA-256', inp.sha256||'—');
      html += kv('Submitted',   inp.submitted_at ? new Date(inp.submitted_at).toLocaleString() : '—');
      // Per-entry hashes (non-null ones)
      for (const e of entries) {
        if (e.sha256) html += kvHash(e.path+' sha256', e.sha256);
      }
      html += kv('Sandbox',     sandbox.profile+' / '+sandbox.runtime+(sandbox.appcds?' + AppCDS':''));
      html += '</div></div></div>';

      // ── Root Metadata ──
      const rootEntry = entries.find(e => e.path === '/');
      if (rootEntry && Object.keys(rootEntry.metadata||{}).length) {
        html += '<div class="job-section"><div class="job-section-hdr">Root Metadata</div><div class="job-section-body">';
        html += renderMetaTable(rootEntry.metadata);
        html += '</div></div>';
      }

      // ── QR codes ──
      if (allQr.length) {
        html += '<div class="job-section"><div class="job-section-hdr">QR Codes <span style="color:#64b5f6">×'+allQr.length+'</span></div><div class="job-section-body"><div class="qr-list">';
        for (const c of allQr) {
          html += '<div class="qr-item"><div class="qr-url">'+esc(c.data)+'</div>';
          html += '<div class="qr-meta">'+esc(c.format||'')+(c.position?' · '+esc(c.position):'')+(c.raw_bytes?' · bytes: '+esc(c.raw_bytes.slice(0,40)):'')+'</div></div>';
        }
        html += '</div></div></div>';
      }

      // ── Text preview ──
      if (fullText) {
        const uid = 'txt-'+(Math.random().toString(36).slice(2));
        const dispFull = _wsCollapse ? (fullTextNorm || collapseWs(fullText)) : fullText;
        html += '<div class="job-section"><div class="job-section-hdr">Text</div><div class="job-section-body">';
        html += '<div class="text-preview" id="'+uid+'">'+esc(dispFull)+'</div>';
        if (dispFull.length > 300) {
          html += '<span class="text-toggle" data-act="toggle-text" data-uid="'+uid+'" data-full="'+esc(dispFull)+'">▼ show full ('+dispFull.length.toLocaleString()+' chars)</span>';
        }
        html += '</div></div>';
      }

      // ── Extraction Tree ──
      html += '<div class="job-section"><div class="job-section-hdr">Extraction Tree';
      html += ' <span style="color:#666;font-weight:normal;font-size:0.8rem">('+entries.length+' entr'+(entries.length===1?'y':'ies')+')</span></div>';
      html += '<div class="job-section-body">'+buildTree(entries, jobId)+'</div></div>';

      html += '</div>';
      return html;
    }

    // ── entry-type icon ───────────────────────────────────────────
    function ctIcon(ct) {
      if (!ct) return '📄';
      if (ct.includes('pdf'))          return '📕';
      if (ct.includes('image'))        return '🖼';
      if (ct.includes('zip')||ct.includes('archive')||ct.includes('compressed')) return '📦';
      if (ct.includes('word')||ct.includes('odt'))  return '📝';
      if (ct.includes('excel')||ct.includes('spreadsheet')||ct.includes('ods')) return '📊';
      if (ct.includes('powerpoint')||ct.includes('presentation')||ct.includes('odp')) return '📊';
      if (ct.includes('vbasic')||ct.includes('macro')||ct.includes('script')) return '⚠️';
      if (ct.includes('text')||ct.includes('plain')||ct.includes('rtf')) return '📄';
      if (ct.includes('html'))         return '🌐';
      if (ct.includes('email')||ct.includes('rfc822')) return '✉️';
      return '📄';
    }

    function buildTree(entries, jobId) {
      if (!entries.length) return '<span style="color:#555">—</span>';

      // Build node map keyed by path
      const nodeMap = new Map();
      for (const e of entries) nodeMap.set(e.path, e);

      // Render each entry as an expandable tree node
      let html = '<div class="tree">';
      for (const e of entries) {
        const depth = e.depth || 0;
        const name = e.path==='/' ? '/' : e.path.split('/').filter(Boolean).pop() || e.path;
        const ct = e.content_type || '';
        const ctShort = ct.split('/').pop() || ct;
        const qrCodes = e.qr?.codes || [];
        // For image entries Tika writes OCR output into TIKA_CONTENT, so e.text === e.ocr.text.
        // Treat the entry as "pure OCR" if content-type is a raster image (not SVG).
        // SVG text comes from <text> element extraction, not OCR — label it differently.
        const isRasterImage = ct.startsWith('image/') && ct !== 'image/svg+xml';
        const isSvg = ct === 'image/svg+xml';
        // Suppress the ocrText block for raster images — it's identical to entryText and
        // would render twice.  For SVG, the text is extracted (not OCR) and shown below.
        const ocrText = isRasterImage ? '' : (e.ocr?.text || '').trim().replace(/\n{3,}/g,'\n\n');
        const sha = e.sha256;
        const meta = e.metadata || {};
        const uid = 'e-'+(Math.random().toString(36).slice(2));

        // Key metadata to surface in the header row summary (brief)
        const metaHighlights = [];
        for (const k of ['Image Width','Image Height','xmpTPg:NPages','meta:word-count',
                          'dc:creator','dc:title','dcterms:created','img:Quality','Content-Length']) {
          if (meta[k]) metaHighlights.push(k.split(':').pop().split(/(?=[A-Z])/).join(' ')+': '+meta[k]);
        }

        html += '<div class="tree-node" style="margin-left:'+(depth*16)+'px">';

        // Header row (always visible)
        html += '<div class="tree-hdr" data-act="tree-toggle" data-arg="'+uid+'">';
        html += '<span class="tree-arrow" id="arr-'+uid+'">▶</span> ';
        html += ctIcon(ct)+' ';
        html += '<span class="tree-name">'+esc(name)+'</span> ';
        html += '<span class="tree-ct">'+esc(ctShort)+'</span>';
        if (e.size_bytes) html += ' <span class="tree-size">'+fmt_bytes(e.size_bytes)+'</span>';
        if (qrCodes.length) html += ' <span class="qr-badge">QR×'+qrCodes.length+'</span>';
        // Show OCR badge when OCR produced output; not for SVG (that's text extraction, not OCR)
        if (e.ocr?.text && !isSvg) html += ' <span class="tree-tag">OCR</span>';
        if (e.ocr?.skipped === 'blank_image') html += ' <span class="tree-blank" title="OCR skipped — blank/uniform image (phash/colorhash)">BLANK</span>';
        if (e.thumbnail_skipped === 'zero_byte_stream') html += ' <span class="tree-blank" title="Thumbnail unavailable — Pass 2 received zero bytes (deeply nested or VBA source-stripped entry)">NO-THUMB</span>';
        if (e.thumbnail_skipped === 'pass2_missed_entry') html += ' <span class="tree-blank" title="Thumbnail unavailable — Pass 1 saw this image entry but Pass 2 (byte-saving pass) didn\'t surface it (Tika parser path difference, common with some MSG/MAPI attachment shapes)">NO-THUMB</span>';
        if (e.error) html += ' <span class="tree-err">ERR</span>';
        html += '</div>';

        // Detail panel (hidden by default)
        html += '<div class="tree-body" id="'+uid+'" style="display:none">';

        // Resolve the thumbnail (root → rmeta/thumbnail.jpg, embedded →
        // rmeta/embedded/thumbnails/<rel>.jpg) to its declared-artifact id.
        const _thumbUrl = (e.has_thumbnail && jobId) ? _artUrl(jobId, _entryThumbPath(e.path)) : null;
        if (_thumbUrl) {
          // data-src: deferred until the tree node is opened (set by treeToggle)
          html += '<img data-src="'+esc(_thumbUrl)+'" alt="" style="max-width:256px;max-height:256px;display:block;margin:0.4rem 0;border:1px solid #333;border-radius:3px" data-onerror="thumb">';
        }
        if (sha)          html += '<div class="tree-meta">sha256: <a class="hash-link" data-hash="sha256" data-val="'+esc(sha)+'" title="Find entries with this exact SHA-256">'+esc(sha)+'</a></div>';
        if (e.md5)        html += '<div class="tree-meta">md5: <span class="mono">'+esc(e.md5)+'</span> &nbsp; sha1: <span class="mono">'+esc(e.sha1||'—')+'</span></div>';
        if (e.phash)      html += '<div class="tree-meta">phash: <a class="hash-link" data-hash="phash" data-val="'+esc(e.phash)+'" title="Find perceptually-similar entries">'+esc(e.phash)+'</a> &nbsp; colorhash: '+(e.colorhash ? '<a class="hash-link" data-hash="colorhash" data-val="'+esc(e.colorhash)+'" title="Find entries with this exact colorhash">'+esc(e.colorhash)+'</a>' : '<span class="mono">—</span>')+'</div>';
        if (metaHighlights.length) html += '<div class="tree-meta">'+esc(metaHighlights.join(' · '))+'</div>';
        html += renderMetaTable(meta);

        if (qrCodes.length) {
          html += '<div class="tree-meta" style="color:#4fc3f7">';
          for (const c of qrCodes) html += '🔗 '+esc(c.data.slice(0,80))+'<br>';
          html += '</div>';
        }

        // Entry text (Tika-extracted) — shown for non-root entries (macros, embedded docs, etc.)
        // Root entry text is already shown in the top-level "Text" section.
        // For raster images, e.text IS the OCR output — show it in the OCR block below, not here.
        const rawEntryText = (e.depth > 0 && !isRasterImage) ? (e.text||'').trim().replace(/\n{3,}/g,'\n\n') : '';
        // For raster images show e.text directly (it's the OCR output); label it "ocr text".
        const imageOcrText = isRasterImage ? (e.text||'').trim().replace(/\n{3,}/g,'\n\n') : '';

        function renderTextBlock(text, label, norm) {
          if (!text) return '';
          // Prefer the server-stored wsnorm (norm); fall back to client collapse
          // (e.g. OCR text, or jobs processed before text_wsnorm existed).
          if (_wsCollapse) text = (norm && norm.trim()) ? norm.trim() : collapseWs(text);
          const uid_='tb-'+(Math.random().toString(36).slice(2));
          let out = '<div class="tree-meta">';
          out += '<div class="tree-meta" style="color:#888;font-size:0.7rem;margin-bottom:0.2rem">'+label+'</div>';
          out += '<div class="text-preview" id="'+uid_+'">'+esc(text)+'</div>';
          if (text.length > 300) {
            out += '<span class="text-toggle" data-act="toggle-text" data-uid="'+uid_+'" data-full="'+esc(text)+'">▼ show full ('+text.length.toLocaleString()+' chars)</span>';
          }
          out += '</div>';
          return out;
        }

        // SVG: label as "extracted text" (not OCR — it comes from <text> elements)
        const entryLabel = isSvg ? 'extracted text' : 'extracted text';
        html += renderTextBlock(rawEntryText, entryLabel, e.text_wsnorm);

        // Raster images: show OCR output once under "ocr text"
        html += renderTextBlock(imageOcrText, 'ocr text', e.text_wsnorm);

        // Non-image OCR output (e.g. OCR ran on a PDF page image embedded in a doc)
        if (ocrText && ocrText !== rawEntryText) {
          html += renderTextBlock(ocrText, 'ocr text');
        }

        if (e.error) html += '<div class="tree-meta" style="color:#ef5350">'+esc(e.error.slice(0,120))+'</div>';

        html += '</div></div>';
      }
      html += '</div>';
      return html;
    }

    function treeToggle(uid) {
      const body = document.getElementById(uid);
      const arr  = document.getElementById('arr-'+uid);
      if (!body) return;
      const open = body.style.display==='none';
      body.style.display = open ? 'block' : 'none';
      if (arr) arr.textContent = open ? '▼' : '▶';
      // Lazy-load thumbnails on first open
      if (open) {
        for (const img of body.querySelectorAll('img[data-src]')) {
          img.src = img.getAttribute('data-src');
          img.removeAttribute('data-src');
        }
      }
    }

    function thumbErr(img) {
      img.style.display = 'none';
      img.insertAdjacentHTML('afterend',
        '<div style="color:#555;font-size:0.75rem;margin:0.2rem 0">thumbnail unavailable</div>');
    }

    function kv(k,v) {
      return '<span class="kv-key">'+esc(k)+'</span><span class="kv-val">'+esc(String(v??'—'))+'</span>';
    }
    function kvHash(k,v) {
      return '<span class="kv-key">'+esc(k)+'</span><span class="kv-val hash">'+esc(String(v??'—'))+'</span>';
    }

    // All text display uses esc() before innerHTML injection or textContent assignment.
    // Never use innerHTML with raw document text — malware (HTA/phishing) payloads
    // contain VBScript/JS that must render as inert text, not execute in the browser.
    function toggleText(btn) {
      const uid = btn.getAttribute('data-uid');
      const el = document.getElementById(uid);
      if (!el) return;
      if (el.classList.contains('expanded')) {
        el.classList.remove('expanded');
        // Re-truncate: trim to 300 chars and add ellipsis
        const full = btn.getAttribute('data-full');
        el.textContent = full.slice(0, 300) + '\n…';
        btn.textContent = '▼ show more (' + full.length.toLocaleString() + ' chars)';
      } else {
        el.classList.add('expanded');
        el.textContent = btn.getAttribute('data-full'); // safe: textContent, not innerHTML
        btn.textContent = '▲ show less';
      }
    }

    // ── search ────────────────────────────────────────────────────
    let searchDebounce = null;
    let activeQuery = '';

    function onSearch(val) {
      const q = val.trim();
      document.getElementById('search-clear').style.opacity = q ? '1' : '0.3';
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => triggerSearch(q), 250);
    }

    function clearSearch() {
      document.getElementById('search-input').value = '';
      onSearch('');
    }

    async function triggerSearch(q) {
      activeQuery = q;
      // Reset to page 1 whenever entering or leaving search mode.
      if (q) currentPage = 1;
      const ind = document.getElementById('refresh-indicator');
      ind.textContent = q ? 'searching…' : 'refreshing…';
      try {
        const bbState = activeStateFilter ? (_UI_TO_BB_STATE[activeStateFilter] || activeStateFilter) : '';
        const stateQS = bbState ? `&state=${bbState}` : '';
        const offset = (currentPage - 1) * PAGE_SIZE;
        const url = q
          ? `/v1/jobs?limit=200&q=${encodeURIComponent(q)}${stateQS}`
          : `/v1/jobs?limit=${PAGE_SIZE}&offset=${offset}${stateQS}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        const raw = Array.isArray(data) ? data : (data.jobs || []);
        const jobs = raw.map(normalizeJob);
        _lastPageFull = !q && raw.length >= PAGE_SIZE;

        for (const j of jobs) {
          if (j.state === 'queued' || j.state === 'running') jobCache.delete(j.id);
        }

        renderJobs(jobs, /*append=*/false);
        const countEl = document.getElementById('search-count');
        countEl.textContent = q ? `${jobs.length} result${jobs.length === 1 ? '' : 's'}` : '';
        ind.textContent = 'updated ' + new Date().toLocaleTimeString();
        renderPager();
      } catch(e) {
        ind.textContent = 'error: ' + e.message;
      }
      fetchPoolStatus();
    }

    function applySearch() {} // no-op: search is server-side

    // ── job data cache ────────────────────────────────────────────
    const jobCache = new Map();

    // ── pagination state ──────────────────────────────────────────
    const PAGE_SIZE = 50;
    let currentPage = 1;   // 1-based
    let _lastPageFull = false;  // last list page returned a full PAGE_SIZE → a Next exists

    function goToPage(p) {
      // No aggregate total on the host; Next is gated by _lastPageFull in the pager.
      currentPage = Math.max(1, p);
      fetchJobs();
    }

    function renderPager() {
      const el = document.getElementById('pager');
      if (!el) return;
      // No pager during a text search (server returns up to 200 results
      // in a single shot; pagination over search would need a separate
      // store API).
      if (activeQuery) {
        el.innerHTML = '';
        return;
      }
      // The host returns no aggregate count, so there's no "page N/total" or
      // last-page jump — just Prev/Next, with Next gated on the last page being
      // full (a partial page means we've reached the end).
      const pg = (label, page, disabled) => disabled
        ? `<span class="pg disabled">${label}</span>`
        : `<span class="pg" data-act="go-page" data-arg="${page}">${label}</span>`;
      const parts = [
        pg('‹ Prev', currentPage - 1, currentPage === 1),
        `<span class="count">page ${currentPage}</span>`,
        pg('Next ›', currentPage + 1, !_lastPageFull),
      ];
      el.innerHTML = parts.join('');
    }

    // ── state-filter pills ────────────────────────────────────────
    let activeStateFilter = null; // null | "queued" | "running" | "succeeded" | "failed"

    function setStateFilter(state) {
      // Toggle off if already active
      activeStateFilter = (activeStateFilter === state) ? null : state;
      renderStatePills();
      // Clear any text-search so the two filters don't fight
      const inp = document.getElementById('search-input');
      if (inp.value) { inp.value = ''; activeQuery = ''; }
      // Reset to first page when filter changes
      currentPage = 1;
      fetchJobs();
    }

    function renderStatePills() {
      // Pure filter pills — the host exposes no aggregate per-state tally, so we
      // drop the live count badges and keep the pills as state filters.
      const states = [
        { key: null,        label: 'All' },
        { key: 'queued',    label: 'Queued' },
        { key: 'running',   label: 'Running' },
        { key: 'succeeded', label: 'Succeeded' },
        { key: 'failed',    label: 'Failed' },
      ];
      const el = document.getElementById('state-pills');
      if (!el) return;
      el.innerHTML = states.map(s => {
        const active = (activeStateFilter === s.key);
        const classes = 'pill' + (s.key ? ' pill-' + s.key : '') + (active ? ' active' : '');
        // data-act delegation (CSP blocks inline onclick); set-state handler
        // reads dataset.arg, falling back to null for the "all" pill.
        const act = s.key ? `data-act="set-state" data-arg="${s.key}"` : 'data-act="set-state"';
        return `<span class="${classes}" ${act}>${s.label}</span>`;
      }).join('');
    }

    async function fetchJobCounts() {
      // blastbox.host has no aggregate /counts endpoint; the pills are pure
      // filters and the pager infers paging from page fullness. Keep the pills
      // rendered (and their active-state highlight in sync) — that's all.
      renderStatePills();
    }

    // ── delete ────────────────────────────────────────────────────
    async function deleteJob(id, btn) {
      if (!confirm('Delete job '+id.slice(0,8)+'?')) return;
      btn.disabled = true;
      try {
        const r = await fetch('/v1/jobs/'+id, {method:'DELETE'});
        if (r.ok||r.status===204) {
          jobCache.delete(id);
          fetchJobs();
        } else {
          const d = await r.json().catch(()=>({detail:'unknown'}));
          alert('Delete failed: '+d.detail);
          btn.disabled = false;
        }
      } catch(e) { alert('Delete failed: '+e.message); btn.disabled=false; }
    }

    // ── client-side routing ───────────────────────────────────────
    //
    //   /              → recent-jobs list view
    //   /jobs/<uuid>   → dedicated detail view for one job
    //
    // The expand-in-place pattern (toggleExpand / openExpand / loadExpand /
    // applyJobDeepLink + a synthetic-row hoist) we used before lived inside
    // the table and fought every poll / pagination / deep-link flow. The
    // click-into pattern is plain SPA routing: each row navigates to its own
    // route, the detail view has the whole viewport to itself, and back /
    // forward buttons + share-as-URL just work.
    let detailPollTimer = null;
    const listPollTimers = [];

    function currentRoute() {
      const m = window.location.pathname.match(/^\/jobs\/([0-9a-fA-F-]+)$/);
      return m ? { kind: 'job', id: m[1] } : { kind: 'list' };
    }

    function navigateToJob(id) {
      const r = currentRoute();
      if (r.kind === 'job' && r.id === id) return;  // already there
      history.pushState({}, '', '/jobs/' + encodeURIComponent(id));
      renderRoute();
    }

    function navigateToList() {
      if (currentRoute().kind === 'list') return;
      history.pushState({}, '', '/');
      renderRoute();
    }

    function stopAllPolls() {
      while (listPollTimers.length) clearInterval(listPollTimers.pop());
      if (detailPollTimer) { clearTimeout(detailPollTimer); detailPollTimer = null; }
    }

    function renderRoute() {
      // Close the slide-out similar-entries panel on every navigation so it
      // doesn't carry stale state from a previous view.
      document.getElementById('similar-panel')?.classList.remove('show');
      const route = currentRoute();
      if (route.kind === 'job') {
        showJobDetailView(route.id);
      } else {
        showListView();
      }
    }

    window.addEventListener('popstate', renderRoute);

    function showListView() {
      stopAllPolls();
      document.getElementById('detail-view').style.display = 'none';
      document.getElementById('list-view').style.display = '';
      fetchJobs();
      fetchJobCounts();
      fetchPoolStatus();
      listPollTimers.push(setInterval(fetchJobs, 3000));
      listPollTimers.push(setInterval(fetchJobCounts, 3000));
      listPollTimers.push(setInterval(fetchPoolStatus, 3000));
    }

    async function showJobDetailView(id) {
      stopAllPolls();
      document.getElementById('list-view').style.display = 'none';
      document.getElementById('detail-view').style.display = '';
      const idEl = document.getElementById('detail-id');
      if (idEl) idEl.textContent = id;
      const stateEl = document.getElementById('detail-state');
      if (stateEl) stateEl.innerHTML = '';

      const content = document.getElementById('detail-content');
      content.innerHTML = '<div style="padding:1.5rem;color:#888">Loading…</div>';

      try {
        // Skip cache when navigating to this view — caches go stale fast for
        // queued/running jobs and the per-job fetch is ~6 ms anyway.
        const r = await fetch('/v1/jobs/' + encodeURIComponent(id));
        if (!r.ok) {
          content.innerHTML = '<div style="padding:1.5rem;color:#ef5350">Job not found (HTTP ' + r.status + ')</div>';
          return;
        }
        const job = normalizeJob(await r.json());
        _curArtMap = {};
        if (job.state === 'succeeded') {
          // Prefer the sealed envelope: it carries the embedded rmeta document
          // (redtusk_rmeta) — exactly the {extraction,input,sandbox,…} shape
          // buildJobView consumes — AND the declared artifacts[] (path→id) needed
          // to resolve thumbnails. One fetch covers both.
          try {
            const mr = await fetch('/v1/jobs/' + encodeURIComponent(id) + '/metadata');
            if (mr.ok) {
              const env = await mr.json();
              for (const a of (env.artifacts || [])) {
                if (a && a.path && a.id) _curArtMap[a.path] = a.id;
              }
              const fields = (((env.payload || {}).metadata) || {}).fields || {};
              const rj = fields.redtusk_rmeta;
              if (typeof rj === 'string' && rj) {
                try { job.result = JSON.parse(rj); } catch { job.result = null; }
              }
            }
          } catch { /* fall through to the legacy /rmeta route */ }
          // Fallback for jobs sealed before the embed (no redtusk_rmeta field):
          // the legacy /rmeta route still serves their declared rmeta/metadata.json.
          if (!job.result) {
            try {
              const rr = await fetch('/v1/jobs/' + encodeURIComponent(id) + '/rmeta');
              if (rr.ok) job.result = await rr.json();
            } catch { /* viewer degrades to summary-only */ }
          }
        }
        renderJobDetail(id, job);

        // Only poll while the job is in flight. Terminal jobs are immutable.
        if (job.state === 'queued' || job.state === 'running') {
          detailPollTimer = setTimeout(() => showJobDetailView(id), 3000);
        }
      } catch (e) {
        content.innerHTML = '<div style="padding:1.5rem;color:#ef5350">Failed: ' + esc(e.message) + '</div>';
      }
    }

    function renderJobDetail(id, job) {
      _lastJobDetail = { id, job };   // cache for the whitespace-collapse re-render
      const stateEl = document.getElementById('detail-state');
      if (stateEl) stateEl.innerHTML = stateCell(job.state);

      const content = document.getElementById('detail-content');
      let html = '<div class="expand-actions" style="margin-bottom:0.75rem">';
      if (job.state === 'succeeded') {
        html += '<a href="/v1/jobs/' + id + '/result" download><button class="dl">⬇ result.zip (pw: infected)</button></a>';
      }
      const isTerminal = job.state === 'succeeded' || job.state === 'failed';
      if (isTerminal) {
        html += '<button class="danger" data-act="delete-job" data-arg="' + esc(id) + '">Delete</button>';
      }
      if (job.result) {
        html += '<button class="dl" data-act="toggle-raw">{ } raw JSON</button>';
        html += '<button class="dl" data-act="toggle-ws">↹ whitespace: ' + (_wsCollapse ? 'collapsed' : 'raw') + '</button>';
      }
      html += '</div>';

      if (job.result) {
        html += '<pre id="raw-json-view" style="display:none;max-height:420px;overflow:auto;background:#0d0d0d;color:#cfcfcf;padding:0.75rem;border-radius:4px;font:0.72rem/1.45 \'Courier New\',monospace;white-space:pre;margin-bottom:0.75rem">' + esc(JSON.stringify(job, null, 2)) + '</pre>';
      }

      if (job.state === 'failed') {
        html += '<div style="color:#ef5350;font-size:0.9rem;margin-bottom:0.75rem">' + esc(job.error_detail || 'Worker error') + '</div>';
      }
      if (job.result) {
        html += buildJobView(job, id);
      } else if (job.state === 'queued' || job.state === 'running') {
        html += '<span style="color:#888">' + job.state + '… (auto-refreshing every 3 s)</span>';
      }
      content.innerHTML = html;
    }

    async function deleteJobAndGoBack(id) {
      if (!confirm('Delete job ' + id + '?')) return;
      try {
        const r = await fetch('/v1/jobs/' + id, { method: 'DELETE' });
        if (r.ok) {
          navigateToList();
        } else {
          let detail = 'unknown';
          try { detail = (await r.json()).detail || detail; } catch {}
          alert('Delete failed: ' + detail);
        }
      } catch (e) {
        alert('Delete failed: ' + e.message);
      }
    }

    // ── pool status ───────────────────────────────────────────────
    async function fetchPoolStatus() {
      try {
        const text = await fetch('/metrics').then(r=>r.text());
        const el = document.getElementById('pool-status');
        const stats = {};
        for (const line of text.split('\n')) {
          // blastbox names the gauge blastbox_pool_slots. NB: in the split api/
          // dispatcher topology the pool lives in the dispatcher, so the api's
          // /metrics usually has no slot gauge — the widget then renders empty.
          const m = line.match(/^blastbox_pool_slots\{state="(\w+)"\}\s+(\d+)/);
          if (m) stats[m[1]]=parseInt(m[2]);
        }
        if (!Object.keys(stats).length) { el.innerHTML=''; return; }
        const colors = {idle:'slot-idle',assigned:'slot-assigned',warming:'slot-warming'};
        let html='<span>Pool:</span>';
        for (const [state,count] of Object.entries(stats)) {
          const cls=colors[state]||'';
          for (let i=0;i<Math.min(count,24);i++) html+='<span class="pool-slot '+cls+'" title="'+state+'"></span>';
          if (count>24) html+='<span>+'+( count-24)+'</span>';
        }
        const total=Object.values(stats).reduce((a,b)=>a+b,0);
        html+='<span>'+total+' slots</span>';
        el.innerHTML=html;
      } catch {}
    }

    // ── jobs table ────────────────────────────────────────────────
    function stateCell(s) {
      return '<span class="state state-'+(s||'queued')+'">'+esc(s||'queued')+'</span>';
    }
    function qrCell(job) {
      // List responses carry qr_count summary; individual fetches have full result
      const n = (job.qr_count != null) ? job.qr_count
              : (job.result?.extraction?.entries||[]).reduce((s,e)=>s+(e.qr?.codes||[]).length,0);
      return n ? '<span class="qr-badge">QR×'+n+'</span>' : '—';
    }

    async function fetchJobs() {
      const ind = document.getElementById('refresh-indicator');
      ind.textContent='refreshing…';
      try {
        // Search: fetch up to 200 results, single shot, no pagination.
        // Normal: fetch the current page via offset=(page-1)*PAGE_SIZE.
        // State filter layers on top of either mode (mapped to host states).
        const bbState = activeStateFilter ? (_UI_TO_BB_STATE[activeStateFilter] || activeStateFilter) : '';
        const stateQS = bbState ? `&state=${bbState}` : '';
        const offset = (currentPage - 1) * PAGE_SIZE;
        const url = activeQuery
          ? `/v1/jobs?limit=200&q=${encodeURIComponent(activeQuery)}${stateQS}`
          : `/v1/jobs?limit=${PAGE_SIZE}&offset=${offset}${stateQS}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('HTTP '+resp.status);
        const data = await resp.json();
        const raw = Array.isArray(data) ? data : (data.jobs||[]);
        const jobs = raw.map(normalizeJob);
        // The host returns no total count; the pager infers "more" from a full page.
        _lastPageFull = !activeQuery && raw.length >= PAGE_SIZE;

        for (const j of jobs) {
          // List response is summary-only; evict stale in-flight entries.
          if (j.state==='queued'||j.state==='running') jobCache.delete(j.id);
        }

        renderJobs(jobs, /*append=*/false);
        ind.textContent='updated '+new Date().toLocaleTimeString();
        renderPager();
      } catch(e) { ind.textContent='error: '+e.message; }
      fetchPoolStatus();
    }

    function rowCells(job) {
      const fullId = job.id || '';
      const fullName = job.filename_hint || '—';
      return '<td class="cell-id" title="'+esc(fullId)+'" style="font-size:0.72rem;letter-spacing:-0.01em">'+esc(fullId)+'</td>'+
        '<td class="cell-truncate" title="'+esc(fullName)+'">'+esc(fullName)+'</td>'+
        '<td>'+stateCell(job.state)+'</td>'+
        '<td>'+relativeTime(job.submitted_at)+'</td>'+
        '<td>'+duration(job)+'</td>'+
        '<td>'+qrCell(job)+'</td>';
    }

    function renderJobs(jobs, append) {
      const tbody = document.getElementById('jobs-body');

      if (append) {
        // Append-only mode: just add new rows at the end of the tbody.
        // Do not touch existing rows.
        for (const job of jobs) {
          if (document.getElementById('row-'+job.id)) continue; // already present
          const tr = document.createElement('tr');
          tr.id='row-'+job.id;
          tr.className='job-row';
          tr.innerHTML = rowCells(job);
          tr.addEventListener('click', ()=>navigateToJob(job.id));
          tbody.appendChild(tr);
        }
        return;
      }

      // Reconcile (append=false) mode.

      // Remove placeholder rows (Loading…, No jobs yet.) before reconciling.
      for (const tr of [...tbody.querySelectorAll('tr:not(.job-row)')]) {
        tr.remove();
      }

      if (!jobs.length) {
        tbody.innerHTML='<tr><td colspan="6" class="no-jobs">No jobs yet.</td></tr>';
        return;
      }

      const jobIds = new Set(jobs.map(j=>j.id));

      // 1. Remove rows whose jobs are no longer in the list. Since we
      //    navigated to /jobs/<id> for the detail view (no inline expansion
      //    here), there's no open panel to preserve — every off-page row
      //    can be evicted cleanly.
      for (const tr of [...tbody.querySelectorAll('tr.job-row')]) {
        const id = tr.id.replace('row-','');
        if (!jobIds.has(id)) tr.remove();
      }

      // 2. Insert/update rows in the API-returned order.
      //    Walk through jobs and ensure each row is in the right DOM position.
      //    Existing rows are updated in-place (mutable cells only).
      let cursor = tbody.firstChild; // DOM position we're placing rows at

      for (const job of jobs) {
        let tr = document.getElementById('row-'+job.id);

        if (tr) {
          // Update the four mutable cells (state, relative-time, duration, qr)
          const tds = tr.querySelectorAll('td');
          if (tds[2]) tds[2].innerHTML = stateCell(job.state);
          if (tds[3]) tds[3].textContent = relativeTime(job.submitted_at);
          if (tds[4]) tds[4].textContent = duration(job);
          if (tds[5]) tds[5].innerHTML = qrCell(job);
        } else {
          // New row
          tr = document.createElement('tr');
          tr.id='row-'+job.id;
          tr.className='job-row';
          tr.innerHTML = rowCells(job);
          tr.addEventListener('click', ()=>navigateToJob(job.id));
        }

        // Move/insert job row at the cursor position
        if (tr !== cursor) tbody.insertBefore(tr, cursor);
        cursor = tr.nextSibling;
      }
    }

    // ── boot ──────────────────────────────────────────────────────
    document.getElementById('search-clear').style.opacity = '0.3';

    // Legacy ?job=<id> URLs still floating around in bookmarks / history —
    // rewrite to /jobs/<id> once on load before the router reads the URL.
    (function migrateLegacyJobQuery() {
      const legacy = new URLSearchParams(window.location.search).get('job');
      if (legacy) {
        history.replaceState({}, '', '/jobs/' + encodeURIComponent(legacy));
      }
    })();

    // Boot the router. showListView / showJobDetailView wire up their own
    // poll intervals via stopAllPolls() + setInterval; there are no
    // top-level setIntervals anymore.
    renderRoute();
  
