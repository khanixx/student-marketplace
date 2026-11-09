# Student Marketplace — prototype

Main process: register -> log in -> post listing -> search -> message seller -> mark as sold.

## Run
    pip install flask pytest
    python app.py
Open http://127.0.0.1:5000 . The database `marketplace.db` is created on first start from
`schema.sql` + `seed.sql`. Delete the file to reset the data.

Test accounts: aruzhan@kbtu.kz, dias@kbtu.kz, madina@kbtu.kz ... password `password123`.

## Tests
    python -m pytest -v      # 22 test cases, TC-01 ... TC-22

## Files
- app.py — routes (Flask), one function per user story (US-1 ... US-7)
- schema.sql — tables (users, categories, listings, messages, favourites), keys, constraints;  seed.sql — test data
- templates/ — HTML pages (_ui.html = inline SVG icons, listing card, category sections)
- test_app.py — automated tests

## Favourites (US-8)
Heart button on every card and listing page; `/favourites` shows saved items grouped by category. Heart toggles add/remove (table `favourites`).

## Security
- CSRF: every POST form carries a per-session token (`csrf_field()`), checked in `check_csrf()`; session cookie is `HttpOnly` + `SameSite=Lax`.
- Logout is POST-only; `?next=` redirects are local-only (`safe_next`).
- Seller can reply only to buyers who wrote about that listing.
- Headers: `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `nosniff`.
- Set `SECRET_KEY` in production; debug mode only with `FLASK_DEBUG=1`.
