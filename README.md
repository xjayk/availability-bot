# availability-bot

Scheduled GitHub Action that logs into a company Drupal portal each weekday morning and sets your availability status for the next day, then sends a confirmation via Telegram.

## How It Works

```
GitHub Actions (scheduled daily)
  └─→ Playwright logs into company Drupal site
        └─→ Navigates to /change-availability-for-tomorrow/{status}
              └─→ Verifies success message in page
                    └─→ Sends confirmation to Telegram
```

The workflow runs Mon-Fri at 11:00 UTC (7:00 AM ET). It can also be triggered manually from the Actions tab.

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

### 2. Set GitHub Secrets

Navigate to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Description |
|--------|-------------|
| `BASE_URL` | Full base URL of the company site, e.g. `https://www.example.com` |
| `USERNAME` | Your login email or username |
| `PASSWORD` | Your password |
| `STATUS_CHOICE` | `available` or `unavailable` |
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID from `getUpdates` |

**Optional:**

| Secret | Default | Description |
|--------|---------|-------------|
| `PAGE_TIMEOUT` | `30000` | Page load / selector wait timeout in milliseconds |
| `MAX_RETRIES` | `3` | Number of retry attempts on failure |
| `RETRY_DELAY` | `10` | Seconds to wait between retries |

### 3. Test

Go to the **Actions** tab → **Set Daily Availability** → **Run workflow**. Check the run logs. If it fails, screenshots are uploaded as artifacts to help debug.

### 4. Adjust the Schedule

Edit the cron expression in `.github/workflows/availability.yml` under `schedule`. The current value `0 11 * * 1-5` = Mon-Fri at 11:00 UTC.

| Timezone | UTC Offset | Cron for ~7 AM |
|----------|------------|----------------|
| Eastern (ET) | UTC-5 / UTC-4 | `0 11 * * 1-5` (7 AM / 6 AM) |
| Pacific (PT) | UTC-8 / UTC-7 | `0 14 * * 1-5` (6 AM / 7 AM) |
| Central Europe (CET) | UTC+1 / UTC+2 | `0 5 * * 1-5` (6 AM / 7 AM) |

## Project Structure

```
.github/workflows/availability.yml   — GitHub Actions workflow
set_availability.py                   — Playwright automation script
requirements.txt                      — Python dependencies
```

## How the Status Toggle Works

The script uses a URL-based toggle discovered by inspecting the company Drupal site:

- `/change-availability-for-tomorrow/available` → marks you **available** for tomorrow
- `/change-availability-for-tomorrow/unavailable` → marks you **unavailable** for tomorrow

No form submission or modal interaction is needed — just navigating to the URL (while authenticated) changes the status. The script verifies by checking for the success message (`"You're made available for tomorrow"`) or the updated header CSS class.
