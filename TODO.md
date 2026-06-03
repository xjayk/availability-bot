# Setup Checklist

- [ ] Create Telegram bot via @BotFather and save token
- [ ] Retrieve Telegram chat ID from `getUpdates` endpoint
- [ ] Set all required GitHub Secrets (Settings → Secrets and variables → Actions)
- [ ] Run workflow manually from Actions tab to verify
- [ ] Verify Telegram notifications fire on success and failure

# Future Ideas

- [ ] **Multi-day scheduling** — different status per weekday (e.g. "available" Mon/Wed/Fri only)
- [ ] **Calendar-aware skip** — read a GCal/iCal feed and skip PTO / holidays automatically
- [ ] **Dry-run mode** — navigate and screenshot without actually toggling status, for safe testing
- [ ] **Multi-site support** — set status on multiple portals in a single run
- [ ] **Structured JSON logging** — parseable logs for debugging and metrics
- [ ] **TOTP / MFA support** — generate 2FA codes from a stored secret when the site enforces MFA
- [ ] **Webhook fallback** — send notifications to Slack / Discord alongside Telegram
- [ ] **Availability dashboard** — GitHub Pages site showing a history of status changes
