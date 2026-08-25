// ============================================
// VAULT NOTES — shared terminal notepad
// Self-contained: injects its own CSS + markup.
// Works on every page; per-account when the host
// page defines window.tvGetAccount().
// ============================================
(function () {
    const CSS = `
        .term-fab { position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 300; display: inline-flex; align-items: center; gap: 0.55rem; padding: 0.6rem 1.15rem; border-radius: 100px; background: linear-gradient(135deg, #0D0714, #140C1F); border: 1px solid rgba(212,175,55,0.28); cursor: pointer; box-shadow: 0 8px 28px rgba(0,0,0,0.55), 0 0 24px rgba(139,92,246,0.16); transition: all 0.3s; font-family: 'JetBrains Mono', monospace; }
        .term-fab .term-fab-icon { color: #D4AF37; font-size: 0.95rem; font-weight: 700; line-height: 1; }
        .term-fab .term-fab-label { color: #B9ABCE; font-size: 0.66rem; letter-spacing: 0.18em; font-weight: 500; }
        .term-fab { animation: termGlow 3.2s ease-in-out infinite; }
        @keyframes termGlow {
            0%, 100% { box-shadow: 0 8px 28px rgba(0,0,0,0.55), 0 0 20px rgba(212,175,55,0.3); border-color: rgba(212,175,55,0.4); }
            50% { box-shadow: 0 8px 28px rgba(0,0,0,0.55), 0 0 36px rgba(139,92,246,0.5); border-color: rgba(139,92,246,0.55); }
        }
        .term-caret { display: inline-block; animation: termBlink 1.1s steps(1) infinite; }
        @keyframes termBlink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
        .term-fab:hover { border-color: #D4AF37; transform: translateY(-2px); box-shadow: 0 12px 36px rgba(0,0,0,0.65), 0 0 40px rgba(212,175,55,0.35); animation-play-state: paused; }
        .term-fab:hover .term-fab-label { color: #F0DA9B; }
        .term-fab.term-shift { bottom: 6.5rem; }
        .term-window { position: fixed; bottom: 5.5rem; right: 1.5rem; width: min(540px, calc(100vw - 2rem)); height: 420px; z-index: 310; display: none; flex-direction: column; border-radius: 14px; overflow: hidden; background: rgba(7,4,10,0.97); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(212,175,55,0.28); box-shadow: 0 30px 80px rgba(0,0,0,0.7), 0 0 44px rgba(139,92,246,0.14); transition: width 0.35s ease, height 0.35s ease; }
        .term-window.term-shift { bottom: 10.5rem; }
        .term-window.open { display: flex; animation: termIn 0.3s ease; }
        .term-window.max { width: min(920px, calc(100vw - 2rem)); height: min(660px, calc(100vh - 2rem)); }
        @keyframes termIn { from { opacity: 0; } to { opacity: 1; } }
        .term-bar { display: flex; align-items: center; gap: 0.6rem; padding: 0.55rem 0.9rem; background: linear-gradient(90deg, rgba(212,175,55,0.07), transparent 40%), #0C0713; border-bottom: 1px solid rgba(212,175,55,0.15); font-family: 'JetBrains Mono', monospace; flex-shrink: 0; cursor: grab; user-select: none; touch-action: none; }
        .term-window.dragging .term-bar { cursor: grabbing; }
        .term-window.dragging { transition: none; }
        .term-window.max { left: 50% !important; top: 50% !important; right: auto !important; bottom: auto !important; transform: translate(-50%, -50%); }
        .term-window::after { content: ''; position: absolute; inset: 0; pointer-events: none; z-index: 5;
            background: repeating-linear-gradient(180deg, transparent 0 3px, rgba(139,92,246,0.035) 3px 4px);
            animation: termCRT 7s ease-in-out infinite; }
        @keyframes termCRT { 0%, 100% { opacity: 0.9; } 50% { opacity: 0.55; } }
        .term-window.open { box-shadow: 0 30px 80px rgba(0,0,0,0.7), 0 0 44px rgba(139,92,246,0.22), inset 0 0 60px rgba(74,44,110,0.12); }
        @media (prefers-reduced-motion: reduce) { .term-fab, .term-caret, .term-window::after { animation: none !important; } }
        .term-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
        .term-title { font-size: 0.62rem; letter-spacing: 0.14em; color: #D4AF37; }
        .term-acct { font-size: 0.58rem; color: #665A7E; }
        .term-btns { margin-left: auto; display: flex; gap: 0.35rem; }
        .term-btn { width: 22px; height: 22px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: transparent; color: #8C7CA6; font-size: 0.72rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s; font-family: 'JetBrains Mono', monospace; padding: 0; }
        .term-btn:hover { border-color: rgba(212,175,55,0.28); color: #D4AF37; }
        .term-body { flex: 1; overflow-y: auto; padding: 0.9rem 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; line-height: 1.75; scrollbar-width: thin; scrollbar-color: rgba(139,92,246,0.4) transparent; }
        .term-body::-webkit-scrollbar { width: 4px; } .term-body::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.35); border-radius: 2px; }
        .term-line { white-space: pre-wrap; word-break: break-word; color: #B9ABCE; }
        .term-line .ts { color: #665A7E; font-size: 0.62rem; margin-right: 0.55rem; }
        .term-line.sys { color: #665A7E; }
        .term-line.cmd { color: #F0DA9B; }
        .term-line.ai { color: #C4B5FD; }
        .term-line.ai::before { content: '◆ AI '; color: #8B5CF6; font-weight: 600; }
        .term-line.ai.term-typing::before { content: ''; }
        .term-tdot { display: inline-block; width: 5px; height: 5px; border-radius: 50%; background: #8B5CF6; margin-right: 3px; animation: termDot 1.2s infinite; }
        .term-tdot:nth-child(2) { animation-delay: 0.2s; } .term-tdot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes termDot { 0%, 100% { opacity: 0.25; } 50% { opacity: 1; } }
        .term-input-row { display: flex; align-items: center; gap: 0.55rem; padding: 0.65rem 0.95rem; border-top: 1px solid rgba(212,175,55,0.12); background: #090511; flex-shrink: 0; }
        .term-prompt { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #D4AF37; white-space: nowrap; }
        .term-input { flex: 1; background: transparent; border: none; outline: none; color: #FAFAFA; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; caret-color: #D4AF37; min-width: 0; }
        .term-input::placeholder { color: #665A7E; }
        @media (max-width: 640px) {
            .term-fab { bottom: 1rem; right: 1rem; padding: 0.5rem 0.95rem; }
            .term-fab.term-shift { bottom: 6rem; }
            .term-window { right: 0.5rem; bottom: 4.5rem; height: 60vh; }
            .term-window.term-shift { bottom: 10rem; }
        }
        @media print { .term-fab, .term-window { display: none !important; } }
    `;

    function init() {
        if (document.getElementById('termWin')) return;
        const style = document.createElement('style');
        style.textContent = CSS;
        document.head.appendChild(style);

        const fab = document.createElement('button');
        fab.className = 'term-fab'; fab.id = 'termFab';
        fab.title = 'Vault Notes — press ` to open';
        fab.innerHTML = '<span class="term-fab-icon">&gt;<span class="term-caret">_</span></span><span class="term-fab-label">NOTES</span>';
        const win = document.createElement('div');
        win.className = 'term-window'; win.id = 'termWin';
        win.setAttribute('role', 'dialog'); win.setAttribute('aria-label', 'Vault Notes terminal');
        win.innerHTML = `
            <div class="term-bar">
                <span style="display:flex;gap:5px;"><span class="term-dot" style="background:#F87171;"></span><span class="term-dot" style="background:#D4AF37;"></span><span class="term-dot" style="background:#34D399;"></span></span>
                <span class="term-title">VAULT NOTES</span>
                <span class="term-acct" id="termAcct"></span>
                <div class="term-btns">
                    <button class="term-btn" id="termMax" title="Maximize">⛶</button>
                    <button class="term-btn" id="termClose" title="Close (Esc)">×</button>
                </div>
            </div>
            <div class="term-body" id="termBody"></div>
            <div class="term-input-row">
                <span class="term-prompt" id="termPrompt">guest@vault:~$</span>
                <input class="term-input" id="termInput" autocomplete="off" spellcheck="false" placeholder="type any note… or /help">
            </div>`;
        document.body.appendChild(fab);
        document.body.appendChild(win);

        // Avoid overlapping the LYRA chat widget on pages that have it
        if (document.querySelector('.ai-chat-widget')) { fab.classList.add('term-shift'); win.classList.add('term-shift'); }

        const termBody = win.querySelector('#termBody');
        const termInput = win.querySelector('#termInput');
        const esc = s => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
        const rawAcct = () => (typeof window.tvGetAccount === 'function' && window.tvGetAccount()) || '';
        const acctLabel = () => { const a = rawAcct(); return a ? a.slice(0, 6) + '…' + a.slice(-4) : 'guest'; };
        const key = () => 'tvNotes:' + (rawAcct() ? rawAcct().toLowerCase() : 'guest');
        const toast = m => { if (typeof window.showToast === 'function') window.showToast(m); };
        const load = () => { try { return JSON.parse(localStorage.getItem(key())) || []; } catch (e) { return []; } };
        const saveAll = lines => { try { localStorage.setItem(key(), JSON.stringify(lines.slice(-500))); } catch (e) { toast('Storage full — /export then /clear to continue'); } };
        const push = entry => { const l = load(); l.push(entry); saveAll(l); };
        const stamp = () => { const d = new Date(); return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + ' ' + d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }); };

        function print(html, cls) {
            const d = document.createElement('div');
            d.className = 'term-line' + (cls ? ' ' + cls : '');
            d.innerHTML = html;
            termBody.appendChild(d);
            termBody.scrollTop = termBody.scrollHeight;
            return d;
        }
        function typeLine(el, text, speed) {
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = text; return; }
            el.textContent = '';
            const t0 = performance.now(), ms = speed || 11;
            const id = setInterval(() => {
                const i = Math.min(text.length, Math.floor((performance.now() - t0) / ms));
                el.textContent = text.slice(0, i) + (i < text.length ? '▌' : '');
                if (i >= text.length) clearInterval(id);
            }, 24);
        }
        function render() {
            termBody.innerHTML = '';
            win.querySelector('#termAcct').textContent = '· ' + acctLabel();
            win.querySelector('#termPrompt').textContent = acctLabel() + '@vault:~$';
            typeLine(print('', 'sys'), 'VAULT NOTES v1.0 — a terminal for your thoughts, saved per account');
            print('type anything to save a note · <b>/ai</b> &lt;question&gt; to discuss · <b>/help</b>', 'sys');
            print('', 'sys');
            load().forEach(l => {
                if (l.t === 'note') print('<span class="ts">' + esc(l.ts) + '</span>' + esc(l.text));
                else if (l.t === 'ask') print(esc('/ai ' + l.text), 'cmd');
                else if (l.t === 'ai') print(esc(l.text), 'ai');
            });
        }
        function notesAI(q) {
            const s = q.toLowerCase();
            if (s.includes('idea') || s.includes('concept')) return 'Interesting. Try splitting the idea into three note lines: the problem it solves, who it serves, and the smallest step you can test this week.';
            if (s.includes('todo') || s.includes('task') || s.includes('list')) return 'Tip: start each task note with [ ] — then search and mark it [x] when done. Want me to break that task into sub-steps?';
            if (s.includes('price') || s.includes('pricing') || s.includes('$tv')) return 'For pricing I defer to SOLON: anchor within the optimal band and note your reasoning here, so the decision can be audited later.';
            if (s.includes('plan') || s.includes('strategy') || s.includes('roadmap')) return 'A good plan fits in five lines. Note the end goal first, then work backwards: what must be true by month 3, month 1, this week?';
            if (s.includes('summar') || s.includes('recap') || s.includes('tldr')) return 'The thread across your notes this session: staged execution with proof at every step. Save a one-line conclusion so tomorrow picks up easily.';
            const generic = [
                'Good point to let settle. Write one more sentence: what decision follows from this?',
                'Context noted. Consider the opposite side too — what would make this assumption wrong?',
                'That idea deserves a small test first. What is the 1-hour version of it?',
                'Interesting — connect it to your earlier notes; the pattern that emerges is usually worth more than any single point.',
            ];
            return generic[Math.floor(Math.random() * generic.length)];
        }
        function aiReply(q) {
            const typing = print('<span class="term-tdot"></span><span class="term-tdot"></span><span class="term-tdot"></span>', 'ai term-typing');
            setTimeout(() => {
                const reply = notesAI(q);
                typing.classList.remove('term-typing');
                typing.textContent = reply;
                termBody.scrollTop = termBody.scrollHeight;
                push({ t: 'ai', text: reply });
            }, 900 + Math.random() * 700);
        }
        function exec(raw) {
            const text = raw.trim();
            if (!text) return;
            if (text.startsWith('/')) {
                const [cmd, ...rest] = text.split(' ');
                const arg = rest.join(' ').trim();
                if (cmd === '/help') {
                    print(esc(text), 'cmd');
                    print('/ai &lt;question&gt;   discuss with AI inside your notes\n/list            count notes for this account\n/export          download all notes (.txt)\n/clear           delete all notes for this account\n/help            this help\n\ndrag the title bar to move the window · double-click it to reset position', 'sys');
                } else if (cmd === '/list') {
                    print(esc(text), 'cmd');
                    print(load().filter(l => l.t === 'note').length + ' notes saved for ' + acctLabel(), 'sys');
                } else if (cmd === '/clear') {
                    print(esc(text), 'cmd');
                    localStorage.removeItem(key());
                    render();
                    print('All notes for ' + acctLabel() + ' cleared.', 'sys');
                } else if (cmd === '/export') {
                    print(esc(text), 'cmd');
                    const out = load().map(l => l.t === 'note' ? '[' + l.ts + '] ' + l.text : (l.t === 'ask' ? '> /ai ' + l.text : 'AI: ' + l.text)).join('\n');
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(new Blob([out], { type: 'text/plain' }));
                    a.download = 'vault-notes-' + acctLabel().replace('…', '-') + '.txt';
                    a.click(); URL.revokeObjectURL(a.href);
                    print('Notes exported.', 'sys');
                } else if (cmd === '/ai') {
                    if (!arg) { print(esc(text), 'cmd'); print('Usage: /ai <your question>', 'sys'); return; }
                    print(esc('/ai ' + arg), 'cmd');
                    push({ t: 'ask', text: arg });
                    aiReply(arg);
                } else {
                    print(esc(text), 'cmd');
                    print('Unknown command. Try /help', 'sys');
                }
            } else {
                const ts = stamp();
                push({ t: 'note', text, ts });
                print('<span class="ts">' + esc(ts) + '</span>' + esc(text));
            }
        }
        // --- Draggable window (position remembered) ---
        const POS_KEY = 'tvNotesPos';
        function setPos(x, y, save) {
            const r = win.getBoundingClientRect();
            x = Math.max(-(r.width - 110), Math.min(x, window.innerWidth - 110));
            y = Math.max(0, Math.min(y, window.innerHeight - 56));
            win.style.left = x + 'px'; win.style.top = y + 'px';
            win.style.right = 'auto'; win.style.bottom = 'auto';
            if (save) { try { localStorage.setItem(POS_KEY, JSON.stringify({ x: Math.round(x), y: Math.round(y) })); } catch (e) {} }
        }
        function applySavedPos() {
            let p = null;
            try { p = JSON.parse(localStorage.getItem(POS_KEY)); } catch (e) {}
            if (p && typeof p.x === 'number') setPos(p.x, p.y, false);
        }
        function resetPos() {
            try { localStorage.removeItem(POS_KEY); } catch (e) {}
            win.style.left = ''; win.style.top = ''; win.style.right = ''; win.style.bottom = '';
        }
        const bar = win.querySelector('.term-bar');
        let drag = null;
        bar.addEventListener('pointerdown', e => {
            if (e.target.closest('.term-btn') || win.classList.contains('max')) return;
            const r = win.getBoundingClientRect();
            drag = { dx: e.clientX - r.left, dy: e.clientY - r.top };
            win.classList.add('dragging');
            try { bar.setPointerCapture(e.pointerId); } catch (err) {}
        });
        bar.addEventListener('pointermove', e => { if (drag) setPos(e.clientX - drag.dx, e.clientY - drag.dy, true); });
        const endDrag = () => { drag = null; win.classList.remove('dragging'); };
        bar.addEventListener('pointerup', endDrag);
        bar.addEventListener('pointercancel', endDrag);
        bar.addEventListener('dblclick', e => { if (!e.target.closest('.term-btn')) { resetPos(); } });
        window.addEventListener('resize', () => {
            if (!win.classList.contains('open') || !win.style.left) return;
            setPos(parseFloat(win.style.left), parseFloat(win.style.top), true);
        });

        function toggle(open) {
            const willOpen = open !== undefined ? open : !win.classList.contains('open');
            win.classList.toggle('open', willOpen);
            if (willOpen) { render(); applySavedPos(); termInput.focus(); }
            else termInput.blur();
        }
        window.termToggle = toggle;

        fab.addEventListener('click', () => toggle());
        win.querySelector('#termClose').addEventListener('click', () => toggle(false));
        win.querySelector('#termMax').addEventListener('click', function () {
            win.classList.toggle('max');
            this.title = win.classList.contains('max') ? 'Restore' : 'Maximize';
            termInput.focus();
        });
        termInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') { exec(termInput.value); termInput.value = ''; }
            if (e.key === 'Escape') toggle(false);
        });
        // Summon: backtick — or just start typing outside any input
        document.addEventListener('keydown', e => {
            const ae = document.activeElement;
            const tag = (ae?.tagName || '').toLowerCase();
            const typingElsewhere = tag === 'input' || tag === 'textarea' || tag === 'select' || ae?.isContentEditable;
            if (e.key === '`' && !typingElsewhere) { e.preventDefault(); toggle(); return; }
            if (win.classList.contains('open') || typingElsewhere) return;
            if (document.querySelector('.modal-overlay.active, .panel-overlay.active, .tv-intro:not(.done)')) return;
            if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && /[\w\p{L}]/u.test(e.key)) {
                toggle(true);
                termInput.value = e.key;
                e.preventDefault();
            }
        });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
