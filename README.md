# Twostones Studio Books

Bookkeeping + garment costing + pricing calculator for Twostones (KES).
Migrated from the Claude artifact **unchanged** except for the CSV export (see MIGRATION below).

## Run locally
No build step, no npm dependencies. Serve the folder with any static server:

    python3 -m http.server 8080      # then open http://localhost:8080
    # or: npx serve .

(Opening index.html directly also works, but a server is closer to production.)

## Folder structure
    twostones-books/
    ├── index.html        # page shell: fonts, stylesheet, mount points (#app, #modal, #toast)
    ├── css/
    │   └── styles.css    # all styling, light/dark theme tokens (CSS variables)
    ├── js/
    │   └── app.js        # ALL logic: state, calculations, views, forms, export
    └── README.md

## Technology (as built)
- Plain HTML + CSS + JavaScript (ES2020). No framework, no TypeScript, no bundler, no npm packages.
- UI is rendered by JS template strings into `#app`; `R()` re-renders. Buttons use inline `onclick`, so `app.js` must stay a **classic script** (not `type="module"`) until handlers are refactored.
- Fonts: Google Fonts (Cormorant Garamond, Inter), loaded by a `<link>`.
- CSS: variables for theming, `prefers-color-scheme` dark mode, `color-mix()`, CSS grid/flex, iOS safe-area insets.
- Data: one JS object `S` (settings, clients, orders, payments, materials, usage, expenses, products) persisted as JSON in `localStorage` under key `twostones.v1`.

## Where the logic lives in `js/app.js`
| Concern | Function(s) |
|---|---|
| Pricing engine (margin/markup) | `price(cost, pct, mode)`, `rp()` rounding to nearest 50, calculator `cin()` |
| Order cost, estimated vs actual, payments | `ocalc(order)`, `pstat()` |
| Monthly sales/expenses/cash | `mstat(month)`, `flow(month)` |
| Persistence | `load()`, `save()`, `seed()` |
| CRUD | `form()`, `edit()`, `del()`, `useMat()` |
| Screens | `views.dash/orders/order/clients/client/mat/exp/calc/cat/rep/set` |
| CSV export | `exp_()` |

## MIGRATION: what changed vs the artifact
1. **CSV export (`exp_` in app.js)** — the artifact used Claude's `downloads` capability (`claude.use('downloads')` / `save()`). Replaced with a standard Blob + `<a download>`. This is the ONLY code change.
2. **Publishing wrapper** — the artifact was one HTML file; it is now split into `index.html`, `css/styles.css`, `js/app.js` (content identical).
3. **Favicon** — the artifact set it at publish time; now an inline emoji `<link rel="icon">`.

## Not used by the app (nothing to remove)
No `window.storage`, no Claude API calls (`api.anthropic.com`), no `window.claude.complete`, no `window.fs`, no React, no CDN scripts. `localStorage` is a normal browser API and works as-is.

## Things that will need replacing LATER (not done now, by request)
- `localStorage` persistence → a real database (replace `load()`/`save()`; all reads/writes go through `S`).
- No authentication (the artifact was private to the owner by link). Needs login before any public hosting.
- Data is per-browser/device; no sync.
- Inline `onclick` handlers and global functions → modules/components if you adopt a framework.

## Migration checklist
- [ ] Create the folder exactly as above and open in Antigravity
- [ ] Run a local static server and open the app
- [ ] Confirm sample data loads (Jane Doe, TS-001, est. cost KES 10,075)
- [ ] Price it: 4 yds × 1,500 + 500 trims + 5 h → cost 10,075; 30% margin → ~14,393 (14,400 rounded)
- [ ] Check 10,000 cost: 30% margin = 14,285.71, 30% markup = 13,000
- [ ] Add a payment; balance and payment status update
- [ ] Assign material to an order; remaining quantity drops
- [ ] Enter actual costs on an order; estimated vs actual difference shows
- [ ] Add an expense; Reports for the month update
- [ ] Settings → Export CSV downloads a file
- [ ] Reload the page; data persists (localStorage)
- [ ] Settings → delete sample data when ready to use real data
- [ ] Back up: export CSVs before changing storage later
- [ ] Commit to Git (baseline), then start adding features/database
