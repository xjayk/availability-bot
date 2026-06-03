# Handoff: availability-bot

## Current State

Everything is implemented and pushed to `main` at `https://github.com/xjayk/availability-bot`. Two commits:

1. `58214fb` — `set_availability.py`, `.github/workflows/availability.yml`, `.gitignore`
2. `e1eff74` — `README.md`, `TODO.md`

`PLAN.md` at root is the original spec — keep it for reference.

## What Exists

| File | Purpose |
|------|---------|
| `set_availability.py` | Playwright script: login, set status, screenshot, output result |
| `.github/workflows/availability.yml` | Scheduled workflow (Mon-Fri 13:00 UTC), Telegram notifications, artifact uploads |
| `.gitignore` | Python + artifacts |
| `README.md` | Full setup guide |
| `TODO.md` | Setup checklist + future ideas |
| `PLAN.md` | Original spec (read-only reference) |

## Architecture

```
GitHub Actions (scheduled) → Playwright (Chromium headless) → company site → Telegram notification
```

- All configuration via GitHub Secrets — no hardcoded credentials.
- Generic CSS selectors as defaults; any site-specific selectors can be overridden via secrets without code changes.
- Screenshots captured on success and failure, uploaded as Actions artifacts (3-day retention).
- Telegram notifications via `appleboy/telegram-action`.

## What's Blocked / Manual

The following requires human action (details in `README.md`):

1. **Create Telegram bot** via @BotFather → save token + chat ID.
2. **Inspect company site** to determine correct CSS selectors for login and status page.
3. **Set GitHub Secrets** — 7 required, 5 optional (see README).
4. **Test** via manual workflow trigger in Actions tab.
5. **Adjust cron** in `availability.yml` for the right timezone.

## Design Decisions

- **Python + Playwright** over Puppeteer/Playwright JS — plan specified Python, simpler for devs who may not know JS.
- **Selector overrides via secrets** — allows one-codebase-many-sites without branching.
- **`wait_for_url("**/dashboard**")` after login** — assumes a `/dashboard` post-login redirect. May need adjustment for different apps.
- **`networkidle` wait strategy** — waits for network to settle before interacting. Robust for SPAs.
- **Screenshots always** — on both success and failure — because you can't see what Playwright sees in CI.

## Potential Next Steps

1. **Debug failed runs** — use uploaded screenshot artifacts to identify wrong selectors.
2. **MFA support** — if the site adds 2FA, the script will need a `page.wait_for_selector` for an MFA code input and a way to supply codes (TOTP secret in secrets, or email-based).
3. **Multi-status scheduling** — e.g. "In Office" Mon/Wed/Fri, "Remote" Tue/Thu.
4. **Dry-run mode** — `page.wait_for_timeout(5000)` + screenshot instead of clicking save, for testing selectors without committing a status change.

## Repo Details

- Remote: `origin` → `https://github.com/xjayk/availability-bot.git`
- Branch: `main` (single branch, no PRs)
- No CI has run yet — first run requires secrets to be set.
