# Setup Checklist

- [ ] Create Telegram bot via @BotFather and save token
- [ ] Retrieve Telegram chat ID from `getUpdates` endpoint
- [ ] Inspect company login page and identify CSS selectors
- [ ] Inspect company status/availability page and identify CSS selectors
- [ ] Set all required GitHub Secrets (Settings → Secrets and variables → Actions)
- [ ] Run workflow manually from Actions tab to verify
- [ ] Adjust cron schedule in `availability.yml` for your timezone
- [ ] Verify Telegram notifications fire on success and failure

# Future Ideas

- [ ] Add support for different statuses on different days (e.g. "In Office" vs "Remote")
- [ ] Handle multi-factor authentication if the site adds it later
- [ ] Send a daily summary instead of per-status messages
- [ ] Add a webhook fallback alongside Telegram
