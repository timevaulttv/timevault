// ============================================
// TIME VAULT: live on-chain figures
//
// Replaces hand-written numbers with what the chain actually says. Every value
// here comes from the letscash.fun public API for the $TV contract, so a
// visitor can check any of it against the token page in seconds.
//
// Usage: put data-tv-live="<field>" on any element. Fields:
//   mcap price holders vol24 supply tax top10 burned launched
// A data-tv-live-fallback attribute holds what to show if the API is down.
//
// The API sends access-control-allow-origin:*, so this runs straight from the
// browser with no proxy.
// ============================================
(() => {
    'use strict';

    const CA   = '0xEAe2a144A3C7CFd4Ea50b9F5513124048Fed8bcc';
    const BASE = 'https://api.letscash.fun/api';
    const TOKEN_PAGE = 'https://www.letscash.fun/token/' + CA;
    const REFRESH_MS = 60000;

    const nodes = document.querySelectorAll('[data-tv-live]');
    if (!nodes.length) return;

    // ---- formatting -------------------------------------------------------
    const usd = n => {
        if (!isFinite(n)) return null;
        if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B';
        if (n >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M';
        if (n >= 1e3) return '$' + (n / 1e3).toFixed(1) + 'K';
        return '$' + n.toFixed(2);
    };
    // Sub-cent prices need significant digits, not fixed decimals.
    const usdPrice = n => {
        if (!isFinite(n) || n <= 0) return null;
        if (n >= 0.01) return '$' + n.toFixed(4);
        const exp = Math.floor(Math.log10(n));
        return '$' + n.toFixed(Math.min(18, -exp + 3));
    };
    const count = n => isFinite(n) ? n.toLocaleString('en-US') : null;
    const compact = n => {
        if (!isFinite(n)) return null;
        if (n >= 1e9) return (n / 1e9).toFixed(n >= 1e10 ? 0 : 1) + 'B';
        if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + 'M';
        if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K';
        return String(n);
    };
    const ago = ms => {
        const d = Math.floor((Date.now() - ms) / 86400000);
        if (d >= 1) return d + (d === 1 ? ' day' : ' days');
        const h = Math.floor((Date.now() - ms) / 3600000);
        if (h >= 1) return h + (h === 1 ? ' hour' : ' hours');
        return Math.max(1, Math.floor((Date.now() - ms) / 60000)) + ' min';
    };

    // ---- fetch ------------------------------------------------------------
    const get = async path => {
        const r = await fetch(BASE + path, { cache: 'no-store' });
        if (!r.ok) throw new Error(path + ' -> ' + r.status);
        return r.json();
    };

    async function load() {
        const [cfg, tok, hold] = await Promise.all([
            get('/config'),
            get('/tokens/' + CA + '?surface=current'),
            get('/tokens/' + CA + '/holders?surface=current').catch(() => null),
        ]);

        const ethUsd = Number(cfg && cfg.ethUsd) || 0;
        const v = {
            mcap:     usd(Number(tok.marketCapEth) * ethUsd),
            price:    usdPrice(Number(tok.priceEth) * ethUsd),
            holders:  count(Number(hold && hold.count != null ? hold.count : tok.holders)),
            vol24:    usd(Number(tok.volumeEth && tok.volumeEth.day) * ethUsd),
            supply:   compact(Number(tok.circulatingSupply)),
            tax:      isFinite(Number(tok.taxPct)) ? Number(tok.taxPct) + '%' : null,
            top10:    hold && isFinite(Number(hold.top10Pct))
                        ? Number(hold.top10Pct).toFixed(1) + '%' : null,
            burned:   isFinite(Number(tok.burnedPct)) ? Number(tok.burnedPct) + '%' : null,
            launched: tok.launchedAt ? ago(Number(tok.launchedAt)) + ' ago' : null,
        };

        nodes.forEach(el => {
            const val = v[el.getAttribute('data-tv-live')];
            if (val == null) return;
            el.textContent = val;
            el.classList.add('tv-live-on');
            if (!el.title) el.title = 'Live from the chain. Verify on the token page.';
        });

        document.querySelectorAll('[data-tv-live-stamp]').forEach(el => {
            el.textContent = 'Updated ' + new Date().toLocaleTimeString('en-GB',
                { hour: '2-digit', minute: '2-digit' });
        });
        return ethUsd;
    }

    // If the API is unreachable the page keeps whatever the markup already
    // says. A stale number is worse than an honest placeholder, so the
    // fallback text is deliberately non-numeric.
    function degrade() {
        nodes.forEach(el => {
            const fb = el.getAttribute('data-tv-live-fallback');
            if (fb) el.textContent = fb;
        });
        document.querySelectorAll('[data-tv-live-stamp]').forEach(el => {
            el.textContent = 'Live figures unavailable, check the token page';
        });
    }

    // ---- real trades ticker ----------------------------------------------
    // Replaces the old simulated feed. Every line here is a transaction that
    // happened, and the hash links to the block explorer so it can be checked.
    const EXPLORER = 'https://robinhoodchain.blockscout.com';
    const viewport = document.querySelector('[data-tv-live-trades]');
    let lastTradeId = null, tradeTimer = null;

    const short = a => a ? a.slice(0, 6) + '…' + a.slice(-4) : '';
    const since = ms => {
        const s = Math.max(1, Math.floor((Date.now() - ms) / 1000));
        if (s < 60) return s + 's';
        if (s < 3600) return Math.floor(s / 60) + 'm';
        return Math.floor(s / 3600) + 'h';
    };

    async function loadTrades(ethUsd) {
        if (!viewport) return;
        const d = await get('/tokens/' + CA + '/trades?surface=current');
        const rows = (d && d.trades) || [];
        if (!rows.length) return;

        // Only re-render when something new actually landed.
        if (rows[0].id === lastTradeId) return;
        lastTradeId = rows[0].id;

        viewport.innerHTML = rows.slice(0, 12).map(t => {
            const buy = String(t.side).toLowerCase() === 'buy';
            const eth = Number(t.ethWei) / 1e18;
            const val = ethUsd ? '$' + (eth * ethUsd).toFixed(2) : eth.toFixed(4) + ' ETH';
            const tv  = Number(t.tokenWei) / 1e18;
            const amt = tv >= 1e6 ? (tv / 1e6).toFixed(2) + 'M' : Math.round(tv).toLocaleString('en-US');
            return '<a class="lt-item" href="' + EXPLORER + '/tx/' + t.txHash + '"'
                 + ' target="_blank" rel="noopener" title="View this transaction on the explorer">'
                 + '<span class="lt-side ' + (buy ? 'buy' : 'sell') + '">'
                 + (buy ? 'BUY' : 'SELL') + '</span> '
                 + val + ' &middot; ' + amt + ' $TV &middot; '
                 + short(t.trader) + ' &middot; ' + since(Number(t.t)) + ' ago</a>';
        }).join('');
        viewport.classList.add('tv-live-on');
    }

    // ---- price chart ------------------------------------------------------
    // Drawn straight into SVG from the candle endpoint. No chart library: this
    // is one path and two labels, and pulling in a dependency for that would
    // cost more than the feature.
    const chart = document.querySelector('[data-tv-live-chart]');

    async function loadChart(ethUsd) {
        if (!chart) return;
        const d = await get('/tokens/' + CA + '/chart?window=86400&step=300&surface=current');
        const rows = (d && d.candles) || [];
        if (rows.length < 2) return;

        const closes = rows.map(c => Number(c.close)).filter(isFinite);
        if (closes.length < 2) return;

        const W = 1000, H = 200, PAD = 6;
        const lo = Math.min(...closes), hi = Math.max(...closes);
        const span = (hi - lo) || hi || 1;
        const x = i => (i / (closes.length - 1)) * W;
        const y = v => PAD + (1 - (v - lo) / span) * (H - PAD * 2);

        const line = closes.map((v, i) => (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1)).join(' ');
        const area = line + ' L' + W + ' ' + H + ' L0 ' + H + ' Z';
        const up = closes[closes.length - 1] >= closes[0];
        const stroke = up ? '#34D399' : '#F87171';
        const change = closes[0] > 0 ? ((closes[closes.length - 1] / closes[0] - 1) * 100) : 0;

        chart.innerHTML =
            '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" aria-hidden="true">'
          + '<defs><linearGradient id="tvChartFill" x1="0" y1="0" x2="0" y2="1">'
          + '<stop offset="0%" stop-color="' + stroke + '" stop-opacity="0.28"/>'
          + '<stop offset="100%" stop-color="' + stroke + '" stop-opacity="0"/>'
          + '</linearGradient></defs>'
          + '<path d="' + area + '" fill="url(#tvChartFill)"/>'
          + '<path d="' + line + '" fill="none" stroke="' + stroke + '" stroke-width="2.5"'
          + ' vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg>';

        const meta = document.querySelector('[data-tv-live-chart-meta]');
        if (meta) {
            meta.textContent = (change >= 0 ? '+' : '') + change.toFixed(1) + '% over 24h';
            meta.style.color = stroke;
        }
        const lowEl  = document.querySelector('[data-tv-live-chart-low]');
        const highEl = document.querySelector('[data-tv-live-chart-high]');
        if (lowEl && ethUsd)  lowEl.textContent  = usdPrice(lo * ethUsd) || '';
        if (highEl && ethUsd) highEl.textContent = usdPrice(hi * ethUsd) || '';
    }

    let failures = 0;
    const tick = () => load()
        .then(ethUsd => { failures = 0; return Promise.all([loadTrades(ethUsd), loadChart(ethUsd)]); })
        .catch(() => { if (++failures === 1) degrade(); });

    tick();
    let timer = setInterval(tick, REFRESH_MS);
    // Stop polling a tab nobody is looking at.
    document.addEventListener('visibilitychange', () => {
        clearInterval(timer);
        if (!document.hidden) { tick(); timer = setInterval(tick, REFRESH_MS); }
    });

    window.__tvLive = { load, CA, TOKEN_PAGE };
})();
