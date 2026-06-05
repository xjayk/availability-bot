import contextlib
import os
import time
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL")
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
_raw_status = os.environ.get("STATUS_CHOICE", "available")
STATUS_CHOICE = _raw_status.lower()

PAGE_TIMEOUT = int(os.environ.get("PAGE_TIMEOUT") or "30000")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES") or "3")
RETRY_DELAY = int(os.environ.get("RETRY_DELAY") or "10")


def validate_env():
    required = (("BASE_URL", BASE_URL), ("USERNAME", USERNAME), ("PASSWORD", PASSWORD))
    missing = [v for v, val in required if val is None]
    if missing:
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")
    if STATUS_CHOICE not in ("available", "unavailable"):
        raise SystemExit(
            f"STATUS_CHOICE must be 'available' or 'unavailable' "
            f"(case-insensitive), got '{_raw_status}'"
        )


def get_toggle_url():
    """Build the toggle URL. On Friday, skip Saturday and target Monday."""
    today = date.today()
    if today.weekday() == 4:  # Friday
        monday = today + timedelta(days=3)  # skip Sat/Sun
        print(
            f"Friday detected — targeting Monday {monday.isoformat()} "
            "instead of Saturday"
        )
        return (
            f"{BASE_URL}/change-availability-for-tomorrow/"
            f"{STATUS_CHOICE}?date={monday.isoformat()}"
        )
    return f"{BASE_URL}/change-availability-for-tomorrow/{STATUS_CHOICE}"


def get_success_message():
    """Return the expected success message, accounting for Friday (unique handling)."""
    today = date.today()
    if today.weekday() == 4:  # Friday
        return (
            "You're made available for Monday"
            if STATUS_CHOICE == "available"
            else "You're made unavailable for Monday"
        )
    return (
        "You're made available for tomorrow"
        if STATUS_CHOICE == "available"
        else "You're made unavailable for tomorrow"
    )


def attempt_set_status():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="en-US", timezone_id="America/New_York"
        )
        page = context.new_page()

        try:
            print(f"Logging into {BASE_URL}/user/login ...")
            page.goto(
                f"{BASE_URL}/user/login",
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )
            page.wait_for_timeout(5000)  # let Drupal BigPipe render the form

            page.fill("input#edit-name", USERNAME, timeout=PAGE_TIMEOUT)
            page.fill("input#edit-pass", PASSWORD, timeout=PAGE_TIMEOUT)
            page.click("input#edit-submit", timeout=PAGE_TIMEOUT)

            page.wait_for_function(
                '!window.location.href.includes("/user/login")',
                timeout=PAGE_TIMEOUT,
            )
            print("Login successful.")

            toggle_url = get_toggle_url()
            print(f"Navigating to {toggle_url} ...")
            page.goto(
                toggle_url,
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            page.wait_for_timeout(4000)  # let Drupal BigPipe render

            page_content = page.content()
            expected_message = get_success_message()

            if expected_message in page_content:
                print(f"SUCCESS: {expected_message}")
                result = "success"
            elif f"availunavail-header-top {STATUS_CHOICE}" in page_content:
                print(
                    f"SUCCESS: Status changed to {STATUS_CHOICE} "
                    "(verified via header class)"
                )
                result = "success"
            else:
                print(
                    "WARNING: Could not verify status change "
                    "via message or header."
                )
                result = "unknown"

            page.screenshot(path="final-status.png", full_page=True)
            return result

        except Exception as e:
            print(f"ERROR: {e}")
            with contextlib.suppress(Exception):
                page.screenshot(path="error-screenshot.png", full_page=True)
            raise

        finally:
            browser.close()


def main():
    validate_env()

    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = attempt_set_status()
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"result={result}\n")
            return
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                print(
                    f"Attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                    f"Retrying in {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)

    print(f"All {MAX_RETRIES} attempts failed.")
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write("result=failure\n")
    raise last_exception


if __name__ == "__main__":
    main()