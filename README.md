# availability-bot

Scheduled GitHub Action that logs into a company portal each weekday morning and sets your availability status, then sends a confirmation via Telegram.

## How It Works

```
GitHub Actions (scheduled daily)
  └─→ Playwright script logs into your company site
        └─→ Sets availability status
            └─→ Sends confirmation to your Telegram
```

The workflow runs Mon-Fri at 13:00 UTC (adjustable). It can also be triggered manually from the Actions tab.

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram and send `/newbot`.
2. Choose a name (e.g. `Availability Bot`) and username (e.g. `YourNameAvailBot`).
3. Save the bot token BotFather gives you.
4. Start a chat with your new bot, then visit:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
5. Look for `"chat":{"id":123456789}` — that number is your Chat ID.

### 2. Find Your Site's Selectors

Inspect your company's login and status pages (right-click → Inspect). Note the CSS selectors for:

- Username input
- Password input
- Submit button
- Availability status button (the one you click to set your status)
- Save/confirm button

### 3. Set GitHub Secrets

Navigate to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Description |
|--------|-------------|
| `LOGIN_URL` | Full URL of the company login page |
| `USERNAME` | Your login email or username |
| `PASSWORD` | Your password |
| `STATUS_URL` | Full URL of the availability/status page |
| `STATUS_CHOICE` | The status label text, e.g. `Available` |
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID from `getUpdates` |

**Optional** (only if the default selectors don't match your site):

| Secret | Default Value | Example Override |
|--------|---------------|------------------|
| `USERNAME_SELECTOR` | `input[name="username"]` | `input#email` |
| `PASSWORD_SELECTOR` | `input[name="password"]` | `input#pass` |
| `SUBMIT_SELECTOR` | `button[type="submit"]` | `button#login-btn` |
| `STATUS_BUTTON_SELECTOR` | `text="Available"` | `text="In Office"` |
| `SAVE_BUTTON_SELECTOR` | `button:has-text("Save")` | `button:has-text("Update")` |

### 4. Test

Go to the **Actions** tab → **Set Daily Availability** → **Run workflow**. Check the run logs. If it fails, screenshots are uploaded as artifacts to help debug.

### 5. Adjust the Schedule

Edit the cron expression in `.github/workflows/availability.yml` under `schedule`. The current value `0 13 * * 1-5` = Mon-Fri at 13:00 UTC.

| Timezone | UTC Offset | Cron for ~9 AM |
|----------|------------|----------------|
| Eastern (ET) | UTC-5 / UTC-4 | `0 13 * * 1-5` (9 AM / 8 AM) |
| Pacific (PT) | UTC-8 / UTC-7 | `0 16 * * 1-5` (8 AM / 9 AM) |
| Central Europe (CET) | UTC+1 / UTC+2 | `0 7 * * 1-5` (8 AM / 9 AM) |

## Project Structure

```
.github/workflows/availability.yml   — GitHub Actions workflow
set_availability.py                   — Playwright automation script
.gitignore
```

## Custom Selectors

The script uses sensible defaults for common login forms, but every company site is different. Set any of the optional secrets above to override selectors without modifying the code.
