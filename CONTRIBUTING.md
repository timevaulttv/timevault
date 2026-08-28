# Contributing to Time Vault

Thanks for your interest in Time Vault! This document keeps contributions smooth and consistent.

## Getting started

```bash
git clone <this-repo>
cd timevault
npx http-server . -p 8080
# open http://localhost:8080
```

No build step, no framework. The whole site is **vanilla HTML/CSS/JS**. Three.js and Google Fonts load from CDN.

## The one rule that matters

**No invented numbers.** Every figure shown to a visitor must be readable from
the chain or plainly labelled as a demonstration. A market cap, a holder count,
a total value locked, a provider count, a delivery count, an agent's accuracy
score: if it cannot be checked, it does not ship.

This is not a style preference. Earlier versions of this site carried a $12.4M
TVL, a simulated activity feed, invented agent performance badges, and a token
allocation that never existed. All of it was removed. `proof.html` now states
what is not built, on purpose, and a PR that quietly makes the project look more
finished than it is will be closed.

If you need a placeholder while building, label it, or read it from
`assets/js/tv-live.js`, which is already wired to the chain.

## Project conventions

- **Design system first.** Colors, typography, and effects are defined as CSS variables in each page's `:root`. Use them, and never introduce new accent colors. Gold (`--gold`) is trim, not paint.
- **Shared modules** live in `assets/js/` (`vault-notes.js`, `wallet-connect.js`, `agent-menu.js`, `tv-auth.js`, `tv-live.js`). If a feature must exist on more than one page, it belongs there, self-contained (inject your own CSS/markup).
- **Assets:** put web-optimized files in `assets/`; original masters stay in `source/brand/` and `source/agents/` and are never referenced by pages.
- **Videos** must be H.264, compressed (target < 1.5 MB), `muted playsinline`, `pointer-events: none`, `disablepictureinpicture`, and edge-feathered with a CSS mask when placed on the dark background.
- **Motion:** every animation must respect `prefers-reduced-motion: reduce`.

## Pull requests

1. One focused change per PR.
2. Test all five pages (`index.html`, `app.html`, `whitepaper.html`, `proof.html`,
   `404.html`) at desktop and 375 px mobile width, with no horizontal overflow and
   no console errors.
3. If the change touches deployment or the backend, run `bash deploy/smoke.sh`
   against a live host and paste the output.
4. Describe what changed and why; screenshots or clips for visual changes.

## Reporting bugs

Open an issue using the bug template. Include the page, browser, and console output.
