# Audit: availability-bot

**Repository:** `xjayk/availability-bot`  
**Commit:** `704a8fb`  
**Date:** 2026-06-03  

---

## Critical

### C1. Exception handler writes `GITHUB_OUTPUT` after a fragile operation

**File:** `set_availability.py:48-52`

The `except` block runs `page.screenshot()` before writing to `GITHUB_OUTPUT`. If the screenshot call also fails (e.g., browser process died before the page loaded), `result=failure` is never written. Downstream workflow conditionals that check `steps.run-script.outputs.result == 'failure'` see an unset variable and silently skip the notification.

**Fix:** Write to `GITHUB_OUTPUT` before the screenshot, and wrap the screenshot in a nested try/except:

```python
except Exception as e:
    print(f"Error: {e}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"result=failure\n")
    try:
        page.screenshot(path="error-screenshot.png", full_page=True)
    except Exception:
        pass
    raise
```

### C2. Monolithic architecture — zero separation of concerns

**File:** `set_availability.py:17-56`

All logic lives in a single `main()` function: browser lifecycle, authentication, status selection, error handling, output/reporting. Adding MFA, multi-day scheduling, dry-run mode, or multi-site support requires invasive edits to this flat function.

**Fix:** Refactor into at least three layers:
- **Orchestrator** (`main()`) — calls steps, writes output
- **AuthProvider** — login flow, session management
- **StatusProvider** — set status, verify, screenshot

---

## High

### H1. `GITHUB_OUTPUT` appends duplicate keys

**File:** `set_availability.py:45-46, 51-52`

Both `try` and `except` blocks append to `GITHUB_OUTPUT`. If status is set successfully but the confirmation screenshot fails, both `result=success` and `result=failure` exist in the output. GitHub reads the last value, signalling failure despite success.

**Fix:** Write once at the end of execution:

```python
with open(os.environ["GITHUB_OUTPUT"], "w") as f:
    f.write(f"result={status}\n")
```

### H2. Hard-coded `/dashboard` post-login URL

**File:** `set_availability.py:30`

```python
page.wait_for_url("**/dashboard**", timeout=15000)
```

Many apps redirect to `/home`, `/app`, `/portal`, or `/?login=success`. When the pattern doesn't match, the script times out and crashes — before setting any status.

**Fix:** Make configurable via secret, default to `**`:

```python
LOGIN_REDIRECT_PATTERN = os.environ.get("LOGIN_REDIRECT_PATTERN", "**")
...
page.wait_for_url(LOGIN_REDIRECT_PATTERN, timeout=15000)
```

### H3. No retry for transient failures

If the target site is down or slow on the first attempt, the script fails permanently. A 30-second network blip means availability isn't set for the entire day.

**Fix:** Wrap the operation in a retry loop (e.g., `tenacity`):

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
def attempt_set_status(...):
    ...
```

### H4. No validation that status was actually saved

After clicking Save (`set_availability.py:39`), the script waits 2 seconds and takes a screenshot. It never checks whether the save succeeded — the button could have been disabled, a validation error could have appeared, or the page could have navigated away unexpectedly.

**Fix:** After Save, wait for a success indicator:

```python
page.click(SAVE_BUTTON_SELECTOR)
if SUCCESS_INDICATOR_SELECTOR:
    page.wait_for_selector(SUCCESS_INDICATOR_SELECTOR, timeout=5000)
```

### H5. Env vars loaded at module import time

**File:** `set_availability.py:4-14`

All environment variables are read at import time. A missing required var (e.g., `GITHUB_OUTPUT` when running locally) crashes with an unhelpful `KeyError` before any user-facing message.

**Fix:** Validate all required vars in `main()` with explicit error messages.

### H6. No explicit timeout on `page.goto`

**File:** `set_availability.py:25, 34`

Relies on Playwright's default 30s timeout. An explicit shorter timeout would fail faster and allow for retries.

**Fix:**

```python
page.goto(url, wait_until=..., timeout=PAGE_TIMEOUT_MS)
```

---

## Medium

### M1. `networkidle` is fragile with SPAs

**File:** `set_availability.py:25, 34`

Modern apps with WebSockets or long-polling never satisfy `networkidle` (500ms of no network activity). The `goto` call times out.

**Fix:** Use `wait_until="load"` by default, allow override via env var.

### M2. Fixed `wait_for_timeout(2000)` instead of waiting for DOM signal

**File:** `set_availability.py:40`

A 2-second sleep is the classic flaky-test anti-pattern — too short on slow pages, unnecessarily long on fast ones.

**Fix:** Wait for a confirmation element to appear.

### M3. `full_page=True` on every screenshot

**File:** `set_availability.py:42, 50`

For long pages this wastes artifact storage and download time.

### M4. Generic browser context

**File:** `set_availability.py:20`

`browser.new_context()` sets no `locale`, `timezone_id`, or `user_agent`. Some sites behave differently for headless Chromium.

### M5. No `page.wait_for_selector` before clicking status button

**File:** `set_availability.py:37`

If the status button is rendered lazily, `click` might miss the intended target.

**Fix:** `page.wait_for_selector(STATUS_BUTTON_SELECTOR)` before clicking.

---

## Security Notes

| Issue | File | Risk |
|-------|------|------|
| Password in env var | `set_availability.py:6` | Inherent; mitigated by CI ephemerality |
| Credentials in context until `browser.close()` | `set_availability.py:56` | Acceptable in CI; note for local runs |
| `STATUS_CHOICE` sent to Telegram in plaintext | `availability.yml:60` | Low; Telegram server-side E2EE |
| Secrets potentially visible in debug logs | `availability.yml:30-40` | Mitigated by GitHub secret masking |

---

## Feature Suggestions

1. **Multi-day scheduling** — different status per weekday via config map
2. **TOTP/MFA support** — `pyotp` integration for 2FA codes
3. **Dry-run mode** — navigate + screenshot without clicking Save
4. **Calendar-aware skip** — read GCal/iCal to skip holidays and PTO
5. **Multi-site support** — set status on multiple portals per run
6. **Structured JSON logging** — parseable logs for debugging
7. **Status audit trail** — log changes to a Gist or issue comment
8. **Health-check pre-flight** — verify site reachable before launching Playwright
9. **Webhook fallback** — notify Slack/Discord alongside Telegram
10. **YAML config file** — consolidate selectors into `.availability.yaml`

---

## Test Plan

The project is testable after a refactor (see C2).

### Unit
- Env var parsing and validation
- `GITHUB_OUTPUT` formatting correctness
- Selector override logic

### Integration (with local test server)
Serve known HTML pages (`login.html`, `dashboard.html`, `status.html`) and verify:
- Full success path → login, redirect, set, save, screenshot
- Wrong redirect → graceful timeout + error screenshot
- Missing selectors → error screenshot captured
- Simulated network delay → retry logic fires

### CI
- `ruff check` / `mypy` on `set_availability.py`
- Workflow YAML syntax validation
- Dependency install + smoke test

---

## Summary

| Severity | Count | Key |
|----------|-------|-----|
| Critical | 2 | Exception handler fragility, monolithic architecture |
| High | 6 | Duplicate output keys, hardcoded redirect, no retry, no save validation, no env validation, no goto timeout |
| Medium | 5 | networkidle mismatch, fixed sleep, full-page screenshots, generic context, missing wait_for_selector |
