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

1. In Telegram, message **@BotFather** and send `/newbot`.
2. Give it a name (e.g. `Availability Bot`) and a username (e.g. `YourNameAvailabilityBot`).
3. BotFather will give you a **token** — save it. It looks like `123456:ABC-DEF1234ghikl...`
4. Start a chat with your new bot (search its username, tap Start).
5. To get your **Chat ID**, message your bot anything, then visit:
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
| `STATUS_CHOICE` | `available` or `unavailable` (case-insensitive) |
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

## Local Testing

You can test the script on your machine before pushing to GitHub.

### Prerequisites

- Python 3.12+
- A Telegram bot and chat ID (same as CI setup)

### Setup

```bash
# Clone and enter the repo
git clone https://github.com/xjayk/availability-bot.git
cd availability-bot

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium --with-deps
```

### Run

```bash
# Set required environment variables
export BASE_URL="https://www.example.com"
export USERNAME="your-email@company.com"
export PASSWORD="your-password"
export STATUS_CHOICE="available"       # or "unavailable"

# Optional overrides
export PAGE_TIMEOUT="30000"            # milliseconds
export MAX_RETRIES="1"                 # 1 = no retry (faster for testing)
export RETRY_DELAY="5"                 # seconds between retries

# Run the script
python set_availability.py
```

### Check Results

After running, two screenshots are saved in the current directory:

| File | Contents |
|------|----------|
| `final-status.png` | The profile page after toggling availability |
| `error-screenshot.png` | Only created if something failed |

If you also want Telegram notifications locally, set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` and run the full workflow with [act](https://github.com/nektos/act):

```bash
act workflow_dispatch -s BASE_URL="$BASE_URL" -s USERNAME="$USERNAME" ...
```

### Testing the Toggle Without Changing Status

To verify the script works without actually changing your availability, set `STATUS_CHOICE` to your *current* status. The toggle is idempotent — setting "available" when you're already available is a no-op but still returns the same success message.

## How the Status Toggle Works

The script uses a URL-based toggle discovered by inspecting the company Drupal site:

- `/change-availability-for-tomorrow/available` → marks you **available** for tomorrow
- `/change-availability-for-tomorrow/unavailable` → marks you **unavailable** for tomorrow

No form submission or modal interaction is needed — just navigating to the URL (while authenticated) changes the status. The script verifies by checking for the success message (`"You're made available for tomorrow"`) or the updated header CSS class.

## Project Structure

```
.github/workflows/availability.yml   — Scheduled availability setter
.github/workflows/ci.yml              — Linting and type checking on push/PR
set_availability.py                   — Playwright automation script
requirements.txt                      — Python dependencies
pyproject.toml                        — Ruff + mypy configuration
```

## CI

On every push and pull request to `main`, the CI workflow runs:

| Job | Tool | What It Checks |
|-----|------|----------------|
| Lint Python | Ruff | Syntax errors, unused imports, code style violations |
| Format Python | Ruff | Consistent formatting (double quotes, spacing) |
| Type Check | Mypy | Type errors in `set_availability.py` |
| Lint YAML | yamllint | Valid workflow syntax, indentation errors |

The daily availability workflow runs independently of CI, but [a future improvement](#future-ideas) will gate it on the last CI pass and send a Telegram message with the gate status.