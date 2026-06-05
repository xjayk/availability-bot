import contextlib
import os
import time
import zoneinfo
from datetime import datetime, timedelta

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
    required = (
        ("BASE_URL", BASE_URL),
        ("USERNAME", USERNAME),
        ("PASSWORD", PASSWORD),
    )
    missing = [v for v, val in required if val is None]
    if missing:
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")
    if STATUS_CHOICE not in ("available", "unavailable"):
        raise SystemExit(
            f"STATUS_CHOICE must be 'available' or 'unavailable' "
            f"(case-insensitive), got '{_raw_status}'"
        )


def _today():
    """Return the current date in the America/New_York timezone."""
    return datetime.now(zoneinfo.ZoneInfo("America/New_York")).date()


def get_toggle_url():
    """Build the toggle URL. On Friday, optionally set Saturday too."""
    today = _today()
    if today.weekday() == 4:  # Friday
        work_saturday = os.environ.get("WORK_SATURDAY", "false").lower() == "true"
        if work_saturday:
            saturday = today + timedelta(days=1)
            print(f"Friday — setting available for Saturday {saturday.isoformat()}")
            return (
                f"{BASE_URL}/change-availability-for-tomorrow/"
                f"{STATUS_CHOICE}?date={saturday.isoformat()}"
            )
        else:
            monday = today + timedelta(days=3)
            print(f"Friday — skipping Saturday, targeting Monday {monday.isoformat()}")
            return (
                f"{BASE_URL}/change-availability-for-tomorrow/"
                f"{STATUS_CHOICE}?date={monday.isoformat()}"
            )
    return f"{BASE_URL}/change-availability-for-tomorrow/{STATUS_CHOICE}"


def get_success_message():
    """Return the expected success message, accounting for Friday."""
    today = _today()
    if today.weekday() == 4:  # Friday
        work_saturday = os.environ.get("WORK_SATURDAY", "false").lower() == "true"
        if work_saturday:
            return "You're made available for Saturday"
        return "You're made available for Monday"
    return (
        "You're made available for tomorrow"
        if STATUS_CHOICE == "available"
        else "You're made unavailable for tomorrow"
    )


def attempt_set_status():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US", timezone_id="America/New_York")
        page = context.new_page()

        try:
            print(f"Logging into {BASE_URL}/user/login ...")
            page.goto(
                f"{BASE_URL}/user/login",
                wait_until="domcontentloaded",
                timeout=PAGE_TIMEOUT,
            )

            page.fill("#edit-name", USERNAME, timeout=PAGE_TIMEOUT)
            page.fill("#edit-pass", PASSWORD, timeout=PAGE_TIMEOUT)
            page.click("#edit-submit", timeout=PAGE_TIMEOUT)

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
            page.wait_for_timeout(4000)

            # Handle confirmation dialog for date-targeted toggles
            page_content = page.content()
            if (
                "Make yourself available" in page_content
                or "Make yourself unavailable" in page_content
            ):
                print("Confirmation dialog detected.")
                page.screenshot(path="confirmation-dialog.png", full_page=True)
                # Try clicking the available/unavailable link
                try:
                    page.click("text=Make yourself", timeout=10000)
                    print("Clicked confirmation.")
                except Exception:
                    print(
                        "Could not click confirmation — "
                        "the GET request may have already "
                        "toggled status."
                    )

                # Wait for redirect back to profile and BigPipe to render
                page.wait_for_url(
                    f"{BASE_URL}/user/*",
                    timeout=PAGE_TIMEOUT,
                )
                page.wait_for_timeout(5000)

            page_content = page.content()

            if (
                "You're made available" in page_content
                or "You're made unavailable" in page_content
            ):
                print("SUCCESS: Status change confirmed via success message")
                result = "success"
            elif f"availunavail-header-top {STATUS_CHOICE}" in page_content:
                print(
                    f"SUCCESS: Status changed to {STATUS_CHOICE} "
                    "(verified via header class)"
                )
                result = "success"
            else:
                # Last resort: check if we're back on the profile page
                if f"/user/" in page.url:
                    print(
                        "Back on profile page — assuming success (status was likely set)"
                    )
                    result = "success"
                else:
                    print(
                        "WARNING: Could not verify status change via message or header."
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
