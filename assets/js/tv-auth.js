// ============================================
// TIME VAULT: Login / Sign-up modal (DESIGN PREVIEW)
// Two paths: Connect Wallet (all EVM, via tv-auth-connect) and
// Email + Time Vault password with a verification-code step.
// UI/flow only. No backend yet. Wire to Privy/Supabase later.
// ============================================
(function () {
    const G = '#D4AF37', GB = '#F0DA9B';
    const CSS = `
    .tva-overlay{position:fixed;inset:0;z-index:420;background:rgba(0,0,0,0.78);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;padding:1.5rem;opacity:0;visibility:hidden;pointer-events:none;transition:opacity .25s,visibility .25s;}
    .tva-overlay.show{opacity:1;visibility:visible;pointer-events:auto;}
    .tva{width:min(420px,100%);border-radius:22px;padding:1px;background:linear-gradient(165deg,rgba(212,175,55,.6),rgba(212,175,55,.12) 28%,rgba(139,92,246,.4) 58%,rgba(192,38,211,.25) 78%,rgba(212,175,55,.5));box-shadow:0 40px 90px rgba(0,0,0,.75),0 0 50px rgba(139,92,246,.18);}
    .tva-in{background:linear-gradient(180deg,#140B20,#0A0512 72%);border-radius:21px;padding:2rem 1.9rem;position:relative;font-family:'Inter',sans-serif;}
    .tva-close{position:absolute;top:1rem;right:1.15rem;background:none;border:none;color:#8C7CA6;font-size:1.4rem;cursor:pointer;line-height:1;}
    .tva-close:hover{color:#FAFAFA;}
    .tva-head{text-align:center;margin-bottom:1.4rem;}
    .tva-head img{height:56px;width:auto;filter:drop-shadow(0 4px 16px rgba(139,92,246,.5));margin-bottom:.7rem;}
    .tva-head h3{font-family:'Cinzel',serif;font-size:1.35rem;color:#FAFAFA;letter-spacing:.04em;}
    .tva-head p{font-family:'JetBrains Mono',monospace;font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:${G};margin-top:.35rem;}
    .tva-tabs{display:flex;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:.25rem;margin-bottom:1.3rem;}
    .tva-tab{flex:1;text-align:center;padding:.6rem;border-radius:9px;font-size:.82rem;font-weight:500;color:#8C7CA6;cursor:pointer;border:none;background:transparent;font-family:'Inter',sans-serif;transition:all .3s;}
    .tva-tab.active{color:#0A0512;background:linear-gradient(135deg,${GB},${G});font-weight:600;}
    .tva-panel{display:none;flex-direction:column;gap:.75rem;}
    .tva-panel.active{display:flex;animation:tvaIn .3s ease;}
    @keyframes tvaIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}
    .tva-wallet-btn{display:flex;align-items:center;justify-content:center;gap:.5rem;padding:.95rem;border-radius:12px;border:1px solid var(--gold-line,rgba(212,175,55,.28));background:linear-gradient(135deg,#6D28D9,#C026D3);color:#fff;font-weight:600;font-size:.9rem;cursor:pointer;font-family:'Inter',sans-serif;box-shadow:inset 0 0 0 1px rgba(212,175,55,.3);transition:all .3s;}
    .tva-wallet-btn:hover{box-shadow:inset 0 0 0 1px rgba(212,175,55,.6),0 0 26px rgba(192,38,211,.35);}
    .tva-hint{text-align:center;font-size:.7rem;color:#665A7E;line-height:1.5;}
    .tva-hint b{color:#8C7CA6;font-weight:500;}
    .tva-seg{display:flex;gap:.4rem;margin-bottom:.4rem;}
    .tva-seg button{flex:1;padding:.5rem;font-size:.75rem;border-radius:8px;border:1px solid rgba(255,255,255,.08);background:transparent;color:#8C7CA6;cursor:pointer;font-family:'Inter',sans-serif;transition:all .3s;}
    .tva-seg button.on{border-color:rgba(212,175,55,.5);color:${G};background:rgba(212,175,55,.06);}
    .tva-lbl{font-family:'JetBrains Mono',monospace;font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:#665A7E;margin:.3rem 0 -.2rem;}
    .tva-inp{width:100%;padding:.8rem 1rem;border-radius:11px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.08);color:#FAFAFA;font-family:'Inter',sans-serif;font-size:.86rem;outline:none;transition:all .3s;}
    .tva-inp:focus{border-color:rgba(212,175,55,.5);box-shadow:0 0 0 3px rgba(212,175,55,.07);}
    .tva-inp::placeholder{color:#665A7E;}
    .tva-go{padding:.9rem;border-radius:11px;border:1px solid rgba(212,175,55,.3);background:linear-gradient(135deg,#6D28D9,#C026D3);color:#fff;font-weight:600;font-size:.88rem;cursor:pointer;font-family:'Inter',sans-serif;margin-top:.3rem;transition:all .3s;}
    .tva-go:hover{box-shadow:0 0 26px rgba(192,38,211,.4);}
    .tva-link{background:none;border:none;color:#8C7CA6;font-size:.72rem;cursor:pointer;text-align:center;font-family:'Inter',sans-serif;}
    .tva-link:hover{color:${G};}
    .tva-code-row{display:flex;gap:.5rem;justify-content:center;margin:.4rem 0;}
    .tva-code{width:44px;height:52px;text-align:center;font-family:'JetBrains Mono',monospace;font-size:1.3rem;color:#FAFAFA;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.1);border-radius:10px;outline:none;}
    .tva-code:focus{border-color:${G};box-shadow:0 0 0 3px rgba(212,175,55,.08);}
    .tva-sent{text-align:center;font-size:.78rem;color:#B9ABCE;line-height:1.6;}
    .tva-sent b{color:${GB};}
    .tva-foot{text-align:center;font-size:.62rem;color:#665A7E;margin-top:1.1rem;line-height:1.6;}
    .tva-preview{text-align:center;font-family:'JetBrains Mono',monospace;font-size:.54rem;letter-spacing:.14em;color:#8A6A1F;text-transform:uppercase;margin-top:.7rem;}
    .tva-acct{position:fixed;z-index:430;background:linear-gradient(180deg,#140B20,#0A0512);border:1px solid rgba(212,175,55,.3);border-radius:14px;padding:.7rem;min-width:230px;box-shadow:0 24px 60px rgba(0,0,0,.7),0 0 34px rgba(139,92,246,.15);font-family:'Inter',sans-serif;opacity:0;visibility:hidden;transform:translateY(-6px);transition:opacity .2s,visibility .2s,transform .2s;}
    .tva-acct.show{opacity:1;visibility:visible;transform:none;}
    .tva-acct .em{padding:.5rem .6rem;border-bottom:1px solid rgba(255,255,255,.07);margin-bottom:.5rem;}
    .tva-acct .em small{display:block;color:#8C7CA6;font-size:.55rem;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.25rem;}
    .tva-acct .em span{font-size:.8rem;color:#FAFAFA;word-break:break-all;}
    .tva-acct button{width:100%;padding:.62rem;border-radius:9px;border:1px solid rgba(255,255,255,.08);background:transparent;color:#E4B4C4;font-size:.82rem;font-weight:500;cursor:pointer;font-family:'Inter',sans-serif;transition:all .25s;}
    .tva-acct button:hover{border-color:rgba(192,38,211,.5);background:rgba(192,38,211,.12);color:#fff;}
    .tva-pwreq{display:flex;flex-wrap:wrap;gap:.3rem .8rem;margin:.15rem 0 .1rem;font-family:'Inter',sans-serif;font-size:.62rem;color:#665A7E;}
    .tva-pwreq span{display:flex;align-items:center;gap:.28rem;transition:color .25s;}
    .tva-pwreq span::before{content:'○';font-size:.66rem;opacity:.8;}
    .tva-pwreq span.ok{color:#5BD6A0;}
    .tva-pwreq span.ok::before{content:'✓';}
    .tva-err{display:none;margin:.2rem 0 .1rem;padding:.55rem .7rem;border-radius:9px;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.38);color:#FCA5A5;font-size:.72rem;line-height:1.45;font-family:'Inter',sans-serif;}
    .tva-err.show{display:block;animation:tvaIn .25s ease;}
    `;

    function el(html) { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstChild; }
    function toast(m) { if (window.showToast) window.showToast(m); }
    // Errors must be readable inside the modal, since a page toast can sit behind the overlay.
    function showErr(m) {
        const e = overlay && overlay.querySelector('#tvaErr');
        if (e) { e.textContent = m; e.classList.add('show'); }
        toast(m);
    }
    function clearErr() {
        const e = overlay && overlay.querySelector('#tvaErr');
        if (e) { e.classList.remove('show'); e.textContent = ''; }
    }

    // ---- Password strength (Create account) ----
    const PW_SYMBOLS = /[!@#$%^&*()_+\-=\[\]{}|;,.<>?]/;
    function pwChecks(pw) {
        return { len: pw.length >= 8, lower: /[a-z]/.test(pw), upper: /[A-Z]/.test(pw), digit: /[0-9]/.test(pw), sym: PW_SYMBOLS.test(pw) };
    }
    function pwStrong(pw) { const c = pwChecks(pw); return c.len && c.lower && c.upper && c.digit && c.sym; }
    function updatePwReq() {
        const inp = overlay.querySelector('#tvaPassInp'); const box = overlay.querySelector('#tvaPwReq');
        if (!inp || !box) return;
        const c = pwChecks(inp.value);
        box.querySelectorAll('span').forEach(s => s.classList.toggle('ok', !!c[s.dataset.r]));
    }

    // ---- Supabase (publishable key is safe in the browser) ----
    const SUPABASE_URL = 'https://jrqhizztseexxippymti.supabase.co';
    const SUPABASE_KEY = 'sb_publishable_0YSoYtjszO3bXxC-N4Fj2w_rfzT3tkV';
    let _sb = null, _sbLoading = null;
    async function supa() {
        if (_sb) return _sb;
        if (!_sbLoading) _sbLoading = import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm')
            .then(m => { _sb = m.createClient(SUPABASE_URL, SUPABASE_KEY, { auth: { persistSession: true, autoRefreshToken: true } }); return _sb; });
        return _sbLoading;
    }
    function onAuthed(user) {
        if (!user) return;
        currentUser = user;
        const label = user.email ? user.email.split('@')[0] : 'Account';
        document.querySelectorAll('.wallet-btn, #walletBtn').forEach(b => {
            b.classList.add('connected');
            const t = b.querySelector('#walletText') || b.querySelector('[id$="walletText"]');
            if (t) t.textContent = label;
        });
    }

    let overlay, view = 'wallet', emailMode = 'signup', pendingEmail = '', currentUser = null, acctMenu = null;

    function build() {
        const style = document.createElement('style'); style.textContent = CSS; document.head.appendChild(style);
        overlay = el(`
        <div class="tva-overlay" id="tvaOverlay" role="dialog" aria-label="Sign in to Time Vault">
          <div class="tva"><div class="tva-in">
            <button class="tva-close" id="tvaClose" aria-label="Close">&times;</button>
            <div class="tva-head">
              <img src="assets/logo.png" alt="">
              <h3>Enter Time Vault</h3>
              <p>Sign in or create your account</p>
            </div>
            <div class="tva-tabs">
              <button class="tva-tab active" data-v="wallet">Wallet</button>
              <button class="tva-tab" data-v="email">Email</button>
            </div>

            <div class="tva-panel active" id="tvaWallet">
              <button class="tva-wallet-btn" id="tvaConnect">◇ Connect Wallet</button>
              <div class="tva-hint">Works with <b>every EVM wallet</b>: MetaMask, Rabby, OKX, Coinbase, Trust, Brave &amp; more.</div>
            </div>

            <div class="tva-panel" id="tvaEmail">
              <div class="tva-seg">
                <button data-m="signup" class="on">Create account</button>
                <button data-m="signin">Sign in</button>
              </div>
              <div class="tva-err" id="tvaErr" role="alert"></div>
              <div id="tvaForm">
                <div class="tva-lbl">Email address</div>
                <input class="tva-inp" id="tvaEmailInp" type="email" placeholder="you@email.com" autocomplete="email">
                <div class="tva-lbl">Time Vault password</div>
                <input class="tva-inp" id="tvaPassInp" type="password" placeholder="Create a strong password" autocomplete="new-password">
                <div class="tva-pwreq" id="tvaPwReq">
                  <span data-r="len">8+ characters</span>
                  <span data-r="lower">lowercase</span>
                  <span data-r="upper">uppercase</span>
                  <span data-r="digit">number</span>
                  <span data-r="sym">symbol</span>
                </div>
                <button class="tva-go" id="tvaSubmit" style="width:100%;">Create account</button>
                <div class="tva-hint" style="margin-top:.5rem;">Your password is for <b>Time Vault only</b>, never your email provider's.</div>
              </div>
              <div id="tvaCode" style="display:none;">
                <div class="tva-sent">We sent a 6-digit code to<br><b id="tvaSentTo">your email</b></div>
                <div class="tva-code-row">
                  <input class="tva-code" maxlength="1" inputmode="numeric"><input class="tva-code" maxlength="1" inputmode="numeric"><input class="tva-code" maxlength="1" inputmode="numeric"><input class="tva-code" maxlength="1" inputmode="numeric"><input class="tva-code" maxlength="1" inputmode="numeric"><input class="tva-code" maxlength="1" inputmode="numeric">
                </div>
                <button class="tva-go" id="tvaVerify" style="width:100%;">Verify &amp; continue</button>
                <button class="tva-link" id="tvaResend" style="width:100%;margin-top:.5rem;">Resend code · Change email</button>
              </div>
            </div>

            <div class="tva-foot">By continuing you agree to the Terms &amp; Privacy Policy.</div>
            <div class="tva-preview">Encrypted &amp; secured · we never see your email password</div>
          </div></div>
        </div>`);
        document.body.appendChild(overlay);

        overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
        overlay.querySelector('#tvaClose').addEventListener('click', close);
        overlay.querySelectorAll('.tva-tab').forEach(t => t.addEventListener('click', () => setView(t.dataset.v)));
        overlay.querySelectorAll('.tva-seg button').forEach(s => s.addEventListener('click', () => setEmailMode(s.dataset.m)));

        overlay.querySelector('#tvaConnect').addEventListener('click', async () => {
            close(); // close this modal first so the wallet picker isn't hidden behind it
            try {
                const r = await window.tvConnectWallet();
                toast('Connected via ' + r.walletName);
                currentUser = { email: r.address.slice(0, 6) + '...' + r.address.slice(-4), wallet: true };
                document.querySelectorAll('.wallet-btn, #walletBtn').forEach(b => {
                    const txt = b.querySelector('#walletText') || b.querySelector('[id$="walletText"]');
                    b.classList.add('connected');
                    if (txt) txt.textContent = r.address.slice(0, 6) + '...' + r.address.slice(-4);
                });
            } catch (err) { if (err && (err.message === 'CANCELLED' || err.message === 'NO_WALLET')) return; toast('Connection failed'); }
        });

        overlay.querySelector('#tvaSubmit').addEventListener('click', async () => {
            const email = overlay.querySelector('#tvaEmailInp').value.trim();
            const password = overlay.querySelector('#tvaPassInp').value;
            clearErr();
            if (!/.+@.+\..+/.test(email)) { showErr('Enter a valid email address'); return; }
            if (emailMode === 'signup') {
                if (!pwStrong(password)) {
                    const c = pwChecks(password);
                    const missing = [['len','8+ characters'],['lower','a lowercase letter'],['upper','an uppercase letter'],['digit','a number'],['sym','a symbol (e.g. ! @ # $)']].filter(([k]) => !c[k]).map(([, l]) => l);
                    showErr('Your password still needs: ' + missing.join(', ') + '.');
                    updatePwReq(); return;
                }
            } else if (!password) { showErr('Enter your password'); return; }
            const btn = overlay.querySelector('#tvaSubmit');
            btn.disabled = true; const orig = btn.textContent; btn.textContent = 'Please wait…';
            try {
                const client = await supa();
                if (emailMode === 'signup') {
                    const { data, error } = await client.auth.signUp({ email, password });
                    if (error) throw error;
                    pendingEmail = email;
                    // Supabase hides "already registered" by returning a user with no identities and
                    // sending no code. Detect it so we don't show a code screen that never fills.
                    if (data.user && Array.isArray(data.user.identities) && data.user.identities.length === 0) {
                        setEmailMode('signin');
                        showErr('This email is already registered. Enter your password to sign in.');
                        overlay.querySelector('#tvaEmailInp').value = email;
                        overlay.querySelector('#tvaPassInp').value = '';
                        overlay.querySelector('#tvaPassInp').focus();
                        return;
                    }
                    if (data.session) { close(); onAuthed(data.user); toast('Welcome to Time Vault'); }
                    else {
                        overlay.querySelector('#tvaSentTo').textContent = email;
                        overlay.querySelector('#tvaForm').style.display = 'none';
                        overlay.querySelector('#tvaCode').style.display = 'block';
                        overlay.querySelector('.tva-code').focus();
                        toast('Verification code sent to your email');
                    }
                } else {
                    const { data, error } = await client.auth.signInWithPassword({ email, password });
                    if (error) throw error;
                    close(); onAuthed(data.user); toast('Signed in');
                }
            } catch (e) {
                const msg = (e && e.message) || 'Something went wrong';
                showErr(/already registered/i.test(msg) ? 'This email is already registered. Sign in instead.' : msg);
            } finally { btn.disabled = false; btn.textContent = orig; }
        });

        overlay.querySelector('#tvaPassInp').addEventListener('input', updatePwReq);

        // code auto-advance
        const codes = [...overlay.querySelectorAll('.tva-code')];
        codes.forEach((c, i) => {
            c.addEventListener('input', () => { if (c.value && i < codes.length - 1) codes[i + 1].focus(); });
            c.addEventListener('keydown', e => { if (e.key === 'Backspace' && !c.value && i > 0) codes[i - 1].focus(); });
        });
        overlay.querySelector('#tvaVerify').addEventListener('click', async () => {
            clearErr();
            const token = codes.map(c => c.value).join('');
            if (token.length < 6) { showErr('Enter all 6 digits of the code'); return; }
            const vb = overlay.querySelector('#tvaVerify');
            vb.disabled = true; const orig = vb.textContent; vb.textContent = 'Verifying…';
            try {
                const client = await supa();
                const { data, error } = await client.auth.verifyOtp({ email: pendingEmail, token, type: 'signup' });
                if (error) throw error;
                close(); onAuthed(data.user); toast('Time Vault account created');
            } catch (e) {
                showErr((e && e.message) || 'That code is invalid or has expired. Check the newest email.');
            } finally { vb.disabled = false; vb.textContent = orig; }
        });
        overlay.querySelector('#tvaResend').addEventListener('click', () => {
            overlay.querySelector('#tvaCode').style.display = 'none';
            overlay.querySelector('#tvaForm').style.display = 'block';
            codes.forEach(c => c.value = '');
        });

        // intercept the nav button: open login when signed out, or the account menu when signed in
        document.addEventListener('click', e => {
            const btn = e.target.closest('.wallet-btn, #walletBtn');
            if (btn && !overlay.contains(btn)) {
                e.preventDefault(); e.stopImmediatePropagation();
                if (currentUser) showAcctMenu(btn); else open();
            }
        }, true);
    }

    function setView(v) {
        view = v;
        overlay.querySelectorAll('.tva-tab').forEach(t => t.classList.toggle('active', t.dataset.v === v));
        overlay.querySelector('#tvaWallet').classList.toggle('active', v === 'wallet');
        overlay.querySelector('#tvaEmail').classList.toggle('active', v === 'email');
    }
    function setEmailMode(m) {
        emailMode = m;
        clearErr();
        overlay.querySelectorAll('.tva-seg button').forEach(s => s.classList.toggle('on', s.dataset.m === m));
        overlay.querySelector('#tvaCode').style.display = 'none';
        overlay.querySelector('#tvaForm').style.display = 'block';
        overlay.querySelector('#tvaSubmit').textContent = m === 'signup' ? 'Create account' : 'Sign in';
        overlay.querySelector('#tvaPassInp').placeholder = m === 'signup' ? 'Create a strong password' : 'Your password';
        const req = overlay.querySelector('#tvaPwReq');
        if (req) req.style.display = m === 'signup' ? 'flex' : 'none';
        updatePwReq();
    }
    function open() { overlay.classList.add('show'); requestAnimationFrame(() => overlay.classList.add('show')); }
    function close() { overlay.classList.remove('show'); }
    window.tvOpenLogin = open;

    function buildAcctMenu() {
        acctMenu = el(`<div class="tva-acct" id="tvaAcct"><div class="em"><small>Signed in as</small><span id="tvaAcctEmail"></span></div><button id="tvaSignOut">Sign out</button></div>`);
        document.body.appendChild(acctMenu);
        acctMenu.querySelector('#tvaSignOut').addEventListener('click', signOut);
        document.addEventListener('click', e => {
            if (acctMenu.classList.contains('show') && !acctMenu.contains(e.target) && !e.target.closest('.wallet-btn, #walletBtn')) hideAcct();
        });
        window.addEventListener('resize', hideAcct);
    }
    function showAcctMenu(anchor) {
        if (!acctMenu) buildAcctMenu();
        acctMenu.querySelector('#tvaAcctEmail').textContent = (currentUser && currentUser.email) ? currentUser.email : 'Account';
        const r = anchor.getBoundingClientRect();
        acctMenu.style.top = (r.bottom + 8) + 'px';
        acctMenu.style.right = Math.max(12, window.innerWidth - r.right) + 'px';
        acctMenu.classList.add('show');
    }
    function hideAcct() { if (acctMenu) acctMenu.classList.remove('show'); }
    async function signOut() {
        hideAcct();
        try { const c = await supa(); await c.auth.signOut(); } catch (e) {}
        currentUser = null;
        document.querySelectorAll('.wallet-btn, #walletBtn').forEach(b => {
            b.classList.remove('connected');
            const t = b.querySelector('#walletText') || b.querySelector('[id$="walletText"]');
            if (t) t.textContent = 'Sign In';
        });
        toast('Signed out');
    }
    window.tvSignOut = signOut;

    async function restoreSession() {
        try {
            const c = await supa();
            const { data } = await c.auth.getSession();
            if (data.session) onAuthed(data.session.user);
            c.auth.onAuthStateChange((_e, s) => { if (s) onAuthed(s.user); });
        } catch (e) {}
    }

    function boot() { build(); restoreSession(); }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && overlay && overlay.classList.contains('show')) close(); });
})();
