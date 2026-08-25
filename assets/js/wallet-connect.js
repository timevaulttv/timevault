// ============================================
// TIME VAULT — Universal EVM Wallet Connector
// EIP-6963 multi-wallet discovery (MetaMask, Rabby,
// OKX, Bitget, Coinbase, Trust, Brave, Phantom, …)
// with legacy window.ethereum fallback.
// API: window.tvConnectWallet() -> Promise<{address, provider, walletName}>
// ============================================
(function () {
    const discovered = [];
    window.addEventListener('eip6963:announceProvider', e => {
        try {
            const d = e.detail;
            if (d && d.info && d.provider && !discovered.some(p => p.info.uuid === d.info.uuid)) discovered.push(d);
        } catch (err) {}
    });
    window.dispatchEvent(new Event('eip6963:requestProvider'));

    const CSS = `
        .wc-overlay { position: fixed; inset: 0; z-index: 480; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; padding: 1.5rem; opacity: 0; transition: opacity 0.25s; }
        .wc-overlay.show { opacity: 1; }
        .wc-modal { width: min(400px, 100%); border-radius: 20px; padding: 1px; background: linear-gradient(165deg, rgba(212,175,55,0.6), rgba(212,175,55,0.12) 28%, rgba(139,92,246,0.4) 58%, rgba(192,38,211,0.25) 78%, rgba(212,175,55,0.5)); }
        .wc-inner { background: linear-gradient(180deg, #140B20, #0A0512 70%); border-radius: 19px; padding: 1.75rem; }
        .wc-title { font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 600; color: #FAFAFA; letter-spacing: 0.04em; margin-bottom: 0.35rem; }
        .wc-sub { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: #D4AF37; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 0.6rem; }
        .wc-sub::before { content: ''; width: 26px; height: 1px; background: linear-gradient(90deg, #D4AF37, transparent); }
        .wc-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 300px; overflow-y: auto; scrollbar-width: thin; }
        .wc-item { display: flex; align-items: center; gap: 0.9rem; padding: 0.8rem 1rem; border-radius: 12px; background: #140C1F; border: 1px solid rgba(255,255,255,0.06); cursor: pointer; transition: all 0.3s; font-family: 'Inter', sans-serif; width: 100%; text-align: left; }
        .wc-item:hover { border-color: rgba(212,175,55,0.45); box-shadow: inset 2px 0 0 #D4AF37; background: rgba(139,92,246,0.07); }
        .wc-item img, .wc-item .wc-fallback-icon { width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0; }
        .wc-fallback-icon { background: linear-gradient(135deg, #6D28D9, #C026D3); display: flex; align-items: center; justify-content: center; color: #fff; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; }
        .wc-item .wc-name { color: #FAFAFA; font-size: 0.9rem; font-weight: 500; flex: 1; }
        .wc-item .wc-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; color: #34D399; letter-spacing: 0.08em; }
        .wc-cancel { margin-top: 1rem; width: 100%; padding: 0.65rem; border-radius: 100px; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: #8C7CA6; font-family: 'Inter', sans-serif; font-size: 0.8rem; cursor: pointer; transition: all 0.3s; }
        .wc-cancel:hover { border-color: rgba(212,175,55,0.4); color: #FAFAFA; }
        .wc-empty { text-align: center; padding: 1rem 0.5rem; color: #8C7CA6; font-size: 0.85rem; line-height: 1.7; }
        .wc-empty a { color: #D4AF37; text-decoration: none; }
        .wc-empty a:hover { text-decoration: underline; }
    `;
    let cssInjected = false;
    function injectCSS() {
        if (cssInjected) return;
        const s = document.createElement('style');
        s.textContent = CSS;
        document.head.appendChild(s);
        cssInjected = true;
    }

    function getWallets() {
        if (discovered.length) return discovered.slice();
        if (window.ethereum) {
            const eth = window.ethereum;
            const name = eth.isMetaMask ? 'MetaMask' : eth.isCoinbaseWallet ? 'Coinbase Wallet' : eth.isRabby ? 'Rabby' : eth.isTrust ? 'Trust Wallet' : 'Injected Wallet';
            return [{ info: { uuid: 'legacy', name, icon: null }, provider: eth }];
        }
        return [];
    }

    function showPicker(wallets) {
        return new Promise((resolve, reject) => {
            injectCSS();
            const ov = document.createElement('div');
            ov.className = 'wc-overlay';
            const rows = wallets.map((w, i) => `
                <button class="wc-item" data-i="${i}">
                    ${w.info.icon ? `<img src="${w.info.icon}" alt="">` : `<span class="wc-fallback-icon">${(w.info.name || 'W')[0]}</span>`}
                    <span class="wc-name">${w.info.name}</span>
                    <span class="wc-tag">DETECTED ✓</span>
                </button>`).join('');
            ov.innerHTML = `
                <div class="wc-modal"><div class="wc-inner">
                    <div class="wc-title">Connect Wallet</div>
                    <div class="wc-sub">${wallets.length} EVM wallet${wallets.length > 1 ? 's' : ''} detected</div>
                    <div class="wc-list">${rows}</div>
                    <button class="wc-cancel">Cancel</button>
                </div></div>`;
            document.body.appendChild(ov);
            requestAnimationFrame(() => ov.classList.add('show'));
            const close = result => {
                ov.classList.remove('show');
                setTimeout(() => ov.remove(), 250);
                document.removeEventListener('keydown', onKey);
                result instanceof Error ? reject(result) : resolve(result);
            };
            const onKey = e => { if (e.key === 'Escape') close(new Error('CANCELLED')); };
            document.addEventListener('keydown', onKey);
            ov.addEventListener('click', e => {
                if (e.target === ov) { close(new Error('CANCELLED')); return; }
                const btn = e.target.closest('.wc-item');
                if (btn) close(wallets[+btn.dataset.i]);
            });
            ov.querySelector('.wc-cancel').addEventListener('click', () => close(new Error('CANCELLED')));
        });
    }

    function showNoWallet() {
        injectCSS();
        const ov = document.createElement('div');
        ov.className = 'wc-overlay';
        ov.innerHTML = `
            <div class="wc-modal"><div class="wc-inner">
                <div class="wc-title">No Wallet Found</div>
                <div class="wc-sub">EVM wallet required</div>
                <div class="wc-empty">Install any EVM wallet extension to continue —<br>
                    <a href="https://metamask.io" target="_blank" rel="noopener">MetaMask</a> ·
                    <a href="https://rabby.io" target="_blank" rel="noopener">Rabby</a> ·
                    <a href="https://www.okx.com/web3" target="_blank" rel="noopener">OKX</a> ·
                    <a href="https://www.coinbase.com/wallet" target="_blank" rel="noopener">Coinbase</a><br>
                    then refresh this page.</div>
                <button class="wc-cancel">Close</button>
            </div></div>`;
        document.body.appendChild(ov);
        requestAnimationFrame(() => ov.classList.add('show'));
        const close = () => { ov.classList.remove('show'); setTimeout(() => ov.remove(), 250); };
        ov.addEventListener('click', e => { if (e.target === ov) close(); });
        ov.querySelector('.wc-cancel').addEventListener('click', close);
    }

    window.tvActiveProvider = null;
    window.tvConnectWallet = async function () {
        window.dispatchEvent(new Event('eip6963:requestProvider'));
        await new Promise(r => setTimeout(r, 80));
        const wallets = getWallets();
        if (!wallets.length) { showNoWallet(); throw new Error('NO_WALLET'); }
        const chosen = wallets.length === 1 ? wallets[0] : await showPicker(wallets);
        const accounts = await chosen.provider.request({ method: 'eth_requestAccounts' });
        if (!accounts || !accounts.length) throw new Error('NO_ACCOUNTS');
        window.tvActiveProvider = chosen.provider;
        return { address: accounts[0], provider: chosen.provider, walletName: chosen.info.name };
    };
    window.tvOnAccountsChanged = function (cb) {
        const p = window.tvActiveProvider;
        if (p && typeof p.on === 'function') p.on('accountsChanged', cb);
    };
})();
